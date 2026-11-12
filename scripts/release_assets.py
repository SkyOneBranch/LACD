#!/usr/bin/env python3
"""Repeatable Release Asset Builder and Verifier for LACD (WP-B).

Builds and verifies:
1. Wheel: lacd-<version>-py3-none-any.whl
2. Template Bundle ZIP: lacd-templates-<version>.zip
3. Release Manifest: release-manifest-<version>.json
4. Release Notes Snippet: release-notes-snippet-<version>.md

Also supports:
- Smoke testing in a clean isolated virtual environment (--smoke-venv)
- Verifying public releases on GitHub Releases API (--verify-public-release --tag vX.Y.Z)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


DEFAULT_UPSTREAM_REPO = "SkyOneBranch/LACD"


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    return _sha256_hex(path.read_bytes())


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_version(repo_root: Path | None = None) -> str:
    root = repo_root or get_repo_root()
    init_py = root / "src" / "lacd" / "__init__.py"
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_py.read_text("utf-8"))
    if not match:
        raise ValueError(f"Cannot extract __version__ from {init_py}")
    return match.group(1)


def get_git_head_sha(repo_root: Path | None = None) -> str:
    root = repo_root or get_repo_root()
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        return r.stdout.strip()
    except Exception:
        return "unknown"


def build_template_zip(out_dir: Path, repo_root: Path | None = None) -> tuple[Path, str]:
    root = repo_root or get_repo_root()
    ver = get_version(root)
    tpl_dir = root / "src" / "lacd" / "templates"
    zip_path = out_dir / f"lacd-templates-{ver}.zip"

    entries: list[tuple[str, Path]] = []
    for file_path in sorted(tpl_dir.rglob("*")):
        if file_path.is_file():
            rel = file_path.relative_to(tpl_dir).as_posix()
            if "__pycache__" in rel or rel.endswith(".pyc") or rel.startswith("."):
                continue
            entries.append((rel, file_path))

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel, path in entries:
            zf.write(path, arcname=rel)

    sha = _file_sha256(zip_path)
    return zip_path, sha


def build_wheel(out_dir: Path, repo_root: Path | None = None) -> tuple[Path, str]:
    root = repo_root or get_repo_root()
    ver = get_version(root)

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "wheel",
        "--no-deps",
        "-w",
        str(out_dir),
        str(root),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"pip wheel failed (exit {r.returncode}):\n{r.stderr}\n{r.stdout}")

    wheel_name = f"lacd-{ver}-py3-none-any.whl"
    wheel_path = out_dir / wheel_name
    if not wheel_path.exists():
        # Fallback to globbing if platform tag differs
        matches = list(out_dir.glob(f"lacd-{ver}*.whl"))
        if not matches:
            raise FileNotFoundError(f"Built wheel not found in {out_dir}")
        wheel_path = matches[0]

    sha = _file_sha256(wheel_path)
    return wheel_path, sha


def build_assets(
    out_dir: Path,
    repo_root: Path | None = None,
    repo: str = DEFAULT_UPSTREAM_REPO,
) -> dict:
    root = repo_root or get_repo_root()
    out_dir.mkdir(parents=True, exist_ok=True)
    ver = get_version(root)
    git_sha = get_git_head_sha(root)

    wheel_path, wheel_sha = build_wheel(out_dir, root)
    zip_path, zip_sha = build_template_zip(out_dir, root)

    manifest_path = root / "src" / "lacd" / "templates" / "manifest.json"
    tpl_manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest_tpl_ver = tpl_manifest.get("template_version", ver)

    release_manifest = {
        "version": ver,
        "manifest_template_version": manifest_tpl_ver,
        "git_head_sha": git_sha,
        "wheel": {
            "filename": wheel_path.name,
            "sha256": wheel_sha,
        },
        "template_zip": {
            "filename": zip_path.name,
            "sha256": zip_sha,
        },
    }
    manifest_file = out_dir / f"release-manifest-{ver}.json"
    manifest_file.write_text(json.dumps(release_manifest, indent=2) + "\n", encoding="utf-8")

    bundle_url = f"https://github.com/{repo}/releases/download/v{ver}/{zip_path.name}"
    snippet_text = (
        f"## Template bundle\n\n"
        f"`{zip_path.name}` — SHA-256 verified by `lacd upgrade` before use:\n\n"
        f"```json\n"
        f'{{"template_bundle": {{"url": "{bundle_url}", "sha256": "{zip_sha}"}}}}\n'
        f"```\n\n"
        f"Template-Bundle-SHA256: {zip_sha}\n"
    )
    snippet_file = out_dir / f"release-notes-snippet-{ver}.md"
    snippet_file.write_text(snippet_text, encoding="utf-8")

    return {
        "version": ver,
        "wheel_path": wheel_path,
        "wheel_sha": wheel_sha,
        "zip_path": zip_path,
        "zip_sha": zip_sha,
        "manifest_file": manifest_file,
        "snippet_file": snippet_file,
    }


def verify_assets(
    out_dir: Path,
    repo_root: Path | None = None,
    smoke_venv: bool = False,
    repo: str = DEFAULT_UPSTREAM_REPO,
) -> None:
    root = repo_root or get_repo_root()
    ver = get_version(root)

    # 1. Wheel inspection
    wheel_path = out_dir / f"lacd-{ver}-py3-none-any.whl"
    if not wheel_path.exists():
        matches = list(out_dir.glob(f"lacd-{ver}*.whl"))
        if not matches:
            raise FileNotFoundError(f"Missing wheel in {out_dir}")
        wheel_path = matches[0]

    with zipfile.ZipFile(wheel_path, "r") as wz:
        names = set(wz.namelist())
        for n in names:
            if "__pycache__" in n or n.endswith(".pyc"):
                raise ValueError(f"Wheel contains forbidden bytecode cache: {n}")

        required_wheel_files = [
            ("lacd/templates/manifest.json", root / "src" / "lacd" / "templates" / "manifest.json"),
            ("lacd/templates/workflows/lacd-verify.yml", root / "src" / "lacd" / "templates" / "workflows" / "lacd-verify.yml"),
            ("lacd/schemas/lacd-config.schema.json", root / "src" / "lacd" / "schemas" / "lacd-config.schema.json"),
            ("lacd/schemas/lock.schema.json", root / "src" / "lacd" / "schemas" / "lock.schema.json"),
            ("lacd/schemas/status.schema.json", root / "src" / "lacd" / "schemas" / "status.schema.json"),
        ]
        for rel_in_wheel, src_file in required_wheel_files:
            if rel_in_wheel not in names:
                raise ValueError(f"Wheel missing required file: {rel_in_wheel}")
            wheel_bytes = wz.read(rel_in_wheel)
            expected_bytes = src_file.read_bytes()
            if _sha256_hex(wheel_bytes) != _sha256_hex(expected_bytes):
                raise ValueError(f"Wheel file content SHA-256 mismatch for: {rel_in_wheel}")

    # 2. Template ZIP verification
    zip_path = out_dir / f"lacd-templates-{ver}.zip"
    if not zip_path.exists():
        raise FileNotFoundError(f"Missing template bundle zip: {zip_path}")
    zip_bytes = zip_path.read_bytes()
    zip_sha = _sha256_hex(zip_bytes)

    # Ensure src is importable
    src_path = str(root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from lacd.upgrade.migrate import load_bundle_from_zip
    from lacd.upgrade.source import parse_template_bundle

    bundle = load_bundle_from_zip(zip_bytes, zip_sha)
    if bundle.version != ver:
        raise ValueError(f"Bundle template_version ({bundle.version}) != CLI version ({ver})")
    if bundle.manifest.get("template_version") != ver:
        raise ValueError(f"Bundle manifest template_version ({bundle.manifest.get('template_version')}) != {ver}")

    # 3. Release notes snippet verification
    snippet_file = out_dir / f"release-notes-snippet-{ver}.md"
    if not snippet_file.exists():
        raise FileNotFoundError(f"Missing release notes snippet: {snippet_file}")
    snippet_text = snippet_file.read_text(encoding="utf-8")
    parsed = parse_template_bundle({"body": snippet_text})
    if not parsed:
        raise ValueError("Failed to parse release notes snippet using parse_template_bundle")
    expected_url = f"https://github.com/{repo}/releases/download/v{ver}/{zip_path.name}"
    if parsed["url"] != expected_url:
        raise ValueError(f"Snippet URL mismatch: expected {expected_url}, got {parsed['url']}")
    if parsed["sha256"] != zip_sha:
        raise ValueError(f"Snippet SHA-256 mismatch: expected {zip_sha}, got {parsed['sha256']}")

    # 4. Release manifest verification
    manifest_file = out_dir / f"release-manifest-{ver}.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Missing release manifest: {manifest_file}")
    m_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    if m_data.get("version") != ver:
        raise ValueError(f"Manifest version mismatch: {m_data.get('version')} != {ver}")
    if m_data.get("manifest_template_version") != ver:
        raise ValueError(f"Manifest template_version mismatch: {m_data.get('manifest_template_version')} != {ver}")
    if m_data.get("wheel", {}).get("sha256") != _file_sha256(wheel_path):
        raise ValueError("Manifest wheel SHA-256 mismatch")
    if m_data.get("template_zip", {}).get("sha256") != zip_sha:
        raise ValueError("Manifest template_zip SHA-256 mismatch")

    print(f"Asset verification passed for LACD v{ver} ({wheel_path.name}, {zip_path.name})")

    # 5. Smoke venv test
    if smoke_venv:
        run_smoke_venv(wheel_path, ver)


def run_smoke_venv(wheel_path: Path, ver: str) -> None:
    with tempfile.TemporaryDirectory(prefix="lacd-smoke-venv-") as venv_dir:
        venv_path = Path(venv_dir)
        # Create virtual environment
        r = subprocess.run([sys.executable, "-m", "venv", str(venv_path)], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"venv creation failed:\n{r.stderr}")

        pip_bin = venv_path / "bin" / "pip"
        lacd_bin = venv_path / "bin" / "lacd"

        # Install wheel
        r = subprocess.run([str(pip_bin), "install", str(wheel_path)], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"pip install of wheel failed:\n{r.stderr}\n{r.stdout}")

        # Check version
        r = subprocess.run([str(lacd_bin), "--version"], capture_output=True, text=True)
        if r.returncode != 0 or ver not in r.stdout:
            raise RuntimeError(f"lacd --version failed or mismatched (exit {r.returncode}): {r.stdout} {r.stderr}")

        # Create temporary git repo to test init / status / verify
        with tempfile.TemporaryDirectory(prefix="lacd-smoke-repo-") as repo_dir:
            repo = Path(repo_dir)
            subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "smoke@test.org"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Smoke Test"], cwd=repo, check=True)

            # 1) init --dry-run: must write 0 files
            r = subprocess.run([str(lacd_bin), "init", "--dry-run", "--path", str(repo)], capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"lacd init --dry-run failed:\n{r.stderr}")
            untracked = [p for p in repo.rglob("*") if ".git" not in str(p)]
            if untracked:
                raise RuntimeError(f"lacd init --dry-run left untracked files: {untracked}")

            # 2) init: creates files
            r = subprocess.run([str(lacd_bin), "init", "--path", str(repo)], capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"lacd init failed:\n{r.stderr}")
            for needed in ["lacd.yaml", ".lacd/lock.json", ".github/workflows/lacd-verify.yml"]:
                if not (repo / needed).is_file():
                    raise RuntimeError(f"Expected file missing after init: {needed}")

            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)

            # 3) status --json: state == VALIDATED, remote_enforcement == unverified
            r = subprocess.run([str(lacd_bin), "status", "--json", "--path", str(repo)], capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"lacd status --json failed:\n{r.stderr}")
            status_data = json.loads(r.stdout)
            if status_data.get("state") != "VALIDATED":
                raise RuntimeError(f"Expected status VALIDATED, got {status_data.get('state')}")
            re_status = status_data.get("dimensions", {}).get("remote_enforcement", {}).get("status")
            if re_status != "unverified":
                raise RuntimeError(f"Expected remote_enforcement.status 'unverified', got {re_status!r}")

            # 4) verify --local --strict: exit 0
            r = subprocess.run([str(lacd_bin), "verify", "--local", "--strict", "--path", str(repo)], capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"lacd verify --local --strict failed:\n{r.stderr}\n{r.stdout}")

    print(f"Smoke venv tests passed successfully for LACD v{ver}")


def verify_public_release(tag: str, repo: str = DEFAULT_UPSTREAM_REPO) -> None:
    tag_clean = tag if tag.startswith("v") else f"v{tag}"
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag_clean}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "lacd-release-verifier",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            rel = json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch public release {tag_clean} from {repo}: {exc}") from exc

    # Ensure src is importable
    root = get_repo_root()
    src_path = str(root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    from lacd.upgrade.migrate import load_bundle_from_zip
    from lacd.upgrade.source import parse_template_bundle

    parsed = parse_template_bundle(rel)
    if not parsed:
        raise ValueError(f"Release {tag_clean} body lacks parseable template bundle metadata")

    bundle_url = parsed["url"]
    expected_sha = parsed["sha256"]

    # Download bundle
    req_dl = urllib.request.Request(bundle_url, headers={"User-Agent": "lacd-release-verifier"})
    try:
        with urllib.request.urlopen(req_dl, timeout=60) as resp:
            zip_bytes = resp.read()
    except Exception as exc:
        raise RuntimeError(f"Failed to download bundle from {bundle_url}: {exc}") from exc

    actual_sha = _sha256_hex(zip_bytes)
    if actual_sha != expected_sha:
        raise ValueError(f"Bundle SHA-256 mismatch for {bundle_url}: expected {expected_sha}, got {actual_sha}")

    bundle = load_bundle_from_zip(zip_bytes, expected_sha)
    expected_version = tag_clean.lstrip("v")
    if bundle.version != expected_version:
        raise ValueError(f"Bundle template_version {bundle.version} != tag version {expected_version}")

    # Check wheel asset if present
    wheel_assets = [a for a in rel.get("assets", []) if a.get("name", "").endswith(".whl")]
    for wa in wheel_assets:
        w_url = wa.get("browser_download_url")
        if w_url:
            req_w = urllib.request.Request(w_url, headers={"User-Agent": "lacd-release-verifier"})
            with urllib.request.urlopen(req_w, timeout=60) as resp:
                w_bytes = resp.read()
            with zipfile.ZipFile(tempfile.SpooledTemporaryFile()) as wz:
                pass  # or write to temp and inspect
            # Just verify wheel is valid zip and has no pyc
            with tempfile.NamedTemporaryFile(suffix=".whl") as tf:
                tf.write(w_bytes)
                tf.flush()
                with zipfile.ZipFile(tf.name, "r") as wz:
                    for n in wz.namelist():
                        if "__pycache__" in n or n.endswith(".pyc"):
                            raise ValueError(f"Public wheel contains bytecode cache: {n}")

    print(f"Successfully verified public release {tag_clean} on {repo} (bundle SHA-256: {actual_sha})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LACD release asset builder and verifier")
    parser.add_argument("--out-dir", type=str, default="/tmp/lacd-release-assets", help="Output directory for assets")
    parser.add_argument("--build", action="store_true", help="Build wheel, template ZIP, manifest, and snippet")
    parser.add_argument("--verify", action="store_true", help="Verify assets in out-dir")
    parser.add_argument("--smoke-venv", action="store_true", help="Run smoke test in isolated venv")
    parser.add_argument("--verify-public-release", action="store_true", help="Verify a published GitHub release")
    parser.add_argument("--tag", type=str, default="", help="Release tag (e.g. v1.0.4)")
    parser.add_argument("--repo", type=str, default=DEFAULT_UPSTREAM_REPO, help="GitHub repository (owner/name)")

    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)

    try:
        if args.verify_public_release:
            if not args.tag:
                parser.error("--verify-public-release requires --tag")
            verify_public_release(args.tag, args.repo)
            return 0

        if not (args.build or args.verify or args.smoke_venv):
            parser.error("Specify at least one action: --build, --verify, --smoke-venv, or --verify-public-release")

        if args.build:
            build_assets(out_dir, repo=args.repo)

        if args.verify or args.smoke_venv:
            verify_assets(out_dir, smoke_venv=args.smoke_venv, repo=args.repo)

        return 0
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
