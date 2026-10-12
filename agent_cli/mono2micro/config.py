"""Configuration and state persistence for local project runs."""

import json
from pathlib import Path
from typing import Optional
from mono2micro.core.security import SafePathValidator


STATE_DIR_NAME = ".mono2micro"


class ProjectStateStore:
    """Manages local state artifacts stored inside the analyzed project."""

    def __init__(self, target_dir: str):
        self.validator = SafePathValidator(target_dir)
        self.base_path = self.validator.base_path
        self.state_dir = self.base_path / STATE_DIR_NAME
        self._ensure_state_dir()

    def _ensure_state_dir(self):
        """Create .mono2micro/ and ensure it is listed in .gitignore."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        gitignore_path = self.base_path / ".gitignore"
        try:
            if gitignore_path.exists():
                content = gitignore_path.read_text(encoding="utf-8")
                if STATE_DIR_NAME not in content:
                    gitignore_path.write_text(content.rstrip() + f"\n\n# Mono2Micro Agent State\n{STATE_DIR_NAME}/\n", encoding="utf-8")
            else:
                gitignore_path.write_text(f"# Mono2Micro Agent State\n{STATE_DIR_NAME}/\n", encoding="utf-8")
        except Exception:
            pass

    def save_json(self, filename: str, data: dict):
        """Persist a JSON artifact safely inside .mono2micro/."""
        target = self.state_dir / filename
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    def load_json(self, filename: str) -> Optional[dict]:
        """Load a JSON artifact from .mono2micro/ if present."""
        target = self.state_dir / filename
        if not target.exists():
            return None
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            return None

    def save_text(self, filename: str, content: str):
        """Save a Markdown or text artifact inside .mono2micro/."""
        target = self.state_dir / filename
        target.write_text(content, encoding="utf-8")
