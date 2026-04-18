from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_PUBLIC_URL = "https://fruition-component.pages.dev/"
DEFAULT_BUNDLE_OUTPUT = ROOT / "streamlit_cloud_bundle.zip"
PUBLISH_FILES = [
    "component_matcher.py",
    "streamlit_app.py",
    "requirements.txt",
    "runtime.txt",
    "README.md",
    "PUBLIC_ACCESS.md",
    ".gitattributes",
    ".gitignore",
    "operation_log.md",
    "logo.png",
    "streamlit_cloud_bundle.manifest.json",
    "streamlit_cloud_bundle.zip.part*",
    "build_streamlit_cloud_bundle.py",
    "sync_local_and_public.py",
    "sync_local_and_public.ps1",
    "sync_local_and_public.cmd",
    "sync_samsung_power_inductors.py",
    "publish_public.ps1",
    "publish_public.cmd",
    # Raw workbook sources required for rebuilding the cloud database.
    "Capacitor",
    "Crystal*",
    "Inductor",
    "Resistor",
    ".streamlit/config.toml",
    "docs",
    # Cloudflare Pages proxy artifacts.
    "cloudflare-pages-proxy/dist/_worker.js",
    "cloudflare-pages-proxy/dist/favicon.png",
    "cloudflare-pages-proxy/wrangler.jsonc",
]


class CommandError(RuntimeError):
    pass


def run_command(
    args: list[str],
    *,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
    env: dict | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess:
    encoding = "utf-8" if text else None
    errors = "replace" if text else None
    completed = subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        capture_output=capture_output,
        text=text,
        encoding=encoding,
        errors=errors,
        env=env,
        input=input_text,
    )
    if check and completed.returncode != 0:
        raise CommandError(
            f"command failed ({completed.returncode}): {' '.join(args)}\n"
            f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
        )
    return completed


def write_step(message: str) -> None:
    print(f"[sync] {message}")


def normalize_ssh_public_key(public_key_text: str) -> str:
    parts = public_key_text.strip().split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return public_key_text.strip()


def resolve_python_command() -> list[str]:
    venv_python = ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return [str(venv_python)]
    for cmd in (["python"], ["py", "-3"]):
        try:
            run_command(cmd + ["--version"])
            return cmd
        except Exception:
            continue
    raise RuntimeError("Python not found. Install Python or create .venv first.")


def parse_repo_full_name(remote_url: str) -> str:
    remote_url = remote_url.strip()
    for pattern in [
        r"github\.com[:/](?P<repo>[^/]+/[^/.]+?)(?:\.git)?$",
        r"ssh://git@ssh\.github\.com:443/(?P<repo>[^/]+/[^/.]+?)(?:\.git)?$",
    ]:
        match = re.search(pattern, remote_url)
        if match:
            return match.group("repo")
    raise RuntimeError(f"Unable to parse GitHub repository from remote URL: {remote_url}")


def get_default_branch() -> str:
    try:
        branch = run_command(["git", "branch", "--show-current"]).stdout.strip()
        return branch or "main"
    except Exception:
        return "main"


def get_github_token() -> str:
    result = run_command(
        ["git", "credential", "fill"],
        input_text="protocol=https\nhost=github.com\n\n",
    ).stdout
    for line in result.splitlines():
        if line.startswith("password="):
            token = line.split("=", 1)[1].strip()
            if token:
                return token
    raise RuntimeError("No GitHub credential found in Git Credential Manager.")


def github_request(token: str, method: str, url: str, payload: dict | None = None) -> dict | list | None:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "component-matcher-sync",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, method=method, headers=headers, data=data)
    last_error = None
    for attempt in range(1, 6):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                if method.upper() == "DELETE":
                    return None
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 422:
                body = exc.read().decode("utf-8", "replace")
                raise RuntimeError(f"GitHub API validation failed: {body}") from exc
            last_error = exc
        except Exception as exc:
            last_error = exc
        time.sleep(min(10, attempt * 2))
    raise RuntimeError(f"GitHub API request failed: {last_error}")


