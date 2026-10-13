"""Configuration, state persistence and user specifications for local project runs."""

import json
from pathlib import Path
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from mono2micro.core.security import SafePathValidator


STATE_DIR_NAME = ".mono2micro"
USER_SPECS_FILENAME = "user_specifications.json"


class UserSpecifications(BaseModel):
    """User-defined domain preferences, team constraints and safety boundaries."""
    custom_domains: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Domaines métier personnalisés et leurs chemins de fichiers associés (ex: {'Facturation': ['src/billing/**']})"
    )
    forbidden_extractions: List[str] = Field(
        default_factory=list,
        description="Modules ou tables interdits d'extraction en microservice (ex: ['Ledger', 'AuthCore'])"
    )
    preferred_architecture: Optional[str] = Field(
        default=None,
        description="Choix d'architecture préféré par l'équipe (MODULAR_MONOLITH, STRANGLER_MICROSERVICES, KEEP_MONOLITH)"
    )
    team_size: int = Field(
        default=2,
        description="Nombre d'ingénieurs dans l'équipe travaillant sur le projet"
    )
    authorized_test_commands: List[str] = Field(
        default_factory=lambda: ["npm test", "pytest"],
        description="Commandes de test formellement autorisées pour le Quality Gate"
    )
    privacy_level: str = Field(
        default="FULL_CODE_REDACTED",
        description="Politique de confidentialité : FULL_CODE_REDACTED, METADATA_ONLY ou ANONYMIZED_SYMBOLS"
    )
    business_rules_notes: Optional[str] = Field(
        default=None,
        description="Notes et contraintes métier spécifiques rédigées par l'équipe"
    )
    language: str = Field(
        default="fr",
        description="Langue par défaut des rapports et analyses ('fr' ou 'en')"
    )
    llm_provider: Optional[str] = Field(
        default=None,
        description="Fournisseur LLM : openai (ou compatible), anthropic, gemini. None = mode heuristique local. La clé API n'est JAMAIS stockée ici."
    )
    llm_model: Optional[str] = Field(
        default=None,
        description="Nom du modèle à utiliser chez le fournisseur choisi"
    )
    llm_base_url: Optional[str] = Field(
        default=None,
        description="URL de base personnalisée (serveur compatible OpenAI, ex: Ollama local)"
    )


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

    def load_text(self, filename: str) -> Optional[str]:
        target = self.state_dir / filename
        if not target.exists():
            return None
        return target.read_text(encoding="utf-8")

    def get_user_specifications(self) -> UserSpecifications:
        """Load persistent user specifications or return defaults."""
        raw = self.load_json(USER_SPECS_FILENAME)
        if raw:
            try:
                return UserSpecifications(**raw)
            except Exception:
                pass
        
        # Return and save defaults
        default_specs = UserSpecifications()
        self.save_user_specifications(default_specs)
        return default_specs

    def save_user_specifications(self, specs: UserSpecifications):
        """Persist user specifications to .mono2micro/user_specifications.json."""
        self.save_json(USER_SPECS_FILENAME, specs.model_dump())
