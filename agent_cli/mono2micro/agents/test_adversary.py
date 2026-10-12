"""Test Adversary / Devil's Advocate Agent (Role 4).

Plays the critical counter-agent role.
Enforces Workflow Step 6:
- Challenges architectural assumptions and looks for hidden couplings.
- Prepares independent test cases BEFORE any implementation begins.
- Examines implementation steps for counterexamples.
- Blocks execution if requirements are ambiguous, evidence is lacking, or risks are unaddressed.
- Never invents business rules: asks clarifying questions or flags blockers instead.
"""

from typing import List, Optional
from mono2micro.models.discovery import DiscoveryReport
from mono2micro.models.plan import StranglerStep
from mono2micro.models.adversarial import (
    AdversarialReview,
    AdversarialObjection,
    ObjectionSeverity,
    HiddenCouplingRisk,
    IndependentTestCase,
)


class TestAdversaryAgent:
    """Agent challenging proposals, finding hidden couplings, and creating test scenarios."""

    def review_step_before_implementation(
        self,
        step: StranglerStep,
        discovery: DiscoveryReport
    ) -> AdversarialReview:
        """Independently analyze a proposed step and prepare adversarial counter-tests."""
        objections: List[AdversarialObjection] = []
        hidden_couplings: List[HiddenCouplingRisk] = []
        independent_tests: List[IndependentTestCase] = []
        ambiguities: List[str] = []
        blocking_reasons: List[str] = []

        # 1. Challenge data separation risk (Principle 6 of Hammad et al. 2023)
        if step.data_ownership.source_tables:
            for tbl in step.data_ownership.source_tables:
                # Check if this table is accessed elsewhere in the codebase
                accessing_files = discovery.database_coupling.cross_module_table_access.get(tbl, [])
                unscoped_accessors = [f for f in accessing_files if f not in step.files_in_scope]
                
                if unscoped_accessors:
                    hidden_couplings.append(HiddenCouplingRisk(
                        coupling_name=f"Accès concurrent non découplé à la table '{tbl}'",
                        module_a=step.target_bounded_context,
                        module_b=", ".join(unscoped_accessors[:3]),
                        coupling_mechanism="Requêtes SQL directes ou relations ORM traversant le périmètre d'extraction",
                        impact_if_separated="Erreur d'exécution 500 ou transaction cassée si la table est migrée sans adapter ces modules",
                        recommended_mitigation="Créer un adaptateur d'accès ou inclure ces modules dans la phase de test de contrat"
                    ))
                    objections.append(AdversarialObjection(
                        objection_id=f"OBJ-DATA-COUPLING-{tbl}",
                        severity=ObjectionSeverity.BLOCKING,
                        topic="Violation de frontière de données",
                        argument_fr=f"La table '{tbl}' est utilisée par des fichiers hors périmètre ({len(unscoped_accessors)} fichier(s)).",
                        evidence_or_counterexample=f"Fichiers appelants : {', '.join(unscoped_accessors[:2])}",
                        suggested_remedy="Adapter d'abord les appelants pour utiliser une interface/API avant de déplacer la table."
                    ))
                    blocking_reasons.append(f"Dépendance de données non résolue sur '{tbl}'")

        # 2. Challenge rollback feasibility (Principle 7 of Hammad et al. 2023)
        if not step.rollback.steps_fr or len(step.rollback.steps_fr) < 2:
            objections.append(AdversarialObjection(
                objection_id="OBJ-ROLLBACK-VAGUE",
                severity=ObjectionSeverity.BLOCKING,
                topic="Procédure de retour arrière imprécise",
                argument_fr="La procédure de rollback ne détaille pas la réconciliation des données en cas d'échec.",
                evidence_or_counterexample="Absence d'instructions de synchronisation inverse de la base.",
                suggested_remedy="Spécifier le script d'inversion des données ou le mode miroir."
            ))
            blocking_reasons.append("Procédure de retour arrière insuffisante")

        # 3. Check for lack of test harness
        if not discovery.test_frameworks_detected:
            objections.append(AdversarialObjection(
                objection_id="OBJ-NO-TESTS",
                severity=ObjectionSeverity.BLOCKING,
                topic="Absence de filet de sécurité de régression",
                argument_fr="Aucun framework de test n'est configuré sur le projet. Une extraction sans tests de régression est hautement risquée.",
                evidence_or_counterexample="Aucune configuration Jest/Pytest/Mocha détectée.",
                suggested_remedy="Rédiger d'abord des tests d'intégration bout-en-bout avant de toucher au code de production."
            ))
            blocking_reasons.append("Absence de tests de non-régression automatisés")

        # 4. Prepare independent test scenarios BEFORE implementation
        independent_tests.append(IndependentTestCase(
            case_id=f"TEST-ADV-REG-{step.step_number}-01",
            title=f"Vérification de parité des réponses HTTP ({step.target_bounded_context})",
            intent="Valider que les codes de statut HTTP et les payloads JSON sont strictement identiques via le nouveau chemin",
            preconditions=["Monolithe et service pilote en cours d'exécution", "Jeu de données de test chargé"],
            input_or_trigger=f"Requête GET sur les endpoints associés à {step.target_bounded_context}",
            expected_outcome="Codes HTTP 200, temps de réponse < 200ms, structures JSON conformes au schéma précédent",
            failure_symptom="Code 502 Bad Gateway ou champ manquant dans le payload",
            is_regression_test=True,
            is_contract_test=True
        ))

        independent_tests.append(IndependentTestCase(
            case_id=f"TEST-ADV-ROLLBACK-{step.step_number}-02",
            title="Validation de défaillance et bascule arrière (Fallback drill)",
            intent="Simuler une indisponibilité du service extrait et vérifier la reprise par le monolithe sans perte de session",
            preconditions=["Trafic routé à 50% vers le service extrait"],
            input_or_trigger="Arrêt forcé du conteneur du service extrait (SIGKILL)",
            expected_outcome="La passerelle redirige automatiquement vers le monolithe en < 500ms sans erreur 5xx exposée au client",
            failure_symptom="Client reçoit des erreurs de connexion ou timeout",
            is_regression_test=False,
            is_contract_test=False
        ))

        step_is_blocked = len(blocking_reasons) > 0
        summary = (
            f"L'étape {step.step_number} est BLOQUÉE : {len(blocking_reasons)} objection(s) critique(s) non résolue(s)."
            if step_is_blocked
            else f"L'étape {step.step_number} est validée avec {len(objections)} avertissement(s). Scénarios de tests indépendants prêts."
        )

        return AdversarialReview(
            target_step_number=step.step_number,
            step_is_blocked=step_is_blocked,
            blocking_reasons=blocking_reasons,
            objections=objections,
            hidden_coupling_risks=hidden_couplings,
            independent_test_cases=independent_tests,
            ambiguous_requirements=ambiguities,
            recommendation_summary_fr=summary
        )
