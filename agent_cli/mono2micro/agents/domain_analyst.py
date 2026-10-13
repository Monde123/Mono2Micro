"""Domain Analyst Agent (Role 2).

Identifies business boundaries and proposes candidate Bounded Contexts.
Grounded in Principle 2 of Hammad et al. (2023):
Decompose along domain boundaries (DDD) rather than technical horizontal tiers.
All domain proposals are hypotheses requiring user confirmation.
"""

import hashlib
import json
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
from mono2micro.core.security import SecretMasker
from mono2micro.llm import LLMClient, LLMError, extract_json

LLM_CONTEXTS_CACHE = "llm_contexts.json"
_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_ -]{0,39}$")
MAX_LLM_CONTEXTS = 12


class DomainAnalystAgent:
    """Agent in charge of bounded context identification and coupling evaluation."""

    def __init__(self, target_directory: str):
        self.target_directory = target_directory

    def analyze_domains(
        self,
        discovery: DiscoveryReport,
        user_specs: Optional[UserSpecifications] = None,
        llm: Optional[LLMClient] = None,
        cache=None,
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

        # 4b. Optional LLM refinement (cached for reproducibility across commands)
        self._merge_llm_contexts(candidate_map, discovery, user_specs, llm, cache)

        return self._build_hypotheses(candidate_map, user_specs)

    def _build_hypotheses(
        self,
        candidate_map: Dict[str, Dict],
        user_specs: Optional[UserSpecifications],
    ) -> List[BoundedContextHypothesis]:
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

    # ------------------------------------------------------------------ LLM

    def _llm_payload(self, discovery: DiscoveryReport, candidate_names: List[str],
                     user_specs: Optional[UserSpecifications]) -> Dict:
        """Metadata-only view of the repository (paths and names, never file contents)."""
        access = discovery.database_coupling.cross_module_table_access
        return {
            "languages": discovery.languages_detected,
            "frameworks": discovery.frameworks_detected,
            "components": [
                {"path": c.relative_path, "type": c.component_type.value}
                for c in discovery.components[:200]
            ],
            "data_models": discovery.database_coupling.detected_models_or_tables[:100],
            "model_access": {k: v[:10] for k, v in list(access.items())[:100]},
            "heuristic_candidates": sorted(candidate_names),
            "team_notes": SecretMasker.mask_text((user_specs.business_rules_notes or "")[:1000]) if user_specs else "",
        }

    def _merge_llm_contexts(self, candidate_map, discovery, user_specs, llm, cache) -> None:
        payload = self._llm_payload(discovery, list(candidate_map), user_specs)
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        key = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        contexts = None
        cached = cache.load_json(LLM_CONTEXTS_CACHE) if cache is not None else None
        if cached and cached.get("key") == key:
            contexts = cached.get("contexts", [])          # reproducible: no new call
        elif llm is not None:
            try:
                reply = llm.complete(self._LLM_SYSTEM, "Dépôt analysé (métadonnées) :\n" + SecretMasker.mask_text(raw))
                contexts = self._validate_llm_contexts(extract_json(reply), discovery)
                if cache is not None:
                    cache.save_json(LLM_CONTEXTS_CACHE, {"key": key, "contexts": contexts})
            except LLMError as exc:
                discovery.analysis_limitations.append(
                    f"Affinage LLM des domaines indisponible ({exc}) : heuristiques locales uniquement."
                )
                return
        if not contexts:
            return

        router_paths = {c.relative_path for c in discovery.components if c.component_type == ComponentType.API_ROUTER}
        existing = {name.lower(): name for name in candidate_map}
        for ctx in contexts:
            name = existing.get(ctx["name"].lower(), ctx["name"])
            entry = candidate_map.setdefault(name, {
                "evidences": [], "entities": [], "endpoints": [], "files": [], "tables": []
            })
            if candidate_map[name].get("user_confirmed"):
                continue  # explicit user domains are never overridden by the model
            for path in ctx["files"]:
                entry["evidences"].append(DomainEvidence(
                    source_type=DomainEvidenceSource.LLM_INFERENCE,
                    file_or_symbol_path=path,
                    description=f"Hypothèse du modèle : {ctx['rationale']}"[:300],
                    strength=0.55,
                ))
                if path not in entry["files"]:
                    entry["files"].append(path)
                if path in router_paths and path not in entry["endpoints"]:
                    entry["endpoints"].append(path)
            for table in ctx["tables"]:
                if table not in entry["tables"]:
                    entry["tables"].append(table)
                    entry["entities"].append(table)
                    entry["evidences"].append(DomainEvidence(
                        source_type=DomainEvidenceSource.LLM_INFERENCE,
                        file_or_symbol_path=table,
                        description=f"Hypothèse du modèle : {ctx['rationale']}"[:300],
                        strength=0.55,
                    ))

    _LLM_SYSTEM = (
        "Tu es un architecte logiciel expert en Domain-Driven Design. À partir des SEULES métadonnées "
        "fournies (chemins de fichiers, modèles de données, frameworks), propose des Bounded Contexts "
        "candidats. Règles strictes : n'invente aucune règle métier ; n'utilise que des chemins et des "
        "modèles présents dans les données ; si les preuves sont insuffisantes, renvoie une liste vide. "
        'Réponds UNIQUEMENT par un JSON : {"contexts":[{"name":str,"responsibility":str,'
        '"files":[chemins fournis],"tables":[modèles fournis],"rationale":str}]}.'
    )

    def _validate_llm_contexts(self, data, discovery: DiscoveryReport) -> List[Dict]:
        """Keep only grounded, well-formed contexts: model output is untrusted."""
        if not isinstance(data, dict) or not isinstance(data.get("contexts"), list):
            raise LLMError("Format de contextes inattendu dans la réponse du modèle.")
        known_files = {c.relative_path for c in discovery.components}
        known_models = set(discovery.database_coupling.detected_models_or_tables)
        clean: List[Dict] = []
        for item in data["contexts"][:MAX_LLM_CONTEXTS]:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            if not _NAME_RE.match(name):
                continue
            files = [f for f in item.get("files", []) if isinstance(f, str) and f in known_files]
            tables = [t for t in item.get("tables", []) if isinstance(t, str) and t in known_models]
            if not files and not tables:
                continue  # ungrounded proposal: discarded
            clean.append({
                "name": name[:1].upper() + name[1:],
                "files": files,
                "tables": tables,
                "rationale": str(item.get("rationale", ""))[:300],
            })
        return clean

    def _infer_domain_from_name(self, name: str) -> str:
        clean = re.sub(r'(Controller|Router|Service|Repository|Model|Route)$', '', name, flags=re.IGNORECASE)
        clean = clean.strip("_-")
        return clean.capitalize() if clean else "Core"
