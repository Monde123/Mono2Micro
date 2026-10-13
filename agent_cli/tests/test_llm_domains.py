"""LLM-assisted domain analysis: grounding, caching and safety of untrusted output."""

import json
import tempfile
from pathlib import Path

import pytest

from mono2micro.agents.domain_analyst import DomainAnalystAgent, LLM_CONTEXTS_CACHE
from mono2micro.config import ProjectStateStore, UserSpecifications
from mono2micro.core.permissions import PermissionEngine, PermissionDeniedError
from mono2micro.llm import LLMClient, LLMError
from mono2micro.models.discovery import (
    ComponentType, DatabaseCouplingInfo, DetectedComponent, DiscoveryReport,
)


class FakeLLM(LLMClient):
    def __init__(self, reply):
        self.reply, self.calls, self.last_user = reply, 0, ""
    def complete(self, system, user):
        self.calls += 1
        self.last_user = user
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply if isinstance(self.reply, str) else json.dumps(self.reply)


def _discovery():
    comps = [
        DetectedComponent(name="cart", relative_path="web/cart.py",
                          component_type=ComponentType.API_ROUTER, language="Python", loc_estimate=10),
        DetectedComponent(name="invoice", relative_path="core/invoice.py",
                          component_type=ComponentType.DATABASE_ORM, language="Python", loc_estimate=10),
    ]
    return DiscoveryReport(
        target_directory="/tmp/x", components=comps,
        database_coupling=DatabaseCouplingInfo(
            detected_models_or_tables=["Invoice", "Cart"],
            cross_module_table_access={"Invoice": ["core/invoice.py"]}),
    )


def _run(reply, tmp, discovery=None, llm=True):
    store = ProjectStateStore(tmp)
    fake = FakeLLM(reply)
    hyps = DomainAnalystAgent(tmp).analyze_domains(
        discovery or _discovery(), UserSpecifications(),
        llm=fake if llm else None, cache=store)
    return hyps, fake, store


GOOD = {"contexts": [{"name": "billing", "files": ["core/invoice.py"], "tables": ["Invoice"],
                      "rationale": "Facturation"}]}


def test_grounded_llm_context_becomes_a_hypothesis():
    with tempfile.TemporaryDirectory() as tmp:
        hyps, fake, _ = _run(GOOD, tmp)
        billing = next(h for h in hyps if h.name == "Billing")
        assert "Invoice" in billing.shared_database_tables
        assert billing.user_confirmed is None            # still a hypothesis
        assert fake.calls == 1


def test_ungrounded_and_malformed_contexts_are_discarded():
    bad = {"contexts": [
        {"name": "Ghost", "files": ["does/not/exist.py"], "tables": ["Nope"], "rationale": "x"},
        {"name": "../evil", "files": ["core/invoice.py"], "tables": [], "rationale": "x"},
        "not a dict",
    ]}
    with tempfile.TemporaryDirectory() as tmp:
        hyps, _, _ = _run(bad, tmp)
        names = {h.name for h in hyps}
        assert "Ghost" not in names and "../evil" not in names


def test_second_run_reuses_cache_without_calling_the_model():
    with tempfile.TemporaryDirectory() as tmp:
        _run(GOOD, tmp)
        hyps, fake, _ = _run(GOOD, tmp)
        assert fake.calls == 0
        assert any(h.name == "Billing" for h in hyps)


def test_cache_is_used_even_when_no_llm_is_configured():
    with tempfile.TemporaryDirectory() as tmp:
        _run(GOOD, tmp)
        hyps, _, _ = _run(GOOD, tmp, llm=False)
        assert any(h.name == "Billing" for h in hyps)


def test_cache_invalidated_when_repository_metadata_changes():
    with tempfile.TemporaryDirectory() as tmp:
        _run(GOOD, tmp)
        changed = _discovery()
        changed.database_coupling.detected_models_or_tables.append("Order")
        _, fake, _ = _run(GOOD, tmp, discovery=changed)
        assert fake.calls == 1


def test_llm_failure_degrades_to_heuristics_with_a_warning():
    with tempfile.TemporaryDirectory() as tmp:
        disc = _discovery()
        hyps, _, _ = _run(LLMError("HTTP 401"), tmp, discovery=disc)
        assert hyps                                          # heuristics still produce domains
        assert any("LLM" in lim for lim in disc.analysis_limitations)


def test_only_metadata_is_sent_to_the_model():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "core").mkdir()
        (Path(tmp) / "core" / "invoice.py").write_text("PASSWORD = 'hunter2-top-secret'", encoding="utf-8")
        _, fake, _ = _run(GOOD, tmp)
        assert "hunter2" not in fake.last_user


def test_permission_prefix_allows_new_service_files_but_not_traversal():
    with tempfile.TemporaryDirectory() as tmp:
        pe = PermissionEngine(tmp)
        pe.request_approval_for_step(
            step_number=1, title="t", files_allowed=["src/a.py", "services/billing/"],
            is_destructive=False, is_data_migration=False, user_confirmation_input="OUI")
        pe.verify_permission_to_apply_step(1, ["src/a.py", "services/billing/app.py"])
        for bad in ["services/billing/../../src/secret.py", "services/billing2/x.py", "src/other.py", "/etc/passwd"]:
            with pytest.raises(PermissionDeniedError):
                pe.verify_permission_to_apply_step(1, [bad])