def ensure_repo_deploy_key(token: str, repo_full_name: str) -> Path:
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(parents=True, exist_ok=True)
    private_key = ssh_dir / "component_matcher_sync_ed25519"
    public_key = private_key.with_suffix(".pub")

    if not private_key.exists() or not public_key.exists():
        write_step("Generating a dedicated GitHub SSH key for sync")
        run_command(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-f",
                str(private_key),
                "-N",
                "",
                "-C",
                f"component-matcher-sync@{os.environ.get('COMPUTERNAME', 'windows')}",
            ],
            capture_output=False,
        )

    public_key_text = public_key.read_text(encoding="utf-8").strip()
    normalized_public_key = normalize_ssh_public_key(public_key_text)
    keys = github_request(
        token,
        "GET",
        f"https://api.github.com/repos/{repo_full_name}/keys",
    )
    assert isinstance(keys, list)

    matching_key = None
    for item in keys:
        if isinstance(item, dict) and normalize_ssh_public_key(item.get("key", "")) == normalized_public_key:
            matching_key = item
            break

    if matching_key and not matching_key.get("read_only", True):
        write_step("Repository deploy key already registered with write access")
        return private_key

    if matching_key and matching_key.get("read_only", True):
        key_id = matching_key.get("id")
        if key_id:
            write_step("Replacing read-only repository deploy key with a writable key")
            github_request(
                token,
                "DELETE",
                f"https://api.github.com/repos/{repo_full_name}/keys/{key_id}",
            )
            matching_key = None

    if not matching_key:
        write_step("Registering a writable repository deploy key with GitHub")
        github_request(
            token,
            "POST",
            f"https://api.github.com/repos/{repo_full_name}/keys",
            {
                "title": f"component-matcher-sync-{os.environ.get('COMPUTERNAME', 'windows')}",
                "key": public_key_text,
                "read_only": False,
            },
        )

    return private_key


def make_ssh_env(private_key: Path) -> dict:
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = (
        f'ssh -i "{private_key}" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new'
    )
    return env


def build_cloud_bundle(python_cmd: list[str], skip_bundle_rebuild: bool) -> None:
    if skip_bundle_rebuild:
        write_step("Skipping cloud bundle rebuild by request")
        return
    write_step("Building streamlit_cloud_bundle.zip from the current local database and caches")
    run_command(
        python_cmd + ["build_streamlit_cloud_bundle.py", "--output", str(DEFAULT_BUNDLE_OUTPUT)],
        capture_output=False,
    )
    split_cloud_bundle_archive(DEFAULT_BUNDLE_OUTPUT)


def split_cloud_bundle_archive(bundle_path: Path, part_size_mb: int = 95) -> None:
    if not bundle_path.exists():
        raise FileNotFoundError(f"Cloud bundle not found: {bundle_path}")
    part_size = int(part_size_mb) * 1024 * 1024
    if part_size <= 0:
        raise ValueError("part_size_mb must be positive")

    for part_file in ROOT.glob("streamlit_cloud_bundle.zip.part*"):
        try:
            if part_file.is_file():
                part_file.unlink()
        except Exception:
            continue

    total_size = bundle_path.stat().st_size
    part_count = (total_size + part_size - 1) // part_size
    write_step(f"Splitting cloud bundle into {part_count} parts (~{part_size_mb}MB each)")
    with bundle_path.open("rb") as source_handle:
        for index in range(1, part_count + 1):
            chunk = source_handle.read(part_size)
            part_path = ROOT / f"streamlit_cloud_bundle.zip.part{index:02d}"
            with part_path.open("wb") as target_handle:
                target_handle.write(chunk)
            write_step(f"Created {part_path.name} ({part_path.stat().st_size} bytes)")


def should_skip_publish_file(path: Path) -> bool:
    file_name = path.name
    lower_name = file_name.lower()
    if file_name.startswith("~$"):
        return True
    if ".backup_" in lower_name:
        return True
    if "backup" in lower_name:
        return True
    if "可查看版" in file_name or "view_only" in lower_name or "view-only" in lower_name:
        return True
    return False


def stage_publish_files() -> list[str]:
    existing_files = []
    for rel in PUBLISH_FILES:
        if any(ch in rel for ch in "*?[]"):
            for path in ROOT.glob(rel):
                if path.is_dir():
                    existing_files.extend(
                        str(child)
                        for child in path.rglob("*")
                        if child.is_file() and not should_skip_publish_file(child)
                    )
                elif path.is_file() and not should_skip_publish_file(path):
                    existing_files.append(str(path))
            continue
        path = ROOT / rel
        if path.is_dir():
            existing_files.extend(
                str(child)
                for child in path.rglob("*")
                if child.is_file() and not should_skip_publish_file(child)
            )
        elif path.is_file() and not should_skip_publish_file(path):
            existing_files.append(str(path))
    if not existing_files:
        raise RuntimeError("No publishable files were found.")
    run_command(["git", "add", "--"] + existing_files, capture_output=False)
    staged = run_command(["git", "diff", "--cached", "--name-only"]).stdout.splitlines()
    return [item.strip() for item in staged if item.strip()]


