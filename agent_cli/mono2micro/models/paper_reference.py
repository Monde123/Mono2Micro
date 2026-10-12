"""Paper reference data and citations.

Grounding reference:
Hatem Hammad, Thaer Sahmoud and Abed Al Rahman Abu Ghazala (2023).
"Convert Monolithic Application to Microservice Application".
alphaXiv: https://www.alphaxiv.org/abs/2306.08851
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class PaperPrincipleId(str, Enum):
    CLARIFY_OBJECTIVES = "PRINCIPLE_1_CLARIFY_OBJECTIVES"
    DOMAIN_ANALYSIS = "PRINCIPLE_2_DOMAIN_ANALYSIS"
    INCREMENTAL_EVOLUTION = "PRINCIPLE_3_INCREMENTAL_EVOLUTION"
    LOW_COUPLING_FIRST = "PRINCIPLE_4_LOW_COUPLING_FIRST"
    STRANGLER_FIG_ROUTING = "PRINCIPLE_5_STRANGLER_FIG_ROUTING"
    DATA_SEPARATION_OWNERSHIP = "PRINCIPLE_6_DATA_SEPARATION_OWNERSHIP"
    CONTINUOUS_TESTING_ROLLBACK = "PRINCIPLE_7_CONTINUOUS_TESTING_ROLLBACK"


class PaperPrincipleCitation(BaseModel):
    """Citation linking a recommendation to the academic paper principles."""
    principle_id: PaperPrincipleId
    principle_name: str
    paper_section: str
    paper_page: Optional[int] = None
    summary_fr: str
    applicability_guideline: str
    caveat_fr: str


PAPER_PRINCIPLES: dict[PaperPrincipleId, PaperPrincipleCitation] = {
    PaperPrincipleId.CLARIFY_OBJECTIVES: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.CLARIFY_OBJECTIVES,
        principle_name="Clarification des objectifs avant tout choix architectural",
        paper_section="Section I & Section II: Background & Motivation",
        paper_page=1,
        summary_fr="Ne jamais découper un monolithe sans objectif d'affaires ou d'exploitation clairement identifié (scalabilité ciblée, indépendance d'équipe, cadence de livraison).",
        applicability_guideline="Si l'objectif peut être satisfait au sein du monolithe (ex: scaling vertical, mise en cache, modularisation interne), privilégier la solution la plus simple.",
        caveat_fr="Le papier ne préconise pas les microservices comme une fin en soi."
    ),
    PaperPrincipleId.DOMAIN_ANALYSIS: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.DOMAIN_ANALYSIS,
        principle_name="Analyse du domaine et contextes délimités (DDD)",
        paper_section="Section III: Domain-Driven Design and Decomposition",
        paper_page=3,
        summary_fr="Découper selon les frontières du domaine métier (Bounded Contexts) plutôt que selon des couches techniques horizontales.",
        applicability_guideline="Les frontières déduites du code sont des hypothèses qui doivent être vérifiées avec les experts métier.",
        caveat_fr="Ne pas inventer de règles métier absentes du code source."
    ),
    PaperPrincipleId.INCREMENTAL_EVOLUTION: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.INCREMENTAL_EVOLUTION,
        principle_name="Évolution progressive vs Grand Soir (Big Bang)",
        paper_section="Section IV: Migration Strategies and Phasing",
        paper_page=4,
        summary_fr="Proscrire la réécriture complète de l'application. Faire cohabiter l'ancien et le nouveau système pas à pas.",
        applicability_guideline="Chaque étape doit être petite, autonome, livrable en production et vérifiable indépendamment.",
        caveat_fr="Une migration Big Bang comporte un risque d'échec critique disproportionné."
    ),
    PaperPrincipleId.LOW_COUPLING_FIRST: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.LOW_COUPLING_FIRST,
        principle_name="Commencer par un composant faiblement couplé",
        paper_section="Section IV.B: Service Selection for Early Extraction",
        paper_page=5,
        summary_fr="Extraire en priorité un sous-domaine périphérique présentant peu de dépendances vers la base centrale et le reste du code.",
        applicability_guideline="Utiliser le premier service extrait pour roder les pipelines CI/CD, l'observabilité et les mécanismes réseau.",
        caveat_fr="Ne pas s'attaquer au cœur transactionnel ou aux entités partagées lors de la première étape."
    ),
    PaperPrincipleId.STRANGLER_FIG_ROUTING: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.STRANGLER_FIG_ROUTING,
        principle_name="Routage progressif de type Strangler Fig",
        paper_section="Section V: The Strangler Application Pattern",
        paper_page=6,
        summary_fr="Intercaler une passerelle ou un composant de routage pour basculer graduellement le trafic des endpoints du monolithe vers le nouveau service.",
        applicability_guideline="Permet le basculement progressif (canary, feature flags, routage par URL) et la détection précoce d'anomalies.",
        caveat_fr="Nécessite la gestion des sessions utilisateur et la cohérence des requêtes distribuées."
    ),
    PaperPrincipleId.DATA_SEPARATION_OWNERSHIP: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.DATA_SEPARATION_OWNERSHIP,
        principle_name="Propriété exclusive et scission des données",
        paper_section="Section VI: Database Decomposition & Data Consistency",
        paper_page=7,
        summary_fr="Un microservice doit posséder sa base de données propre. Aucun accès direct inter-services à la base de données.",
        applicability_guideline="Traiter explicitement la scission des tables, les clés étrangères partagées, et substituer les transactions ACID locales par des événements ou patterns de sagas si nécessaire.",
        caveat_fr="La séparation des données n'est JAMAIS une opération automatique : elle requiert une validation rigoureuse de la cohérence éventuelle."
    ),
    PaperPrincipleId.CONTINUOUS_TESTING_ROLLBACK: PaperPrincipleCitation(
        principle_id=PaperPrincipleId.CONTINUOUS_TESTING_ROLLBACK,
        principle_name="Tests indépendants, Quality Gate et réversibilité systématique",
        paper_section="Section VII: Testing, Verification and Fallback Mechanisms",
        paper_page=8,
        summary_fr="Chaque étape de migration doit comporter des tests de régression, de contrat d'API, et une procédure documentée et testée de retour arrière.",
        applicability_guideline="Le Quality Gate doit bloquer tout passage en production si un critère obligatoire échoue. Interdiction de moyenner les résultats.",
        caveat_fr="Si le retour arrière n'est pas garanti, l'étape ne doit pas être approuvée."
    ),
}
