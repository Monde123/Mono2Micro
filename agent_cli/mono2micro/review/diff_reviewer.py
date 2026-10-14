"""Adversarial diff reviewer enforcing architectural boundaries and anti-coupling rules."""

import re
from typing import List, Optional, Set

from mono2micro.models.memory import (
    AdversarialDiffRule,
    AdversarialDiffViolation,
)


class AdversarialDiffReviewer:
    """Inspects candidate code changes and diffs to reject illegal couplings before writing."""

    def __init__(self, reviewer_llm=None):
        self.reviewer_llm = reviewer_llm

    def review_diff(
        self,
        diff_text: str,
        files_allowed: Optional[List[str]] = None,
        owned_tables: Optional[List[str]] = None,
        forbidden_imports: Optional[List[str]] = None,
    ) -> List[AdversarialDiffViolation]:
        """Apply deterministic adversarial rules to a code diff."""
        violations: List[AdversarialDiffViolation] = []
        allowed_set = set(files_allowed) if files_allowed else set()
        owned_tables_lower = set(t.lower() for t in owned_tables) if owned_tables else set()
        forbidden_imports = forbidden_imports or []

        current_file = ""
        line_num = 0
        sync_calls = []

        for line in diff_text.splitlines():
            # Track target file from diff header
            if line.startswith("+++ b/"):
                current_file = line[6:].strip()
                line_num = 0
                continue
            elif line.startswith("@@"):
                # Chunk header e.g. @@ -1,4 +1,6 @@
                m = re.search(r'\+(\d+)', line)
                if m:
                    line_num = int(m.group(1)) - 1
                continue

            if not line.startswith("+") or line.startswith("+++"):
                line_num += 1
                continue

            # We are analyzing an added/modified line
            line_num += 1
            added_content = line[1:].strip()

            # Rule 1: New out of scope imports or forbidden internal imports
            import_match = re.search(r'(?:from\s+([a-zA-Z0-9_.]+)\s+import|import\s+([a-zA-Z0-9_.]+))', added_content)
            if import_match:
                imp = import_match.group(1) or import_match.group(2)
                for forbidden in forbidden_imports:
                    if imp.startswith(forbidden):
                        violations.append(AdversarialDiffViolation(
                            rule=AdversarialDiffRule.NEW_OUT_OF_SCOPE_IMPORT,
                            file_path=current_file,
                            line_number=line_num,
                            description=f"Forbidden import '{imp}' violates domain encapsulation boundary.",
                            code_excerpt=added_content,
                        ))

            # Rule 2: Direct cross-domain table access
            if owned_tables_lower:
                sql_match = re.search(r'(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z0-9_]+)', added_content, re.IGNORECASE)
                if sql_match:
                    tbl = sql_match.group(1).lower()
                    if tbl not in ("where", "select", "set", "values", "inner", "left", "right") and tbl not in owned_tables_lower:
                        violations.append(AdversarialDiffViolation(
                            rule=AdversarialDiffRule.DIRECT_CROSS_DOMAIN_TABLE_ACCESS,
                            file_path=current_file,
                            line_number=line_num,
                            description=f"Direct query to foreign table '{tbl}' outside bounded context tables {sorted(owned_tables_lower)}.",
                            code_excerpt=added_content,
                        ))

            # Rule 3: Synchronous chained RPC calls
            if re.search(r'(?:requests\.(?:get|post|put|delete)|httpx\.(?:get|post)|http\.(?:get|post)|axios\.(?:get|post))', added_content):
                sync_calls.append((current_file, line_num, added_content))
                if len(sync_calls) >= 2 or re.search(r'for\s+.*?\s+in', added_content):
                    violations.append(AdversarialDiffViolation(
                        rule=AdversarialDiffRule.SYNCHRONOUS_CHAINED_RPC,
                        file_path=current_file,
                        line_number=line_num,
                        description="Synchronous cascading RPC calls detected across domain services; asynchronous outbox or events required.",
                        code_excerpt=added_content,
                    ))

            # Rule 4: Prompt injection pattern inside comments
            if re.search(r'#.*?(?:ignore all previous instructions|system prompt override|you are now in)', added_content, re.IGNORECASE):
                violations.append(AdversarialDiffViolation(
                    rule=AdversarialDiffRule.PROMPT_INJECTION_PATTERN_DETECTED,
                    file_path=current_file,
                    line_number=line_num,
                    description="Suspicious prompt injection directive detected in diff comment.",
                    code_excerpt=added_content,
                ))

        # Optional second-opinion review via independent reviewer LLM
        if self.reviewer_llm is not None and not violations:
            try:
                prompt = (
                    "Act as an independent adversarial software reviewer. "
                    "Analyze this diff for hidden architectural leaks, cross-service synchronous locks, or data boundary violations. "
                    "Reply with VALID if clean, or INVALID: <reason> if flawed.\n\n"
                    f"DIFF:\n{diff_text[:3000]}"
                )
                resp = self.reviewer_llm.generate(prompt)
                if "INVALID:" in resp:
                    reason = resp.split("INVALID:", 1)[1].strip()
                    violations.append(AdversarialDiffViolation(
                        rule=AdversarialDiffRule.NEW_OUT_OF_SCOPE_IMPORT,
                        file_path=current_file or "unknown",
                        line_number=1,
                        description=f"Independent LLM reviewer objection: {reason}",
                        code_excerpt=None,
                    ))
            except Exception:
                pass

        return violations
