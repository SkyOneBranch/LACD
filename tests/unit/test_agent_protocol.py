"""Unit tests for lacd.agents.protocol (MODULE_CONTRACT §7).

The `core` modules (Agent-A/B deliverables) are not present yet, so these
tests install faithful test doubles in sys.modules with the exact contract
signatures. The point under test is that `agent_checklist` really calls
through to `core.state.compute_state` and `core.report.build_status_dict`
(AT-24) rather than reading a static file.
"""

import sys
import types
from pathlib import Path

from lacd.agents.protocol import (
    MANAGED_BEGIN,
    agent_checklist,
    read_project_instructions,
)


def _install_fake_core(monkeypatch, state_value="VALIDATED"):
    """Install fake lacd.core.state / lacd.core.report recording calls."""
    calls = {}

    core_pkg = types.ModuleType("lacd.core")
    core_pkg.__path__ = []  # mark as package
    state_mod = types.ModuleType("lacd.core.state")
    report_mod = types.ModuleType("lacd.core.report")

    class _StateReport:
        def __init__(self, state):
            self.state = state

    def compute_state(project_dir, remote=None):
        calls["compute_state"] = str(project_dir)
        return _StateReport(state_value)

    def build_status_dict(project_dir, remote=None):
        calls["build_status_dict"] = str(project_dir)
        return {
            "schema": "lacd-status/1",
            "state": state_value,
            "project_dir": str(project_dir),
            "dimensions": {},
        }

    state_mod.compute_state = compute_state
    report_mod.build_status_dict = build_status_dict
    monkeypatch.setitem(sys.modules, "lacd.core", core_pkg)
    monkeypatch.setitem(sys.modules, "lacd.core.state", state_mod)
    monkeypatch.setitem(sys.modules, "lacd.core.report", report_mod)
    return calls


def _write_agents(tmp_path, managed=True):
    body = "# Project instructions\n\nDo the thing.\n"
    if managed:
        body += f"\n{MANAGED_BEGIN}\n- run lacd status\n<!-- LACD:MANAGED:END -->\n"
    (tmp_path / "AGENTS.md").write_text(body, encoding="utf-8")


# ---------- read_project_instructions ----------

def test_read_instructions_found_with_managed_section(tmp_path):
    _write_agents(tmp_path, managed=True)
    info = read_project_instructions(tmp_path)
    assert info["found"] is True
    assert info["path"] == str(tmp_path / "AGENTS.md")
    assert info["managed_section_present"] is True
    assert info["chars"] > 0


def test_read_instructions_found_without_managed_section(tmp_path):
    _write_agents(tmp_path, managed=False)
    info = read_project_instructions(tmp_path)
    assert info["found"] is True
    assert info["managed_section_present"] is False


def test_read_instructions_missing(tmp_path):
    info = read_project_instructions(tmp_path)
    assert info == {
        "found": False,
        "path": None,
        "managed_section_present": False,
        "chars": 0,
    }


# ---------- agent_checklist: real delegation to core ----------

def test_checklist_calls_live_core_modules(tmp_path, monkeypatch):
    calls = _install_fake_core(monkeypatch, "VALIDATED")
    _write_agents(tmp_path, managed=True)

    result = agent_checklist(tmp_path, intended_paths=["src/x.py"])

    # AT-24: both core entry points were really invoked with the project dir.
    assert calls["compute_state"] == str(tmp_path)
    assert calls["build_status_dict"] == str(tmp_path)

    assert set(result) == {"instructions", "status", "risk_tier", "rules", "ready"}
    assert result["instructions"]["found"] is True
    assert result["instructions"]["managed_section_present"] is True
    assert result["status"]["state"] == "VALIDATED"
    assert result["risk_tier"] == "T1"
    assert isinstance(result["rules"], list) and len(result["rules"]) >= 3
    assert any("lacd status --json" in rule for rule in result["rules"])
    assert result["ready"] is True


