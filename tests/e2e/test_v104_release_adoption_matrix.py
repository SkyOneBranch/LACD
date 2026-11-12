"""E2E test suite for WP-A and WP-B (v1.0.4 release and adoption matrix).

Covers:
1. WP-B: test_wp_b_build_verify_and_clean_wheel_smoke
   - scripts/release_assets.py --build --verify --smoke-venv
   - verifies wheel, template zip, manifest, snippet, and smoke venv.
2. WP-A: test_wp_a_alpha_beta_dual_repo_full_adoption_and_upgrade_from_v103
   - builds candidate 1.0.4 wheel and installs into isolated venv.
   - Synthetic Repo Alpha: clean init, dry-run, commit, status (VALIDATED,
     remote_enforcement unverified), verify --local --strict, idempotent init.
   - Synthetic Repo Beta: pre-existing AGENTS.md + ci.yml, v1.0.3 baseline
     with historical source.repo = "SkyCjq/LACD":
     * DRIFT conflict refusal: modified workflow -> exit 3, preserved untouched.
     * Upgrade: dry-run, real upgrade --yes -> AGENTS.md prose preserved,
       ci.yml preserved, lock.json updated (template 1.0.4, cli 1.0.4),
       historical source.repo intact, verify --local --strict passes,
       idempotent re-run zero diff, rollback_last restores v1.0.3 baseline.
3. WP-A: test_wp_a_real_v103_github_release_fixture_and_optional_live
   - tests parse_template_bundle against real v1.0.3 metadata fixture
     (published_at: 2026-10-16T03:48:55Z, zip created_at: 2026-10-16T04:47:38Z,
     sha256: 8f49019eb5fd4febae37732b940fb610daed9361075d7d07c5ac435179507c34)
   - tests fail-closed behavior on v1.0.2 metadata fixture -> None
   - opt-in live check (LACD_LIVE_RELEASE_E2E=1): fetches real v1.0.3 from GitHub,
     validates bundle and checksum.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

import pytest

from lacd.upgrade.migrate import load_bundle_from_zip, rollback_last
from lacd.upgrade.source import parse_template_bundle


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from release_assets import build_assets


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(args: list[str], cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return r.stdout.strip()


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(["init", "-q", "-b", "main", "."], path)
    _git(["config", "user.email", "e2e@test.local"], path)
    _git(["config", "user.name", "E2E Runner"], path)
    return path


def _tree_hashes(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for f in sorted(path.rglob("*")):
        if f.is_file():
            rel = f.relative_to(path).as_posix()
            if rel.startswith(".git/") or rel.startswith(".lacd/backup/"):
                continue
            out[rel] = _sha256_hex(f.read_bytes())
    return out


def test_wp_b_build_verify_and_clean_wheel_smoke(tmp_path):
    """AC-B1/AC-B2: release_assets.py build, verify, and smoke venv."""
    assets_dir = tmp_path / "ci-assets"
    script = REPO_ROOT / "scripts" / "release_assets.py"

    cmd = [
        sys.executable,
        str(script),
        "--out-dir",
        str(assets_dir),
        "--build",
        "--verify",
        "--smoke-venv",
    ]
    r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    assert r.returncode == 0, f"release_assets.py failed:\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}"

    wheel_files = list(assets_dir.glob("lacd-1.0.4*.whl"))
    assert len(wheel_files) == 1, f"Expected 1 wheel, found: {wheel_files}"

    zip_file = assets_dir / "lacd-templates-1.0.4.zip"
    assert zip_file.is_file()

    manifest_file = assets_dir / "release-manifest-1.0.4.json"
    assert manifest_file.is_file()
    m_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert m_data["version"] == "1.0.4"
    assert m_data["manifest_template_version"] == "1.0.4"
    assert m_data["wheel"]["filename"] == wheel_files[0].name
    assert m_data["template_zip"]["filename"] == zip_file.name

    snippet_file = assets_dir / "release-notes-snippet-1.0.4.md"
    assert snippet_file.is_file()
    snippet_text = snippet_file.read_text(encoding="utf-8")
    parsed = parse_template_bundle({"body": snippet_text})
    assert parsed is not None
    assert parsed["sha256"] == m_data["template_zip"]["sha256"]
    assert "https://github.com/SkyOneBranch/LACD/releases/download/v1.0.4/" in parsed["url"]


def test_wp_a_alpha_beta_dual_repo_full_adoption_and_upgrade_from_v103(tmp_path):
    """WP-A: Dual-repo adoption matrix + upgrade from v1.0.3 baseline."""
    # 1. Build real candidate 1.0.4 assets

    assets_dir = tmp_path / "build_assets"
    built = build_assets(assets_dir, repo_root=REPO_ROOT)
    wheel_path = built["wheel_path"]
    zip_path = built["zip_path"]
    zip_sha = built["zip_sha"]

    # 2. Setup isolated venv and install built wheel
    vlacd = tmp_path / "vlacd"
    subprocess.run([sys.executable, "-m", "venv", str(vlacd)], check=True)
    pip_bin = str(vlacd / "bin" / "pip")
    lacd_bin = str(vlacd / "bin" / "lacd")

    r = subprocess.run([pip_bin, "install", str(wheel_path)], capture_output=True, text=True)
    assert r.returncode == 0, f"pip install wheel failed: {r.stderr}\n{r.stdout}"

    r_ver = subprocess.run([lacd_bin, "--version"], capture_output=True, text=True, check=True)
    assert "1.0.4" in r_ver.stdout

    # -----------------------------------------------------------------------
    # Synthetic Repo Alpha (Clean Git repo adoption)
    # -----------------------------------------------------------------------
    alpha = tmp_path / "alpha"
    _init_repo(alpha)

    # init --dry-run: 0 files written
    r = subprocess.run([lacd_bin, "init", "--dry-run", "--path", str(alpha)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    alpha_files = [p for p in alpha.rglob("*") if ".git" not in str(p)]
    assert len(alpha_files) == 0, f"init --dry-run created unexpected files: {alpha_files}"

    # init
    r = subprocess.run([lacd_bin, "init", "--path", str(alpha)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert (alpha / "lacd.yaml").is_file()
    assert (alpha / ".lacd" / "lock.json").is_file()
    assert (alpha / ".github" / "workflows" / "lacd-verify.yml").is_file()

    _git(["add", "-A"], alpha)
    _git(["commit", "-m", "init alpha"], alpha)

    # status --json
    r = subprocess.run([lacd_bin, "status", "--json", "--path", str(alpha)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    status_alpha = json.loads(r.stdout)
    assert status_alpha["state"] == "VALIDATED"
    re_status = status_alpha["dimensions"]["remote_enforcement"]["status"]
    assert re_status == "unverified"
    assert re_status.upper() != "ENFORCED"
    assert status_alpha["state"] != "ENFORCED"

    # verify --local --strict
    r = subprocess.run([lacd_bin, "verify", "--local", "--strict", "--path", str(alpha)], capture_output=True, text=True)
    assert r.returncode == 0, f"verify --local --strict failed:\n{r.stdout}\n{r.stderr}"

    # Idempotent second init
    before_init2 = _tree_hashes(alpha)
    r = subprocess.run([lacd_bin, "init", "--path", str(alpha)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    after_init2 = _tree_hashes(alpha)
    assert before_init2 == after_init2

    # -----------------------------------------------------------------------
    # Synthetic Repo Beta (Pre-existing files + realistic v1.0.3 baseline)
    # -----------------------------------------------------------------------
    beta = tmp_path / "beta"
    _init_repo(beta)

    # Pre-existing project files
    ci_yml_content = "name: project-ci\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo build\n"
    ci_path = beta / ".github" / "workflows" / "ci.yml"
    ci_path.parent.mkdir(parents=True, exist_ok=True)
    ci_path.write_text(ci_yml_content, encoding="utf-8")

    inner_agents = "\n" + (REPO_ROOT / "src" / "lacd" / "templates" / "managed" / "agents-md.section.md").read_text("utf-8")
    if not inner_agents.endswith("\n"):
        inner_agents += "\n"
    agents_sha = _sha256_hex(inner_agents.encode("utf-8"))

    agents_md_content = (
        "# Beta Project\n\n"
        "Custom agents instructions that must be preserved across upgrades.\n\n"
        '<!-- LACD:MANAGED:BEGIN section="lacd-agent-protocol" version="1.0.3" -->'
        + inner_agents +
        "<!-- LACD:MANAGED:END -->\n\n"
        "Beta team trailing notes.\n"
    )
    (beta / "AGENTS.md").write_text(agents_md_content, encoding="utf-8")

    # Realistic v1.0.3 workflow with @v1.0.3 tag (sha256 = c8ca159c95c892e674e0b3c84f64cda673743724493b3d733219a6b10e76c1b6)
    wf_current = (REPO_ROOT / "src" / "lacd" / "templates" / "workflows" / "lacd-verify.yml").read_text("utf-8")
    wf_v103_content = wf_current.replace("@v1.0.4", "@v1.0.3")
    v103_wf_sha = _sha256_hex(wf_v103_content.encode("utf-8"))
    assert v103_wf_sha == "c8ca159c95c892e674e0b3c84f64cda673743724493b3d733219a6b10e76c1b6"

    wf_file = beta / ".github" / "workflows" / "lacd-verify.yml"
    wf_file.write_text(wf_v103_content, encoding="utf-8")

    # Project rules
    rules_content = (REPO_ROOT / "src" / "lacd" / "templates" / "project-rules.template.yaml").read_text("utf-8")
    rules_file = beta / ".lacd" / "project-rules.yaml"
    rules_file.parent.mkdir(parents=True, exist_ok=True)
    rules_file.write_text(rules_content, encoding="utf-8")

    # Config pointing historically to SkyCjq/LACD
    cfg_content = (
        'schema_version: "1"\n'
        "lacd:\n"
        "  enabled: true\n"
        "  mode: lacd\n"
        '  policy_version: "1"\n'
        '  upstream_repo: "SkyCjq/LACD"\n'
        "governance:\n"
        "  pull_request_required: true\n"
        "  human_merge_required: true\n"
        "  risk_tiers:\n"
        "    - T0\n"
        "    - T1\n"
        "    - T2\n"
        "verification:\n"
        "  bind_to_commit_sha: true\n"
        "  fail_closed: true\n"
        "  github_enforcement_required: true\n"
        "agents:\n"
        "  protocol: lacd\n"
        "  auto_detect: true\n"
        "project:\n"
        "  extensions: .lacd/project-rules.yaml\n"
    )
    (beta / "lacd.yaml").write_text(cfg_content, encoding="utf-8")

    # Lockfile seeded with realistic v1.0.3 metadata and historical SkyCjq/LACD repo
    lock_dict = {
        "lock_format_version": "1",
        "lacd_cli_version": "1.0.3",
        "source": {
            "type": "git-tag",
            "repo": "SkyCjq/LACD",
            "ref": "v1.0.3",
            "commit": None,
        },
        "schema_version": "1",
        "policy_version": "1",
        "template_version": "1.0.3",
        "managed_files": [
            {
                "path": ".github/workflows/lacd-verify.yml",
                "sha256": "c8ca159c95c892e674e0b3c84f64cda673743724493b3d733219a6b10e76c1b6",
                "template": "workflows/lacd-verify.yml",
                "template_version": "1.0.3",
                "merge": "replace",
            }
        ],
        "shared_files": [
            {
                "path": "AGENTS.md",
                "section": "lacd-agent-protocol",
                "sha256": agents_sha,
                "template": "managed/agents-md.section.md",
                "template_version": "1.0.3",
                "merge": "marked-section",
            }
        ],
        "generated_at": "2026-10-16T04:47:38+00:00",
        "generated_by": "lacd 1.0.3",
    }
    (beta / ".lacd" / "lock.json").write_text(json.dumps(lock_dict, indent=2), encoding="utf-8")

    _git(["add", "-A"], beta)
    _git(["commit", "-m", "beta v1.0.3 baseline"], beta)

    # Create local upstream directory with releases.json pointing to file:// bundle
    upstream_dir = tmp_path / "upstream_feed"
    upstream_dir.mkdir(parents=True, exist_ok=True)
    feed_doc = {
        "releases": [
            {
                "version": "1.0.4",
                "tag": "v1.0.4",
                "commit": None,
                "published_at": "2026-11-12T00:00:00Z",
                "prerelease": False,
                "template_bundle": {
                    "url": zip_path.resolve().as_uri(),
                    "sha256": zip_sha,
                },
                "notes": "LACD v1.0.4 release",
            }
        ]
    }
    (upstream_dir / "releases.json").write_text(json.dumps(feed_doc, indent=2), encoding="utf-8")
    feed_env = dict(os.environ, LACD_TEMPLATE_DIR=str(upstream_dir))

    # 1) DRIFT conflict refusal: modify managed workflow, run upgrade
    wf_modified = wf_v103_content + "\n# Beta team local workflow customization\n"
    wf_file.write_text(wf_modified, encoding="utf-8")
    _git(["add", "-A"], beta)
    _git(["commit", "-m", "beta custom drift"], beta)

    r_conflict = subprocess.run(
        [
            lacd_bin,
            "upgrade",
            "--to",
            "1.0.4",
            "--path",
            str(beta),
            "--yes",
        ],
        env=feed_env,
        capture_output=True,
        text=True,
    )
    assert r_conflict.returncode == 3, f"Expected conflict code 3, got {r_conflict.returncode}:\n{r_conflict.stdout}\n{r_conflict.stderr}"
    assert wf_file.read_text("utf-8") == wf_modified, "User modification was altered during conflict!"

    # 2) Restore clean v1.0.3 baseline
    _git(["reset", "--hard", "HEAD~1"], beta)
    assert wf_file.read_text("utf-8") == wf_v103_content

    # Upgrade --dry-run: worktree untouched
    before_dry = _tree_hashes(beta)
    r_dry = subprocess.run(
        [
            lacd_bin,
            "upgrade",
            "--dry-run",
            "--to",
            "1.0.4",
            "--path",
            str(beta),
        ],
        env=feed_env,
        capture_output=True,
        text=True,
    )
    assert r_dry.returncode == 0, r_dry.stderr
    assert _tree_hashes(beta) == before_dry

    # Real upgrade --yes
    r_up = subprocess.run(
        [
            lacd_bin,
            "upgrade",
            "--to",
            "1.0.4",
            "--path",
            str(beta),
            "--yes",
        ],
        env=feed_env,
        capture_output=True,
        text=True,
    )
    assert r_up.returncode == 0, f"upgrade failed:\n{r_up.stdout}\n{r_up.stderr}"

    # Assertions on upgraded Beta:
    # 1. User prose preserved
    beta_agents = (beta / "AGENTS.md").read_text("utf-8")
    assert "Custom agents instructions that must be preserved across upgrades." in beta_agents
    assert "Beta team trailing notes." in beta_agents

    # 2. Existing CI preserved
    assert (beta / ".github" / "workflows" / "ci.yml").read_text("utf-8") == ci_yml_content

    # 3. Managed workflow updated to 1.0.4
    beta_wf = wf_file.read_text("utf-8")
    assert "@v1.0.4" in beta_wf

    # 4. Lockfile updated to template 1.0.4 and cli 1.0.4, but historical source.repo NOT falsified
    up_lock = json.loads((beta / ".lacd" / "lock.json").read_text("utf-8"))
    assert up_lock["template_version"] == "1.0.4"
    assert up_lock["lacd_cli_version"] == "1.0.4"
    assert up_lock["source"]["repo"] == "SkyCjq/LACD", "Historical source.repo was overwritten!"

    # 5. verify --local --strict passes
    r_ver = subprocess.run([lacd_bin, "verify", "--local", "--strict", "--path", str(beta)], capture_output=True, text=True)
    assert r_ver.returncode == 0, f"verify failed:\n{r_ver.stdout}\n{r_ver.stderr}"

    _git(["add", "-A"], beta)
    _git(["commit", "-m", "beta upgrade to 1.0.4"], beta)

    # 6. Idempotent re-run: zero diff
    before_idem = _tree_hashes(beta)
    r_idem = subprocess.run(
        [
            lacd_bin,
            "upgrade",
            "--to",
            "1.0.4",
            "--path",
            str(beta),
            "--yes",
        ],
        env=feed_env,
        capture_output=True,
        text=True,
    )
    assert r_idem.returncode == 0, r_idem.stderr
    after_idem = _tree_hashes(beta)
    assert before_idem == after_idem

    # 7. rollback_last restores v1.0.3 baseline
    assert rollback_last(str(beta)) is True
    assert "@v1.0.3" in wf_file.read_text("utf-8")
    rolled_lock = json.loads((beta / ".lacd" / "lock.json").read_text("utf-8"))
    assert rolled_lock["template_version"] == "1.0.3"


def test_wp_a_real_v103_github_release_fixture_and_optional_live(tmp_path):
    """WP-A: parse_template_bundle on real v1.0.3 metadata fixture and optional live test."""
    # Real v1.0.3 fixture (from api.github.com)
    v103_fixture = {
        "tag_name": "v1.0.3",
        "published_at": "2026-10-16T03:48:55Z",
        "assets": [
            {
                "name": "lacd-templates-1.0.3.zip",
                "created_at": "2026-10-16T04:47:38Z",
                "browser_download_url": "https://github.com/SkyOneBranch/LACD/releases/download/v1.0.3/lacd-templates-1.0.3.zip",
            }
        ],
        "body": (
            "LACD v1.0.3 — Repository Migration Compatibility & README Experience Patch\r\n"
            "CI: Python 3.11/3.12 全绿\r\n\r\n"
            "Template bundle\r\n"
            "lacd-templates-1.0.3.zip — SHA-256 verified by lacd upgrade before use:\r\n"
            '{"template_bundle": {"url": "https://github.com/SkyOneBranch/LACD/releases/download/v1.0.3/lacd-templates-1.0.3.zip", "sha256": "8f49019eb5fd4febae37732b940fb610daed9361075d7d07c5ac435179507c34"}}\r\n'
            "Template-Bundle-SHA256: 8f49019eb5fd4febae37732b940fb610daed9361075d7d07c5ac435179507c34"
        ),
    }

    parsed = parse_template_bundle(v103_fixture)
    assert parsed is not None
    assert parsed["sha256"] == "8f49019eb5fd4febae37732b940fb610daed9361075d7d07c5ac435179507c34"
    assert parsed["url"] == "https://github.com/SkyOneBranch/LACD/releases/download/v1.0.3/lacd-templates-1.0.3.zip"

    # Real v1.0.2 fixture (unclosed fence / missing bundle metadata -> fail-closed None)
    v102_fixture = {
        "tag_name": "v1.0.2",
        "published_at": "2026-10-12T15:16:33Z",
        "assets": [
            {
                "name": "lacd-templates-1.0.2.zip",
                "browser_download_url": "https://github.com/SkyOneBranch/LACD/releases/download/v1.0.2/lacd-templates-1.0.2.zip",
            }
        ],
        "body": "## LACD v1.0.2 — patch release\r\n\r\nNo template bundle block in body.\r\n",
    }
    assert parse_template_bundle(v102_fixture) is None

    # Opt-in live check against GitHub API
    if os.environ.get("LACD_LIVE_RELEASE_E2E") == "1":
        url = "https://api.github.com/repos/SkyOneBranch/LACD/releases/tags/v1.0.3"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "lacd-live-e2e-test", "Accept": "application/vnd.github.v3+json"},
        )
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            req.add_header("Authorization", f"Bearer {token}")

        with urllib.request.urlopen(req, timeout=30) as resp:
            live_data = json.loads(resp.read().decode("utf-8"))

        live_parsed = parse_template_bundle(live_data)
        assert live_parsed is not None
        assert live_parsed["sha256"] == "8f49019eb5fd4febae37732b940fb610daed9361075d7d07c5ac435179507c34"
        assert live_parsed["url"] == "https://github.com/SkyOneBranch/LACD/releases/download/v1.0.3/lacd-templates-1.0.3.zip"

        dl_req = urllib.request.Request(live_parsed["url"], headers={"User-Agent": "lacd-live-e2e-test"})
        with urllib.request.urlopen(dl_req, timeout=60) as dl_resp:
            zip_bytes = dl_resp.read()

        actual_sha = _sha256_hex(zip_bytes)
        assert actual_sha == live_parsed["sha256"]

        bundle = load_bundle_from_zip(zip_bytes, actual_sha)
        assert bundle.version == "1.0.3"
