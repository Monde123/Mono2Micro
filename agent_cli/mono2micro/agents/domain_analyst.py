"""Domain Analyst Agent (Role 2).

Identifies business boundaries and proposes candidate Bounded Contexts.
Grounded in Principle 2 of Hammad et al. (2023):
Decompose along domain boundaries (DDD) rather than technical horizontal tiers.
All domain proposals are hypotheses requiring user confirmation.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set, Optional
from mono2micro.models.discovery import DiscoveryReport, ComponentType
from mono2micro.models.domains import (
    BoundedContextHypothesis,
    DomainEvidence,
    DomainEvidenceSource,
    CouplingLevel,
)
from mono2micro.config import UserSpecifications


class DomainAnalystAgent:
    """Agent in charge of bounded context identification and coupling evaluation."""

    def __init__(self, target_directory: str):
        self.target_directory = target_directory

    def analyze_domains(
        self,
        discovery: DiscoveryReport,
        user_specs: Optional[UserSpecifications] = None
    ) -> List[BoundedContextHypothesis]:
        """Infer candidate bounded contexts from files, route prefixes, and DB models, honoring user specifications."""
        candidate_map: Dict[str, Dict] = {}

        # 0. Incorporate explicit user specifications if defined
        if user_specs and user_specs.custom_domains:
            for custom_name, file_patterns in user_specs.custom_domains.items():
                candidate_map[custom_name] = {
                    "evidences": [
                        DomainEvidence(
                            source_type=DomainEvidenceSource.USER_DOMAIN_SPEC,
                            file_or_symbol_path=", ".join(file_patterns),
                            description="Domaine métier explicitement défini par l'équipe",
                            strength=1.0
                        )
                    ],
                    "entities": [],
                    "endpoints": [],
                    "files": list(file_patterns),
                    "tables": [],
                    "user_confirmed": True
                }

        # 1. Inspect directory structure hints (e.g., src/auth, src/billing, src/catalog)
        target_path = Path(self.target_directory)
        common_domain_roots = ["src", "app", "lib", "services", "modules"]
        
        for root_name in common_domain_roots:
            candidate_dir = target_path / root_name
            if candidate_dir.exists() and candidate_dir.is_dir():
                for sub in candidate_dir.iterdir():
                    if sub.is_dir() and not sub.name.startswith((".", "_")):
                        name = sub.name.capitalize()
                        if name not in ("Utils", "Common", "Shared", "Config", "Middleware"):
                            candidate_map.setdefault(name, {
                                "evidences": [],
                                "entities": [],
                                "endpoints": [],
                                "files": [],
                                "tables": []
                            })
                            candidate_map[name]["evidences"].append(
                                DomainEvidence(
                                    source_type=DomainEvidenceSource.DIRECTORY_STRUCTURE,
                                    file_or_symbol_path=str(sub.relative_to(target_path)),
                                    description=f"Sous-répertoire modulaire dédié identifié dans {root_name}/",
                                    strength=0.8
                                )
                            )
                            candidate_map[name]["files"].append(str(sub.relative_to(target_path)))

        # 2. Inspect route components for domain hints
        for comp in discovery.components:
            if comp.component_type == ComponentType.API_ROUTER:
                domain_name = self._infer_domain_from_name(comp.name)
                candidate_map.setdefault(domain_name, {
                    "evidences": [],
                    "entities": [],
                    "endpoints": [],
                    "files": [],
                    "tables": []
                })
                candidate_map[domain_name]["endpoints"].append(comp.relative_path)
                candidate_map[domain_name]["evidences"].append(
                    DomainEvidence(
                        source_type=DomainEvidenceSource.API_ROUTE_PREFIX,
                        file_or_symbol_path=comp.relative_path,
                        description=f"Contrôleur ou routeur d'API associé au domaine",
                        strength=0.75
                    )
                )

        # 3. Associate detected database models
        for model in discovery.database_coupling.detected_models_or_tables:
            domain_name = self._infer_domain_from_name(model)
            if domain_name in candidate_map:
                candidate_map[domain_name]["entities"].append(model)
                candidate_map[domain_name]["tables"].append(model)
                candidate_map[domain_name]["evidences"].append(
                    DomainEvidence(
                        source_type=DomainEvidenceSource.DATABASE_TABLES,
                        file_or_symbol_path=model,
                        description=f"Modèle d'entité persistant '{model}' rattaché",
                        strength=0.7
                    )
                )

        # 4. If nothing was detected (small or flat repo), synthesize default domain hypothesis
        if not candidate_map:
            candidate_map["CoreDomain"] = {
                "evidences": [
                    DomainEvidence(
                        source_type=DomainEvidenceSource.SERVICE_CLASS,
                        file_or_symbol_path="root",
                        description="Codebase monolithique monolithique à domaine unique ou non découpé",
                        strength=0.5
                    )
                ],
                "entities": discovery.database_coupling.detected_models_or_tables,
                "endpoints": [c.relative_path for c in discovery.components if c.component_type == ComponentType.API_ROUTER],
                "files": [],
                "tables": discovery.database_coupling.detected_models_or_tables
            }

        # 5. Build BoundedContextHypothesis instances with coupling analysis
        hypotheses: List[BoundedContextHypothesis] = []
        for idx, (name, data) in enumerate(candidate_map.items(), 1):
            tables_count = len(data["tables"])
            # Evaluate coupling: high if many tables and shared access
            if tables_count > 4:
                coupling = CouplingLevel.TIGHT
                feasibility = 0.35
                coupling_notes = "Fort couplage persistant avec de multiples entités de données centrales."
            elif tables_count > 1:
                coupling = CouplingLevel.MODERATE
                feasibility = 0.65
                coupling_notes = "Couplage modéré avec la base relationnelle, extraction envisageable avec adaptateur."
            else:
                coupling = CouplingLevel.LOOSE
                feasibility = 0.90
                coupling_notes = "Faible couplage repéré. Excellent candidat pour un premier pas Strangler Fig."

            # Check if domain extraction is forbidden by user specifications
            is_forbidden = user_specs and any(fb.lower() == name.lower() for fb in user_specs.forbidden_extractions)
            if is_forbidden:
                feasibility = 0.05
                coupling = CouplingLevel.TIGHT
                coupling_notes = "Extraction en microservice formellement interdite par la spécification utilisateur."

            hypo = BoundedContextHypothesis(
                context_id=f"CTX-{idx:02d}-{name.upper()}",
                name=name,
                suggested_responsibility=f"Gestion des fonctionnalités et règles métier relatives à {name}",
                evidences=data["evidences"],
                identified_entities=data["entities"],
                identified_api_endpoints=data["endpoints"],
                coupling_level=coupling,
                coupling_notes=coupling_notes,
                shared_database_tables=data["tables"],
                user_confirmed=data.get("user_confirmed", None),
                user_feedback=None,
                extraction_feasibility_score=feasibility
            )
            hypotheses.append(hypo)

        # Sort by feasibility descending: lowest coupled first (Principle 4)
        hypotheses.sort(key=lambda h: h.extraction_feasibility_score, reverse=True)
        return hypotheses

    def _infer_domain_from_name(self, name: str) -> str:
        clean = re.sub(r'(Controller|Router|Service|Repository|Model|Route)$', '', name, flags=re.IGNORECASE)
        clean = clean.strip("_-")
        return clean.capitalize() if clean else "Core"