def test_checklist_no_agents_md_is_not_ready(tmp_path, monkeypatch):
    _install_fake_core(monkeypatch, "VALIDATED")
    result = agent_checklist(tmp_path)
    assert result["instructions"]["found"] is False
    assert result["ready"] is False
    assert result["risk_tier"] is None


def test_checklist_blocked_state_is_not_ready(tmp_path, monkeypatch):
    _install_fake_core(monkeypatch, "BLOCKED")
    _write_agents(tmp_path, managed=True)
    result = agent_checklist(tmp_path, intended_paths=[".github/workflows/w.yml"])
    assert result["ready"] is False
    assert result["risk_tier"] == "T2"
    assert any("T2" in rule for rule in result["rules"])


def test_checklist_unverified_state_warns(tmp_path, monkeypatch):
    _install_fake_core(monkeypatch, "UNVERIFIED")
    _write_agents(tmp_path, managed=True)
    result = agent_checklist(tmp_path)
    assert result["ready"] is False
    assert any("UNVERIFIED" in rule for rule in result["rules"])


def test_checklist_t0_paths(tmp_path, monkeypatch):
    _install_fake_core(monkeypatch, "ENFORCED")
    _write_agents(tmp_path, managed=True)
    result = agent_checklist(tmp_path, intended_paths=["docs/guide.md"])
    assert result["risk_tier"] == "T0"
    assert result["ready"] is True


# ---------- regression & security negative tests (B-01) ----------

import pytest


@pytest.mark.parametrize("version", ["1.0.0", "1.0.3", "1.0.4", "2.1.0"])
def test_read_instructions_valid_semver_versions(tmp_path, version):
    agents = (
        f"# Project instructions\n\n"
        f'<!-- LACD:MANAGED:BEGIN section="lacd-agent-protocol" version="{version}" -->\n'
        f"- run lacd status\n"
        f"<!-- LACD:MANAGED:END -->\n"
    )
    (tmp_path / "AGENTS.md").write_text(agents, encoding="utf-8")
    info = read_project_instructions(tmp_path)
    assert info["found"] is True
    assert info["managed_section_present"] is True


def test_read_instructions_real_lacd_init_output(tmp_path):
    from lacd.cli.main import main
    rc = main(["init", "--path", str(tmp_path)])
    assert rc == 0
    info = read_project_instructions(tmp_path)
    assert info["found"] is True
    assert info["managed_section_present"] is True


def test_read_instructions_rejects_wrong_section_name(tmp_path):
    agents = (
        "# Project instructions\n\n"
        '<!-- LACD:MANAGED:BEGIN section="other-section" version="1.0.3" -->\n'
        "- run lacd status\n"
        "<!-- LACD:MANAGED:END -->\n"
    )
    (tmp_path / "AGENTS.md").write_text(agents, encoding="utf-8")
    info = read_project_instructions(tmp_path)
    assert info["found"] is True
    assert info["managed_section_present"] is False


@pytest.mark.parametrize("content", [
    # missing END marker
    '<!-- LACD:MANAGED:BEGIN section="lacd-agent-protocol" version="1.0.0" -->\n- run lacd status\n',
    # END marker appearing only before BEGIN marker
    '<!-- LACD:MANAGED:END -->\n<!-- LACD:MANAGED:BEGIN section="lacd-agent-protocol" version="1.0.0" -->\n',
    # malformed non-SemVer version=""
    '<!-- LACD:MANAGED:BEGIN section="lacd-agent-protocol" version="" -->\n<!-- LACD:MANAGED:END -->\n',
    # malformed non-SemVer version="bad"
    '<!-- LACD:MANAGED:BEGIN section="lacd-agent-protocol" version="bad" -->\n<!-- LACD:MANAGED:END -->\n',
])
def test_read_instructions_rejects_invalid_managed_sections(tmp_path, content):
    (tmp_path / "AGENTS.md").write_text(content, encoding="utf-8")
    info = read_project_instructions(tmp_path)
    assert info["found"] is True
    assert info["managed_section_present"] is False

