"""Conservative, source-backed completion for existing MLCC catalogue records.

Never generates identities, prices, certificates, lifecycle states or dimensions.
Only missing fields are filled. Existing nonempty indexed values win.
See docs/catalog_parameter_completion.md for the primary-source references.
"""
import re

FIELDS = ('_size', '_mat', '_tol', '_mount_style')
RAW_COLUMNS = ('品牌', '型号', '_component_type', *FIELDS, '尺寸（inch）',
               '材质（介质）', '容值误差', '安装方式', '封装代码')
SIZES = frozenset('008004 01005 0102 015008 0201 0204 0302 0306 0402 05035 0508 0603 0612 0805 1206 1210 1808 1812 1825 2220 2225'.split())
EMPTY = frozenset(('', '-', '--', '/', 'N/A', 'NA', 'NULL', 'NONE', 'NAN'))


def text(value):
    value = '' if value is None else str(value).strip()
    return '' if value.upper() in EMPTY else value


def size_code(value, brand='', model=''):
    value = text(value).upper().replace(' ', '')
    if value in SIZES:
        return value
    # Sunway calls its 0.40x0.20mm body "0100"; keep this brand-scoped.
    if value == '0100' and ('SUNWAY' in brand.upper() or '信维' in brand) and re.match(r'^M[CAH]0100', model):
        return '01005'
    return ''


def tolerance(value):
    value = text(value).upper().replace(' ', '').replace('％', '%').replace('+/-', '±')
    if re.fullmatch(r'±?\d+(?:\.\d+)?PF', value):
        return value.lstrip('±')
    if re.fullmatch(r'±?\d+(?:\.\d+)?%?', value):
        number = value.lstrip('±').rstrip('%')
        return number if 0 < float(number) <= 100 else ''
    if re.fullmatch(r'\+?\d+(?:\.\d+)?%?/-\d+(?:\.\d+)?%?', value):
        return value.replace('%', '')
    return ''


def surface_family(brand, model):
    """Recognized chip families only: notably excludes Murata DE* leaded parts."""
    brand = brand.upper()
    families = (
        (('MURATA', '村田'), r'^(?:GR[MJTLQ]|GC[MJAGQR]|G[JQ]M|LL[ADLMR]|KCA|WBM|ZRB)'),
        (('SAMSUNG', '三星'), r'^CL'),
        (('TAIYO', '太诱', '太阳诱电'), r'^(?:[PAJLETGUHQSX]MK|LDK|M[A-Z]{4})'),
        (('TDK', '东电化'), r'^C(?:\d{4}|[GNBTA][A-Z])'),
        (('CCTC', '三环'), r'^TCC'),
        (('SUNWAY', '信维'), r'^M[CAH]'),
        (('YAGEO', '国巨'), r'^(?:CC|CS|CQ|AC|AS|CA|CL|SC|CN|IC)\d{4}'),
        (('WALSIN', '华新科'), r'^(?:\d{4}|[A-Z]{2}\d{2})'),
        (('SAMWHA', '三和'), r'^C[QS]\d{4}'),
        (('FOJAN', '富捷'), r'^FCC'),
        (('HRE', '芯声'), r'^(?:CGA|CSA|C\d{4})'),
        (('FENGHUA', '风华', 'FH('), r'^(?:\d{4}|(?:AM|MBK)\d{4})'),
        (('VIIYONG', '微容'), r'^[A-Z]*\d{4}'),
        (('EYANG', '宇阳'), r'^[A-Z]*\d{4}'),
        (('DARFON', '达方'), r'^C'),
        (('KEMET', '基美'), r'^C\d{4}'),
        (('KYOCERA', 'AVX', '晶瓷'), r'^(?:\d{4}|K[AG]M\d{2})'),
    )
    return any(any(token in brand for token in names) and re.match(pattern, model)
               for names, pattern in families)


def complete(record, model_resolver=None):
    """Return only four specification fields, preserving existing nonempty data."""
    result = {key: text(record.get(key)) for key in FIELDS}
    if record.get('_component_type') != 'MLCC' or not text(record.get('型号')):
        return result
    brand, model = text(record.get('品牌')), text(record.get('型号')).upper()
    if not result['_size']:
        result['_size'] = size_code(record.get('尺寸（inch）'), brand, model) or size_code(record.get('封装代码'), brand, model)
    if not result['_size'] and ('SUNWAY' in brand.upper() or '信维' in brand) and re.match(r'^M[CAH]0100', model):
        result['_size'] = '01005'
    if not result['_mat']:
        result['_mat'] = text(record.get('材质（介质）'))
        if not result['_mat'] and ('CCTC' in brand.upper() or '三环' in brand) and re.fullmatch(r'TCC(?:0603|0805|1206)M3L\d{3}[JKM]\d{3}[A-Z]+', model):
            result['_mat'] = 'M3L'
    if not result['_tol']:
        result['_tol'] = tolerance(record.get('容值误差'))
    if model_resolver and any(not result[key] for key in FIELDS[:3]):
        decoded = model_resolver(model, brand) or {}
        for key, raw in (('_size', '尺寸（inch）'), ('_mat', '材质（介质）'), ('_tol', '容值误差')):
            value = decoded.get(raw)
            if key == '_size':
                value = size_code(value, brand, model)
            elif key == '_tol':
                value = tolerance(value)
            if not result[key] and text(value):
                result[key] = text(value)
    if not result['_mount_style']:
        mount = text(record.get('安装方式'))
        # Explicit source mounting wins, including any non-SMD value.
        if mount:
            result['_mount_style'] = '贴片' if mount.upper() in {'SMD', 'SMT', 'CHIP', '贴片'} else mount
        elif result['_size'] in SIZES and surface_family(brand, model):
            result['_mount_style'] = '贴片'
    return result