def commit_if_needed(message: str) -> str:
    staged = stage_publish_files()
    if not staged:
        write_step("No staged publish changes were found")
        return ""
    write_step(f"Creating commit: {message}")
    run_command(["git", "commit", "-m", message], capture_output=False)
    return run_command(["git", "rev-parse", "HEAD"]).stdout.strip()


def fetch_remote_head(repo_full_name: str, branch: str, ssh_env: dict) -> str:
    remote_url = f"ssh://git@ssh.github.com:443/{repo_full_name}.git"
    write_step("Fetching the latest remote branch through SSH 443")
    run_command(["git", "fetch", remote_url, branch], env=ssh_env, capture_output=False)
    return run_command(["git", "rev-parse", "FETCH_HEAD"]).stdout.strip()


def create_publish_commit(commit_sha: str, remote_sha: str) -> str:
    if not commit_sha:
        return remote_sha

    ancestor_check = run_command(
        ["git", "merge-base", "--is-ancestor", remote_sha, commit_sha],
        check=False,
    )
    if ancestor_check.returncode == 0:
        write_step("Local publish commit already builds on the remote branch")
        return commit_sha

    tree_sha = run_command(["git", "show", "-s", "--format=%T", commit_sha]).stdout.strip()
    message = run_command(["git", "show", "-s", "--format=%B", commit_sha]).stdout
    author_name = run_command(["git", "show", "-s", "--format=%an", commit_sha]).stdout.strip()
    author_email = run_command(["git", "show", "-s", "--format=%ae", commit_sha]).stdout.strip()
    author_date = run_command(["git", "show", "-s", "--format=%aI", commit_sha]).stdout.strip()
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = author_name
    env["GIT_AUTHOR_EMAIL"] = author_email
    env["GIT_AUTHOR_DATE"] = author_date
    write_step("Synthesizing a publish commit on top of the latest remote branch")
    return run_command(
        ["git", "commit-tree", tree_sha, "-p", remote_sha],
        env=env,
        input_text=message,
    ).stdout.strip()


def push_branch(repo_full_name: str, branch: str, ssh_env: dict, publish_sha: str) -> None:
    remote_url = f"ssh://git@ssh.github.com:443/{repo_full_name}.git"
    write_step("Pushing the branch through SSH 443")
    run_command(["git", "push", remote_url, f"{publish_sha}:{branch}"], env=ssh_env, capture_output=False)
    run_command(["git", "update-ref", f"refs/remotes/origin/{branch}", publish_sha])


def validate_python_files(python_cmd: list[str]) -> None:
    files = [
        str(ROOT / rel)
        for rel in [
            "component_matcher.py",
            "streamlit_app.py",
            "build_streamlit_cloud_bundle.py",
            "sync_local_and_public.py",
        ]
        if (ROOT / rel).exists()
    ]
    if files:
        write_step("Running syntax validation for the sync and app entry files")
        run_command(python_cmd + ["-m", "py_compile"] + files, capture_output=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="One-click sync for local and public Component Matcher deployments.")
    parser.add_argument("--commit-message", default="", help="Optional custom git commit message.")
    parser.add_argument("--skip-bundle-rebuild", action="store_true", help="Skip rebuilding streamlit_cloud_bundle.zip.")
    parser.add_argument("--skip-push", action="store_true", help="Prepare commit locally but do not push.")
    parser.add_argument("--public-url", default=DEFAULT_PUBLIC_URL, help="Public site URL to display after publish.")
    args = parser.parse_args()

    os.chdir(ROOT)
    python_cmd = resolve_python_command()
    branch = get_default_branch()
    repo_remote = run_command(["git", "remote", "get-url", "origin"]).stdout.strip()
    repo_full_name = parse_repo_full_name(repo_remote)
    commit_message = args.commit_message.strip() or f"Sync local and public release {time.strftime('%Y-%m-%d %H:%M')}"

    build_cloud_bundle(python_cmd, args.skip_bundle_rebuild)
    validate_python_files(python_cmd)

    token = get_github_token()
    private_key = ensure_repo_deploy_key(token, repo_full_name)
    ssh_env = make_ssh_env(private_key)

    commit_sha = commit_if_needed(commit_message)
    remote_sha = fetch_remote_head(repo_full_name, branch, ssh_env)
    publish_sha = create_publish_commit(commit_sha, remote_sha)

    if args.skip_push:
        write_step("Skipping push by request")
    else:
        push_branch(repo_full_name, branch, ssh_env, publish_sha)
        write_step(f"Public site: {args.public_url}")

    if commit_sha:
        print(f"[sync] local commit: {commit_sha}")
    if commit_sha and publish_sha and publish_sha != commit_sha:
        print(f"[sync] published commit: {publish_sha}")
    print("[sync] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
