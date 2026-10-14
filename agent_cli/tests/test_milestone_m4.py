"""Milestone 4 (M4) Tests: Deterministic Codemods & Generate->Test->Fix Loop.

Acceptance criteria:
- Deterministic codemods (extract, facade, gateway, feature flags, SQL schema split)
- Generate -> Test -> Fix loop with max 3 attempts
- Automatic rollback/restoration when tests fail after 3 attempts
- Existing tests pass after apply on benchmark application
- Reports attempts count, tokens consumed, cost, and duration
"""

import sys
from pathlib import Path
import pytest

from mono2micro.migration.codemods import DeterministicCodemods
from mono2micro.migration.fix_loop import GenerateTestFixLoop
from mono2micro.models.plan import StranglerStep, RoutingStrategyType, DataOwnershipPlan, DataSeparationStrategy, RollbackProcedure
from mono2micro.models.migration import GatewayRouteConfig, FeatureFlagConfig


def _sample_step() -> StranglerStep:
    return StranglerStep(
        step_number=1,
        title="Extract Billing Service",
        description="Extract billing calculation to dedicated service",
        target_bounded_context="Billing",
        files_in_scope=["services/billing.py"],
        routing_strategy=RoutingStrategyType.API_GATEWAY_REVERSE_PROXY,
        routing_details="/api/billing/* -> billing_svc:8081",
        data_ownership=DataOwnershipPlan(
            strategy=DataSeparationStrategy.DATABASE_PER_SERVICE,
            source_tables=["invoices"],
            target_tables=["billing_invoices"],
            data_rollback_strategy="restore database backup",
        ),
        rollback=RollbackProcedure(
            steps_fr=["git checkout main"],
            git_revert_command="git revert HEAD",
            routing_fallback_action="route traffic back to monolith",
            data_revert_action="replay events",
            estimated_time_to_recover_minutes=2,
        ),
    )


def test_m4_deterministic_function_extraction_and_facade():
    source_code = (
        "import math\n\n"
        "def compute_tax(amount: float) -> float:\n"
        "    return round(amount * 0.20, 2)\n\n"
        "def calculate_total(amount: float) -> float:\n"
        "    return amount + compute_tax(amount)\n"
    )

    updated_src, new_module = DeterministicCodemods.extract_python_function(
        source_code=source_code,
        target_func_name="compute_tax",
        target_module_rel_path="services/tax_service.py",
    )

    # New module contains compute_tax
    assert "def compute_tax" in new_module
    # Source code now has facade import forwarder
    assert "from services.tax_service import compute_tax" in updated_src
    assert "def calculate_total" in updated_src


def test_m4_deterministic_gateway_and_feature_flags_generation():
    routes = [
        GatewayRouteConfig(
            service_name="BillingService",
            route_prefix="billing",
            upstream_url="http://billing-svc:8081",
            feature_flag_key="ENABLE_BILLING_SERVICE",
        )
    ]
    gateway_code = DeterministicCodemods.generate_api_gateway_routes(routes, framework="fastapi")
    assert "route_to_billingservice" in gateway_code
    assert "ENABLE_BILLING_SERVICE" in gateway_code

    flags = [
        FeatureFlagConfig(
            flag_key="ENABLE_BILLING_SERVICE",
            enabled=True,
            description="Toggle routing to billing microservice",
        )
    ]
    flags_code = DeterministicCodemods.generate_feature_flags_module(flags)
    assert "ENABLE_BILLING_SERVICE" in flags_code
    assert "is_feature_enabled" in flags_code


def test_m4_deterministic_schema_sql_split():
    full_ddl = (
        "CREATE TABLE accounts (id INT PRIMARY KEY, name VARCHAR(100));\n"
        "CREATE TABLE invoices (id INT PRIMARY KEY, amount NUMERIC);\n"
        "CREATE TABLE orders (id INT PRIMARY KEY, total NUMERIC);\n"
    )
    retained_sql, extracted_sql = DeterministicCodemods.split_database_schema_sql(
        full_schema_sql=full_ddl,
        tables_to_extract=["invoices"],
    )
    assert "CREATE TABLE invoices" in extracted_sql
    assert "CREATE TABLE accounts" in retained_sql
    assert "CREATE TABLE orders" in retained_sql
    assert "CREATE TABLE invoices" not in retained_sql


def test_m4_fix_loop_passes_and_reports_metrics(tmp_path):
    # Setup mini project with existing unit test
    calc_py = tmp_path / "calculator.py"
    calc_py.write_text("def add(a, b): return a + b\n")

    test_py = tmp_path / "test_calc.py"
    test_py.write_text("from calculator import add\ndef test_add(): assert add(2, 3) == 5\n")

    step = _sample_step()
    loop = GenerateTestFixLoop(target_directory=str(tmp_path), max_attempts=3)

    # Modification that preserves existing test pass
    mods = {
        "calculator.py": "def add(a, b): return a + b\ndef multiply(a, b): return a * b\n",
    }
    test_cmd = f"{sys.executable} -m pytest test_calc.py"

    session = loop.execute_loop(
        step=step,
        initial_modifications=mods,
        test_command=test_cmd,
        tokens_per_attempt=150,
        cost_per_attempt=0.0005,
    )


    assert session.final_success is True
    assert len(session.attempts) == 1
    assert session.attempts[0].test_passed is True
    assert session.total_tokens_used > 0
    assert session.total_cost_usd > 0.0
    assert session.total_duration_seconds >= 0.0


def test_m4_fix_loop_auto_restores_on_3_failures(tmp_path):
    # Setup project with test expecting 42
    target_py = tmp_path / "app.py"
    original_code = "def get_val(): return 42\n"
    target_py.write_text(original_code)

    test_py = tmp_path / "test_app.py"
    test_py.write_text("from app import get_val\ndef test_val(): assert get_val() == 42\n")

    step = _sample_step()
    loop = GenerateTestFixLoop(target_directory=str(tmp_path), max_attempts=3)

    # Bad modifications that break the test
    bad_mods = {"app.py": "def get_val(): return 0\n"}
    test_cmd = f"{sys.executable} -m pytest test_app.py"

    # Generator also produces failing fixes
    def bad_fix_gen(attempt_num: int, output: str):
        return {"app.py": f"def get_val(): return {attempt_num}\n"}

    session = loop.execute_loop(
        step=step,
        initial_modifications=bad_mods,
        test_command=test_cmd,
        fix_generator=bad_fix_gen,
    )

    # After 3 failed attempts: must fail and restore automatically
    assert session.final_success is False
    assert session.restored_automatically is True
    assert len(session.attempts) == 3

    # File must be restored to original content!
    assert target_py.read_text() == original_code
