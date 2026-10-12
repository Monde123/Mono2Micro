"""Tests for PermissionEngine and safety boundaries."""

import pytest
from mono2micro.core.permissions import (
    PermissionEngine,
    PermissionDeniedError,
    ActionScope,
)


def test_permission_denied_without_approval():
    engine = PermissionEngine(target_directory="/workspace/app")
    
    # Trying to apply step 1 without approval should fail
    with pytest.raises(PermissionDeniedError) as exc_info:
        engine.verify_permission_to_apply_step(step_number=1, target_files=["src/auth.py"])
    
    assert "n'a reçu aucune approbation humaine explicite" in str(exc_info.value)


def test_step_isolation_approving_step_1_does_not_approve_step_2():
    engine = PermissionEngine(target_directory="/workspace/app")
    
    # Approve step 1
    engine.request_approval_for_step(
        step_number=1,
        title="Extract Logging",
        files_allowed=["src/logger.py"],
        user_confirmation_input="OUI"
    )
    
    # Step 1 passes
    record = engine.verify_permission_to_apply_step(step_number=1, target_files=["src/logger.py"])
    assert record.step_number == 1
    
    # Step 2 strictly FAILS
    with pytest.raises(PermissionDeniedError) as exc_info:
        engine.verify_permission_to_apply_step(step_number=2, target_files=["src/billing.py"])
    
    assert "L'étape 2 n'a reçu aucune approbation humaine explicite" in str(exc_info.value)


def test_file_scope_boundary_enforcement():
    engine = PermissionEngine(target_directory="/workspace/app")
    
    engine.request_approval_for_step(
        step_number=1,
        title="Refactor routes",
        files_allowed=["src/routes/users.py", "src/routes/auth.py"],
        user_confirmation_input="OUI"
    )
    
    # Allowed files
    engine.verify_permission_to_apply_step(
        step_number=1,
        target_files=["src/routes/users.py"]
    )
    
    # Attempting to touch unapproved file outside scope MUST FAIL
    with pytest.raises(PermissionDeniedError) as exc_info:
        engine.verify_permission_to_apply_step(
            step_number=1,
            target_files=["src/routes/users.py", "src/database/secret_config.py"]
        )
    
    assert "VIOLATION DE PÉRIMÈTRE" in str(exc_info.value)
    assert "secret_config.py" in str(exc_info.value)


def test_rejection_on_invalid_confirmation_string():
    engine = PermissionEngine(target_directory="/workspace/app")
    
    with pytest.raises(PermissionDeniedError) as exc_info:
        engine.request_approval_for_step(
            step_number=1,
            title="Format DB",
            files_allowed=["schema.sql"],
            user_confirmation_input="NON"
        )
    assert "Action refusée pour l'étape 1" in str(exc_info.value)


def test_step_execution_invalidation_prevents_replay():
    engine = PermissionEngine(target_directory="/workspace/app")
    
    engine.request_approval_for_step(
        step_number=1,
        title="Migrate",
        files_allowed=["file1.py"],
        user_confirmation_input="OUI"
    )
    
    # Execute step
    engine.mark_step_executed(step_number=1)
    
    # Verifying again should fail
    with pytest.raises(PermissionDeniedError):
        engine.verify_permission_to_apply_step(step_number=1, target_files=["file1.py"])
        
    # Re-requesting same executed step should fail
    with pytest.raises(PermissionDeniedError) as exc_info:
        engine.request_approval_for_step(
            step_number=1,
            title="Migrate again",
            files_allowed=["file1.py"],
            user_confirmation_input="OUI"
        )
    assert "a déjà été exécutée" in str(exc_info.value)
