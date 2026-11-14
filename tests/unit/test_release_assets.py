"""Unit tests for scripts/release_assets.py --verify-public-release.

All tests run offline: ``urllib.request.urlopen`` is mocked, so no real
GitHub request is made in CI. The positive test is the falsification proof
for the v1.0.4 PRV defect: on the pre-fix code it fails with
``zipfile.BadZipFile`` because ``verify_public_release`` opened an empty
``tempfile.SpooledTemporaryFile()`` as a ZIP before inspecting the real
downloaded wheel bytes.
"""

import hashlib
import importlib.util
import io
import json
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "release_assets.py"

BUNDLE_URL = "https://github.com/SkyOneBranch/LACD/releases/download/v1.0.4/lacd-templates-1.0.4.zip"
WHEEL_URL = "https://github.com/SkyOneBranch/LACD/releases/download/v1.0.4/lacd-1.0.4-py3-none-any.whl"
API_URL = "https://api.github.com/repos/SkyOneBranch/LACD/releases/tags/v1.0.4"


def _load_release_assets():
    spec = importlib.util.spec_from_file_location("release_assets_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release_assets = _load_release_assets()


def _valid_wheel_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("lacd-1.0.4.dist-info/METADATA", "Metadata-Version: 2.1\nName: lacd\nVersion: 1.0.4\n")
        zf.writestr("lacd/__init__.py", '__version__ = "1.0.4"\n')
    return buf.getvalue()


def _wheel_bytes_with_pycache() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("lacd/__init__.py", '__version__ = "1.0.4"\n')
        zf.writestr("lacd/__pycache__/__init__.cpython-312.pyc", b"\xa7\x0d\x0d\x0a\x00\x00\x00\x00")
    return buf.getvalue()


class _FakeResponse:
    """Minimal urlopen response: context manager + read()."""

    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def public_release_env(tmp_path, monkeypatch):
    """Build a real template bundle and stub urlopen for the three fetches.

    Returns a dict the test can mutate (``zip_bytes`` / ``wheel_bytes`` /
    ``declared_sha``) before calling ``verify_public_release``.
    """
    zip_path, zip_sha = release_assets.build_template_zip(tmp_path, REPO_ROOT)
    zip_bytes = zip_path.read_bytes()
    assert hashlib.sha256(zip_bytes).hexdigest() == zip_sha

    env = {
        "zip_bytes": zip_bytes,
        "wheel_bytes": _valid_wheel_bytes(),
        "declared_sha": zip_sha,
    }

    def fake_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if url == API_URL:
            body = (
                "## Template bundle\n\n"
                "`lacd-templates-1.0.4.zip` — SHA-256 verified by `lacd upgrade` before use:\n\n"
                "```json\n"
                + json.dumps(
                    {"template_bundle": {"url": BUNDLE_URL, "sha256": env["declared_sha"]}}
                )
                + "\n```\n\n"
                f"Template-Bundle-SHA256: {env['declared_sha']}\n"
            )
            rel = {
                "tag_name": "v1.0.4",
                "body": body,
                "assets": [
                    {"name": "lacd-templates-1.0.4.zip", "browser_download_url": BUNDLE_URL},
                    {"name": "lacd-1.0.4-py3-none-any.whl", "browser_download_url": WHEEL_URL},
                ],
            }
            return _FakeResponse(json.dumps(rel).encode("utf-8"))
        if url == BUNDLE_URL:
            return _FakeResponse(env["zip_bytes"])
        if url == WHEEL_URL:
            return _FakeResponse(env["wheel_bytes"])
        raise AssertionError(f"unexpected urlopen URL in test: {url}")

    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    return env


def test_verify_public_release_valid_release_passes(public_release_env):
    """Falsification anchor: fails on pre-fix code (BadZipFile from the
    empty-SpooledTemporaryFile block), passes after the fix (exit 0)."""
    release_assets.verify_public_release("v1.0.4", "SkyOneBranch/LACD")


def test_verify_public_release_corrupt_wheel_fails(public_release_env):
    public_release_env["wheel_bytes"] = b"this is not a zip archive"
    with pytest.raises(zipfile.BadZipFile):
        release_assets.verify_public_release("v1.0.4", "SkyOneBranch/LACD")


def test_verify_public_release_wheel_with_pycache_fails(public_release_env):
    public_release_env["wheel_bytes"] = _wheel_bytes_with_pycache()
    with pytest.raises(ValueError, match="bytecode cache"):
        release_assets.verify_public_release("v1.0.4", "SkyOneBranch/LACD")


def test_verify_public_release_bundle_sha_mismatch_fails(public_release_env):
    public_release_env["zip_bytes"] = b"tampered bundle bytes"
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        release_assets.verify_public_release("v1.0.4", "SkyOneBranch/LACD")
