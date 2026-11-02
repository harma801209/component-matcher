"""Version-bound, public-only filter assets prepared before deployment.

No network, credentials, runtime stores or original-library writes. Stale or
missing assets return None so the existing exact query path remains available.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import threading
from contextlib import closing
from functools import lru_cache

SCHEMA = 1
ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'catalog_ready'
LOCK = threading.RLock()


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def stat_key(path):
    value = Path(path).stat()
    return str(Path(path).resolve()), value.st_size, value.st_mtime_ns, value.st_ctime_ns


@lru_cache(maxsize=96)
def cached_digest(key):
    return digest(key[0])


def recipe(root=ROOT):
    """Conservatively invalidate on any root rule/code or evidence change.

    Release stamps alone have no data meaning. Everything else in the matcher
    is covered rather than guessing which helpers a naming rule might call.
    """
    root = Path(root)
    paths = sorted(root.glob('*.py'))
    paths += sorted((root / 'catalog_sources').glob('*.json'))
    paths += sorted((root / 'data').glob('*.json'))
    paths += [root / 'manufacturer_lifecycle_evidence.json']
    result = hashlib.sha256()
    for path in paths:
        if path.name == 'streamlit_app.py':
            continue
        # The build host is Windows and the public worker is Linux. Git's
        # checkout newline conversion must not look like a changed rule.
        data = path.read_text(encoding='utf-8').encode('utf-8')
        if path.name == 'component_matcher.py':
            data = re.sub(rb'PUBLIC_CODE_STAMP = "[^"]*"', b'PUBLIC_CODE_STAMP = ""', data)
        result.update(path.relative_to(root).as_posix().encode())
        result.update(b'\0' + data + b'\0')
    return result.hexdigest()


def source_members(root=ROOT):
    document = json.loads((Path(root) / 'streamlit_cloud_bundle.manifest.json').read_text(encoding='utf-8'))
    wanted = ('cache/components_search.sqlite', 'cache/components_prepared_v5.parquet')
    entries = {r['path']: {'sha256': r['sha256'], 'size': r['size']}
               for r in document['members'] if r['path'] in wanted}
    if set(entries) != set(wanted):
        raise ValueError('Incomplete public catalogue revision')
    return entries


def manifest(root=ROOT, assets=ASSETS, index=None, details=None):
    """Missing public files can use their shipped SHA; existing ones must match.

    In particular a locally replaced index, or a live WAL, cannot silently use
    yesterday's prepared data, even when the file sizes happen to be equal.
    """
    root, assets = Path(root), Path(assets)
    try:
        document = json.loads((assets / 'manifest.json').read_text(encoding='utf-8'))
        if document['schema'] != SCHEMA or document['recipe'] != recipe(root):
            return None
        expected = source_members(root)
        if document['sources'] != expected:
            return None
        for member, path in (('cache/components_search.sqlite', index),
                             ('cache/components_prepared_v5.parquet', details)):
            path = Path(path) if path else root / member
            if Path(str(path) + '-wal').is_file() and Path(str(path) + '-wal').stat().st_size:
                return None
            if path.is_file():
                if path.stat().st_size != expected[member]['size'] or cached_digest(stat_key(path)) != expected[member]['sha256']:
                    return None
        return document
    except (OSError, ValueError, KeyError, TypeError):
        return None


def export(conn, kind, target):
    """Export the *existing completed* projection, never generate model codes."""
    import component_filters as filters
    filters.prepare_browse_source(conn, kind)
    unique = filters.has_unique_model_rows(conn, kind)
    aggregates = filters.QueryCache(conn)
    initial = filters.snapshot(conn, kind, verified_unique=unique, query_cache=aggregates)
    fields = filters.available_profile(conn, kind)[1]
    allowed = {'品牌', '型号', '_component_type', '_lifecycle_source', '_lifecycle_checked'} | {f.key for f in fields}
    columns = [r[1] for r in conn.execute('PRAGMA table_info(catalog_browse_source)')]
    if set(columns) - allowed:
        raise ValueError('Non-public filter column in export')
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='catalog-filter-build-') as folder:
        database = Path(folder) / 'public.sqlite'
        with closing(sqlite3.connect(database)) as out:
            names = ','.join('"'+c.replace('"','""')+'"' for c in columns)
            out.execute('CREATE TABLE catalog_browse_source ('+names+')')
            cursor = conn.execute('SELECT '+names+' FROM catalog_browse_source ORDER BY rowid')
            while rows := cursor.fetchmany(2048):
                out.executemany('INSERT INTO catalog_browse_source VALUES ('+','.join('?' for _ in columns)+')', rows)
            out.execute('CREATE INDEX catalog_browse_order ON catalog_browse_source(品牌,型号)')
            out.execute('CREATE INDEX catalog_browse_identity ON catalog_browse_source(COALESCE(品牌,\'\')||char(0)||型号)')
            metadata = conn.execute('SELECT kind,fields FROM catalog_browse_metadata').fetchone()
            out.execute('CREATE TABLE catalog_browse_metadata (kind TEXT,fields TEXT)')
            out.execute('INSERT INTO catalog_browse_metadata VALUES (?,?)', metadata)
            out.execute('CREATE TABLE catalog_browse_aggregates (sql TEXT,params TEXT,result TEXT)')
            for (sql, params), (rows, _) in aggregates.entries.items():
                out.execute('INSERT INTO catalog_browse_aggregates VALUES (?,?,?)',
                            (sql, json.dumps(params, ensure_ascii=False), json.dumps(rows, ensure_ascii=False)))
            out.commit()
            if out.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise ValueError('Invalid filter export')
        raw_sha, raw_size = digest(database), database.stat().st_size
        with database.open('rb') as source, target.open('wb') as sink:
            with gzip.GzipFile(fileobj=sink, mode='wb', mtime=0, filename='', compresslevel=6) as compressed:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    compressed.write(chunk)
    return dict(file=target.name, sha256=digest(target), raw_sha256=raw_sha,
                raw_size=raw_size, total=initial['total'], unique=unique)


def open_source(document, kind, assets=ASSETS, cache=None):
    """Open a completed, verified read-only SQLite asset and its exact aggregates."""
    import component_filters as filters
    from catalog_passive_completion import SharedSource
    try:
        entry = document['kinds'][kind]
        name = entry['file']
        if Path(name).name != name or not re.fullmatch(r'[0-9a-f]{16}\.sqlite\.gz', name):
            return None
        archive = Path(assets) / name
        if cached_digest(stat_key(archive)) != entry['sha256']:
            return None
        folder = Path(cache) if cache else Path(tempfile.gettempdir()) / 'component-public-filter-v1'
        target = folder / (entry['raw_sha256'] + '.sqlite')
        with LOCK:
            folder.mkdir(parents=True, exist_ok=True)
            valid = (target.is_file() and target.stat().st_size == entry['raw_size']
                     and cached_digest(stat_key(target)) == entry['raw_sha256'])
            if not valid:
                with tempfile.NamedTemporaryFile(dir=folder, prefix='public-', suffix='.part', delete=False) as output:
                    partial = Path(output.name)
                    try:
                        actual, size = hashlib.sha256(), 0
                        with gzip.open(archive, 'rb') as source:
                            while chunk := source.read(1024 * 1024):
                                size += len(chunk)
                                if size > entry['raw_size']:
                                    raise ValueError('Oversized public filter asset')
                                actual.update(chunk)
                                output.write(chunk)
                        if size != entry['raw_size'] or actual.hexdigest() != entry['raw_sha256']:
                            raise ValueError('Public filter asset checksum mismatch')
                    except Exception:
                        output.close()
                        partial.unlink(missing_ok=True)
                        raise
                os.replace(partial, target)
        conn = sqlite3.connect(target.resolve().as_uri()+'?mode=ro&immutable=1', uri=True, check_same_thread=False)
        try:
            if conn.execute('SELECT kind FROM catalog_browse_metadata').fetchone() != (kind,):
                raise ValueError('Wrong filter kind')
            source = SharedSource(conn)
            source.verified_unique = bool(entry['unique'])
            source.query_cache = filters.QueryCache(conn)
            for sql, params, rows in conn.execute('SELECT sql,params,result FROM catalog_browse_aggregates'):
                # Only data from the checksum-verified build; never execute SQL
                # read from a browser or accept member-specific cached results.
                values = tuple(tuple(row) for row in json.loads(rows))
                cells = 1 + sum(map(len, values))
                source.query_cache.entries[(sql, tuple(json.loads(params)))] = (values, cells)
                source.query_cache.cells += cells
            return source
        except Exception:
            conn.close()
            raise
    except (OSError, ValueError, KeyError, TypeError, sqlite3.DatabaseError):
        return None
