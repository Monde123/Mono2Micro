"""LLM-driven 'apply': strict validation of model output and the end-to-end CLI flow."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

import mono2micro.cli as cli_module
from mono2micro.agents.implementer import ImplementerAgent, ProposalError
from mono2micro.cli import app
from mono2micro.config import ProjectStateStore
from mono2micro.core.permissions import PermissionEngine
from mono2micro.llm import LLMClient
from mono2micro.models.plan import (
    DataOwnershipPlan, DataSeparationStrategy, RollbackProcedure,
    RoutingStrategyType, StranglerStep,
)

runner = CliRunner()
SECRET = "sk-ant-SUPERSECRETKEY1234567890abcdef"


class FakeLLM(LLMClient):
    def __init__(self, reply):
        self.reply, self.last_user = reply, ""
    def complete(self, system, user):
        self.last_user = user
        return self.reply if isinstance(self.reply, str) else json.dumps(self.reply)


def _step(files=("src/billing",)):
    return StranglerStep(
        step_number=1, title="Extract Billing", description="pilot",
        target_bounded_context="Billing", files_in_scope=list(files),
        routing_strategy=RoutingStrategyType.STRANGLER_FACADE, routing_details="gateway",
        data_ownership=DataOwnershipPlan(strategy=DataSeparationStrategy.LOGICAL_SCHEMA_SPLIT,
                                         source_tables=[], data_rollback_strategy="mirror"),
        rollback=RollbackProcedure(steps_fr=["a", "b"], git_revert_command="git revert HEAD",
                                   routing_fallback_action="x", data_revert_action="y",
                                   estimated_time_to_recover_minutes=5),
    )


def _project(tmp, with_secret=False):
    root = Path(tmp)
    (root / "src" / "billing").mkdir(parents=True)
    body = "def total(items):\n    return sum(items)\n"
    if with_secret:
        body += f'API_KEY = "{SECRET}"\n'
    (root / "src" / "billing" / "invoice.py").write_text(body, encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_invoice.py").write_text("import pytest\n\ndef test_ok():\n    assert True\n", encoding="utf-8")
    return root


def _agent(tmp):
    return ImplementerAgent(tmp, PermissionEngine(tmp))


NEW_INVOICE = "def total(items):\n    return round(sum(items), 2)\n"


def test_scope_directory_is_expanded_to_source_files():
    with tempfile.TemporaryDirectory() as tmp:
        _project(tmp)
        assert _agent(tmp).expand_scope(_step()) == ["src/billing/invoice.py"]


def test_valid_proposal_is_accepted_and_new_files_must_be_under_prefix():
    with tempfile.TemporaryDirectory() as tmp:
        _project(tmp)
        reply = {"files": {"src/billing/invoice.py": NEW_INVOICE,
                           "services/billing/app.py": "print('svc')\n"}, "notes": "ok"}
        prop = _agent(tmp).propose_modifications(_step(), FakeLLM(reply))
        assert set(prop.files) == {"src/billing/invoice.py", "services/billing/app.py"}
        assert prop.originals["services/billing/app.py"] == ""
        assert prop.new_files_prefix == "services/billing/"


@pytest.mark.parametrize("bad_path", [
    "src/auth/login.py", "../outside.py", "/etc/passwd",
    "services/billing/../../src/auth/x.py", "services/other/x.py", "src//billing/invoice.py",
])
def test_out_of_scope_or_unsafe_paths_are_rejected(bad_path):
    with tempfile.TemporaryDirectory() as tmp:
        _project(tmp)
        reply = {"files": {"src/billing/invoice.py": NEW_INVOICE, bad_path: "x = 1\n"}}
        prop = _agent(tmp).propose_modifications(_step(), FakeLLM(reply))
        assert bad_path in prop.rejected and bad_path not in prop.files


def test_redacted_marker_in_output_is_rejected_to_avoid_corrupting_files():
    with tempfile.TemporaryDirectory() as tmp:
        _project(tmp, with_secret=True)
        reply = {"files": {"src/billing/invoice.py": 'API_KEY = "[REDACTED_VALUE]"\n'}}
        with pytest.raises(ProposalError, match="rejetées"):
            _agent(tmp).propose_modifications(_step(), FakeLLM(reply))


def test_secrets_never_reach_the_model():
    with tempfile.TemporaryDirectory() as tmp:
        _project(tmp, with_secret=True)
        fake = FakeLLM({"files": {"src/billing/invoice.py": NEW_INVOICE}})
        _agent(tmp).propose_modifications(_step(), fake)
        assert SECRET not in fake.last_user


@pytest.mark.parametrize("level", ["METADATA_ONLY", "ANONYMIZED_SYMBOLS"])
def test_code_generation_requires_full_code_policy(level):
    with tempfile.TemporaryDirectory() as tmp:
        _project(tmp)
        with pytest.raises(ProposalError, match="FULL_CODE_REDACTED"):
            _agent(tmp).propose_modifications(_step(), FakeLLM({}), privacy_level=level)


def test_empty_or_garbage_model_output_is_an_error():
    with tempfile.TemporaryDirectory() as tmp:
        _project(tmp)
        for reply in ({"files": {}, "notes": "il manque X"}, "pas du json"):
            with pytest.raises(Exception):
                _agent(tmp).propose_modifications(_step(), FakeLLM(reply))


def test_unchanged_files_are_not_proposed():
    with tempfile.TemporaryDirectory() as tmp:
        root = _project(tmp)
        same = (root / "src/billing/invoice.py").read_text()
        reply = {"files": {"src/billing/invoice.py": same, "services/billing/a.py": "x=1\n"}}
        prop = _agent(tmp).propose_modifications(_step(), FakeLLM(reply))
        assert list(prop.files) == ["services/billing/a.py"]


# ----------------------------------------------------------------- end-to-end CLI

def _git(tmp, *args):
    return subprocess.run(["git", *args], cwd=tmp, capture_output=True, text=True, check=True).stdout.strip()


def _ready_repo(tmp):
    root = _project(tmp)
    store = ProjectStateStore(tmp)
    specs = store.get_user_specifications()
    specs.custom_domains = {"Billing": ["src/billing/**"]}
    specs.llm_provider = "anthropic"
    store.save_user_specifications(specs)
    _git(tmp, "init", "-q")
    _git(tmp, "config", "user.email", "t@t")
    _git(tmp, "config", "user.name", "t")
    _git(tmp, "add", "-A")
    _git(tmp, "commit", "-q", "-m", "init")
    return root, _git(tmp, "rev-parse", "HEAD")


def _patch_llm(monkeypatch, reply):
    monkeypatch.setattr(cli_module, "build_client_from_specs", lambda specs, ask_key=False: FakeLLM(reply))


def test_cli_apply_writes_reviewed_changes_on_an_isolated_branch(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root, base = _ready_repo(tmp)
        _patch_llm(monkeypatch, {
            "files": {"src/billing/invoice.py": NEW_INVOICE,
                      "services/billing/README.md": "# Billing service\n",
                      "src/auth/evil.py": "x=1\n"},
            "notes": "façade ajoutée"})
        result = runner.invoke(app, ["apply", "--path", tmp, "--step", "1", "--confirm", "OUI"])
        assert result.exit_code == 0, result.stdout
        assert (root / "src/billing/invoice.py").read_text() == NEW_INVOICE
        assert (root / "services/billing/README.md").exists()
        assert not (root / "src/auth/evil.py").exists()                  # out of scope: rejected
        assert _git(tmp, "rev-parse", "--abbrev-ref", "HEAD").startswith("mono2micro/step-1")
        assert "def total(items):\n    return sum(items)\n" == _git(tmp, "show", f"{base}:src/billing/invoice.py") + "\n"
        assert (root / ".mono2micro" / "step-1.diff").exists()


def test_cli_apply_refuses_to_overwrite_uncommitted_work(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root, _ = _ready_repo(tmp)
        (root / "src/billing/invoice.py").write_text("# my local edit\n", encoding="utf-8")
        _patch_llm(monkeypatch, {"files": {"src/billing/invoice.py": NEW_INVOICE}})
        result = runner.invoke(app, ["apply", "--path", tmp, "--step", "1", "--confirm", "OUI"])
        assert result.exit_code == 1
        assert (root / "src/billing/invoice.py").read_text() == "# my local edit\n"


def test_cli_apply_without_wrong_confirmation_writes_nothing(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root, _ = _ready_repo(tmp)
        _patch_llm(monkeypatch, {"files": {"src/billing/invoice.py": NEW_INVOICE}})
        result = runner.invoke(app, ["apply", "--path", tmp, "--step", "1", "--confirm", "NON"])
        assert result.exit_code == 1
        assert "def total(items):\n    return sum(items)\n" == (root / "src/billing/invoice.py").read_text()


def test_cli_apply_refuses_code_generation_under_metadata_only(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root, _ = _ready_repo(tmp)
        store = ProjectStateStore(tmp)
        specs = store.get_user_specifications()
        specs.privacy_level = "METADATA_ONLY"
        store.save_user_specifications(specs)
        _patch_llm(monkeypatch, {"files": {"src/billing/invoice.py": NEW_INVOICE}})
        result = runner.invoke(app, ["apply", "--path", tmp, "--step", "1", "--confirm", "OUI"])
        assert result.exit_code == 1
        assert "FULL_CODE_REDACTED" in result.stdout.replace("\n", "")
