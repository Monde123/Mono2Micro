"""Generate -> Test -> Fix loop (max 3 attempts with automatic rollback).

Enforces M4:
- Deterministic/LLM code proposal application
- Test execution without shell injection
- Max 3 correction attempts
- Automatic rollback/restoration upon failure
- Accounting of trials, tokens, cost, and duration
"""

import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from mono2micro.models.migration import FixLoopAttempt, FixLoopSession
from mono2micro.models.plan import StranglerStep


class GenerateTestFixLoop:
    """Orchestrates test execution and iterative correction loop."""

    def __init__(self, target_directory: str, max_attempts: int = 3):
        self.target_directory = str(Path(target_directory).resolve())
        self.max_attempts = max_attempts

    def run_command_safely(self, command: str) -> Tuple[bool, str]:
        """Execute test command safely without shell=True."""
        try:
            tokens = shlex.split(command)
            if not tokens:
                return False, "Empty test command."
            res = subprocess.run(
                tokens,
                cwd=self.target_directory,
                capture_output=True,
                text=True,
                timeout=60,
                shell=False,
            )
            output = (res.stdout or "") + (res.stderr or "")
            return (res.returncode == 0), output
        except Exception as e:
            return False, f"Execution failed: {str(e)}"

    def execute_loop(
        self,
        step: StranglerStep,
        initial_modifications: Dict[str, str],
        test_command: str,
        fix_generator: Optional[Callable[[int, str], Optional[Dict[str, str]]]] = None,
        tokens_per_attempt: Optional[int] = None,
        cost_per_attempt: Optional[float] = None,
    ) -> FixLoopSession:
        """Run up to 3 generate->test->fix attempts, restoring repo on failure."""
        tok_per_att = tokens_per_attempt if tokens_per_attempt is not None else 0
        cost_per_att = cost_per_attempt if cost_per_attempt is not None else 0.0
        start_session_time = time.time()
        session = FixLoopSession(
            step_number=step.step_number,

            target_context=step.target_bounded_context,
            max_attempts=self.max_attempts,
        )

        # Backup original content of files to touch
        originals: Dict[str, Optional[str]] = {}
        for rel_path in initial_modifications:
            abs_p = os.path.join(self.target_directory, rel_path)
            if os.path.exists(abs_p):
                with open(abs_p, "r", encoding="utf-8", errors="ignore") as f:
                    originals[rel_path] = f.read()
            else:
                originals[rel_path] = None

        current_mods = dict(initial_modifications)

        for attempt_idx in range(1, self.max_attempts + 1):
            att_start = time.time()
            # 1. Write current modifications to disk
            for rel_path, content in current_mods.items():
                abs_p = os.path.join(self.target_directory, rel_path)
                os.makedirs(os.path.dirname(abs_p), exist_ok=True)
                with open(abs_p, "w", encoding="utf-8") as f:
                    f.write(content)

            # 2. Run existing test suite
            passed, test_out = self.run_command_safely(test_command)
            att_duration = round(time.time() - att_start, 3)

            attempt = FixLoopAttempt(
                attempt_number=attempt_idx,
                proposed_diff=f"{len(current_mods)} files modified in attempt {attempt_idx}",
                test_passed=passed,
                test_output=test_out[:500],
                tokens_used=tok_per_att,
                cost_usd=cost_per_att,
                duration_seconds=att_duration,
            )
            session.attempts.append(attempt)
            session.total_tokens_used += tok_per_att
            session.total_cost_usd += cost_per_att

            if passed:
                session.final_success = True
                session.total_duration_seconds = round(time.time() - start_session_time, 3)
                return session

            # If failed and not last attempt, request fix from generator
            if attempt_idx < self.max_attempts and fix_generator is not None:
                next_mods = fix_generator(attempt_idx, test_out)
                if next_mods:
                    current_mods = next_mods
                else:
                    break

        # If loop exited without passing: automatic rollback
        self._restore_files(originals)
        session.final_success = False
        session.restored_automatically = True
        session.total_duration_seconds = round(time.time() - start_session_time, 3)
        return session

    def _restore_files(self, originals: Dict[str, Optional[str]]):
        """Restore all touched files to their exact pre-run state."""
        for rel_path, original_content in originals.items():
            abs_p = os.path.join(self.target_directory, rel_path)
            if original_content is None:
                # File didn't exist before, remove it
                if os.path.exists(abs_p):
                    try:
                        os.remove(abs_p)
                    except OSError:
                        pass
            else:
                with open(abs_p, "w", encoding="utf-8") as f:
                    f.write(original_content)
