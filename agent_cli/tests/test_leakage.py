"""Leakage prevention test for benchmark and domain analyst LLM prompts."""

import json
from mono2micro.agents.domain_analyst import DomainAnalystAgent
from mono2micro.models.discovery import DiscoveryReport, DatabaseCouplingInfo


def test_prompt_zero_leakage():
    """G6: Prompts sent to LLM must not contain reference domains or ground truth labels."""
    agent = DomainAnalystAgent("/tmp")
    discovery = DiscoveryReport(
        scanned_path="/tmp",
        languages_detected=["python"],
        frameworks_detected=["flask"],
        database_coupling=DatabaseCouplingInfo(
            detected_models_or_tables=["users", "orders"],
            cross_module_table_access={"users": ["app/routes.py"]},
        ),
    )
    
    # Candidate names inferred from heuristics
    candidates = ["UserDomain", "OrderDomain"]
    payload = agent._llm_payload(discovery, candidates, user_specs=None)
    payload_str = json.dumps(payload).lower()

    # Verify zero contamination of ground truth or benchmark reference labels
    assert "ground_truth" not in payload_str
    assert "reference_domains" not in payload_str
    assert "secret_label" not in payload_str
    assert "jpetstore" not in payload_str
