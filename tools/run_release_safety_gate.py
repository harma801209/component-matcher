from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTECTED_RUNTIME_DATABASES = (
    ROOT / "cache" / "member_auth.sqlite",
    ROOT / "cache" / "cost_price_lists.sqlite",
    ROOT / "cache" / "no_match_reports.sqlite",
)
PROTECTED_RUNTIME_DATABASES = tuple(
    dict.fromkeys(
        [
            *DEFAULT_PROTECTED_RUNTIME_DATABASES,
            *(
                Path(value).expanduser().resolve()
                for value in (
                    os.getenv("MEMBER_AUTH_DB_PATH", ""),
                    os.getenv("COST_PRICE_DB_PATH", ""),
                    os.getenv("NO_MATCH_REPORT_DB_PATH", ""),
                )
                if value.strip()
            ),
        ]
    )
)
SQLITE_SIDE_SUFFIXES = ("", "-wal", "-shm", "-journal")


def file_fingerprint(path: Path) -> dict[str, str | int | bool]:
    if not path.exists():
        return {"exists": False}
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "exists": True,
        "size": path.stat().st_size,
        "sha256": digest.hexdigest(),
    }


def protected_runtime_snapshot() -> dict[str, dict[str, str | int | bool]]:
    snapshot = {}
    for database in PROTECTED_RUNTIME_DATABASES:
        for suffix in SQLITE_SIDE_SUFFIXES:
            path = Path(f"{database}{suffix}")
            try:
                label = str(path.relative_to(ROOT))
            except ValueError:
                label = str(path)
            snapshot[label] = file_fingerprint(path)
    return snapshot


def run_checked(command: list[str], env: dict[str, str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    before = protected_runtime_snapshot()
    with tempfile.TemporaryDirectory(prefix="component-matcher-release-gate-") as temp_dir:
        temp_root = Path(temp_dir)
        env = os.environ.copy()
        env.update(
            {
                "MEMBER_AUTH_DB_PATH": str(temp_root / "member.sqlite"),
                "COST_PRICE_DB_PATH": str(temp_root / "cost.sqlite"),
                "NO_MATCH_REPORT_DB_PATH": str(temp_root / "reports.sqlite"),
                "COMPONENT_MATCHER_BUILD_MODE": "1",
                "COMPONENT_MATCHER_STARTUP_MAINTENANCE": "0",
                "MEMBER_AUTH_REMOTE_FORCE": "0",
                "RUNTIME_STORE_REMOTE_FORCE": "0",
            }
        )
        run_checked(
            [
                sys.executable,
                "-m",
                "py_compile",
                "component_matcher.py",
                "streamlit_app.py",
                "sync_local_and_public.py",
            ],
            env,
        )
        run_checked(
            [sys.executable, "-m", "unittest", "tests.test_system_regression"],
            env,
        )
    after = protected_runtime_snapshot()
    if before != after:
        changed = sorted(path for path in before if before[path] != after[path])
        print("Release blocked: protected runtime data changed during validation.", file=sys.stderr)
        for path in changed:
            print(f"  - {path}", file=sys.stderr)
        return 1
    print("Release safety gate passed: tests used isolated databases and protected runtime data is unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
