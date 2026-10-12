"""Migration Architect Agent (Role 3).

Compares the 4 architectural options and generates a phased Strangler Fig roadmap.
Enforces Principles 1, 3, 4, 5, 6, 7 of Hammad et al. (2023):
- Never assume microservices are automatically desirable.
- Prioritize low-coupled components for early steps.
- Ensure explicit data ownership and verified rollback procedures.
"""

from typing import List, Optional
from mono2micro.models.discovery import DiscoveryReport
from mono2micro.models.objectives import MigrationObjectiveClarification, MigrationGoalType
from mono2micro.models.domains import BoundedContextHypothesis, CouplingLevel
from mono2micro.models.options import (
    ArchitectureOptionType,
    OptionEvaluation,
    OptionsComparisonMatrix,
)
from mono2micro.models.plan import (
    StranglerPlan,
    StranglerStep,
    RoutingStrategyType,
    DataSeparationStrategy,
    DataOwnershipPlan,
    RollbackProcedure,
)


class MigrationArchitectAgent:
    """Agent evaluating options and designing the progressive migration plan."""

    def compare_options(
        self,
        discovery: DiscoveryReport,
        objectives: MigrationObjectiveClarification,
        domains: List[BoundedContextHypothesis]
    ) -> OptionsComparisonMatrix:
        """Systematically evaluate the 4 architectural options."""
        evaluations: List[OptionEvaluation] = []

        has_tests = len(discovery.test_frameworks_detected) > 0
        tight_domains_count = sum(1 for d in domains if d.coupling_level == CouplingLevel.TIGHT)
        small_team = objectives.current_team_size <= 3

        # Option 1: KEEP_MONOLITH
        keep_suitability = 0.85 if small_team and objectives.primary_goal not in (
            MigrationGoalType.TARGETED_SCALABILITY, MigrationGoalType.TECH_DIVERSITY
        ) else 0.40
        evaluations.append(OptionEvaluation(
            option_type=ArchitectureOptionType.KEEP_MONOLITH,
            title="Conserver l'Architecture Actuelle",
            summary="Maintenir le monolithe existant en concentrant les efforts sur l'optimisation des performances et l'outillage de test.",
            expected_benefits=[
                "Zéro surcoût de réseau ou d'orchestration distribuée",
                "Transactions ACID locales garanties",
                "Simplicité maximale de débogage et de déploiement en équipe restreinte"
            ],
            implementation_costs=["Nul à très faible"],
            operational_risks=["Goulots d'étranglement persistants si la charge explose sur un composant spécifique"],
            prerequisites=["Maintien de la discipline de code"],
            uncertainties=["Plafond de scalabilité verticale"],
            complexity_rating="FAIBLE",
            operational_overhead="MINIME",
            suitability_score=keep_suitability,
            is_recommended=False,
            recommendation_rationale="Option pragmatique si la charge et la taille de l'équipe ne justifient pas de complexité distribuée."
        ))

        # Option 2: MODULAR_MONOLITH
        modular_suitability = 0.90 if (small_team or tight_domains_count > 0 or not has_tests) else 0.65
        evaluations.append(OptionEvaluation(
            option_type=ArchitectureOptionType.MODULAR_MONOLITH,
            title="Modulariser le Monolithe (Modular Monolith)",
            summary="Établir des frontières de modules strictes et des schémas de données isolés au sein du même exécutable ou conteneur.",
            expected_benefits=[
                "Clarté des domaines métier sans payer la 'taxe distribuée' (latence réseau, sérialisation)",
                "Préparation optimale à une future extraction si les besoins évoluent",
                "Déploiements et tests rapides en local"
            ],
            implementation_costs=["Refactorisation interne des dépendances et interfaces d'appels"],
            operational_risks=["Risque de contournement des frontières si les linters architecturaux ne sont pas stricts"],
            prerequisites=["Définition claire des interfaces entre modules"],
            uncertainties=["Adhésion des développeurs à la discipline modulaire"],
            complexity_rating="MOYENNE",
            operational_overhead="MODÉRÉ",
            suitability_score=modular_suitability,
            is_recommended=False,
            recommendation_rationale="Offre les bénéfices d'organisation du code sans les défaillances réseau des microservices."
        ))

        # Option 3: STRANGLER_MICROSERVICES
        strangler_suitability = 0.85 if (not small_team and has_tests and len(domains) >= 2) else 0.50
        evaluations.append(OptionEvaluation(
            option_type=ArchitectureOptionType.STRANGLER_MICROSERVICES,
            title="Extraction Progressive en Microservices (Strangler Fig)",
            summary="Extraire graduellement les services candidats en commençant par le domaine le plus faiblement couplé, avec routage réversible.",
            expected_benefits=[
                "Autonomie complète de déploiement et de mise à l'échelle sur les services extraits",
                "Isolation des pannes (la défaillance d'un service n'arrête pas le monolithe)",
                "Possibilité d'adopter des stacks technologiques spécialisées"
            ],
            implementation_costs=[
                "Mise en place d'une passerelle (API Gateway)",
                "Gestion de la cohérence éventuelle des données et des pannes réseau",
                "Observabilité distribuée (Distributed Tracing, métriques)"
            ],
            operational_risks=[
                "Complexité opérationnelle élevée (Kubernetes, CI/CD multiples)",
                "Transactions distribuées complexes si la scission de base de données est précipitée"
            ],
            prerequisites=["Suite de tests de régression fiable", "Observabilité et pipelines CI/CD automatisés"],
            uncertainties=["Latence réseau inter-services"],
            complexity_rating="ÉLEVÉE",
            operational_overhead="IMPORTANT",
            suitability_score=strangler_suitability,
            is_recommended=False,
            recommendation_rationale="Adapté si l'équipe a besoin d'indépendance de livraison et que les prérequis de tests sont remplis."
        ))

        # Option 4: POSTPONE_MIGRATION
        postpone_suitability = 0.95 if (not has_tests and tight_domains_count > 2) else 0.30
        evaluations.append(OptionEvaluation(
            option_type=ArchitectureOptionType.POSTPONE_MIGRATION,
            title="Repousser la Migration (Dette Technique Préalable)",
            summary="Différer toute extraction architecturale jusqu'à ce que la suite de tests automatisés et l'observabilité minimale soient en place.",
            expected_benefits=[
                "Évite un échec critique de migration en aveugle",
                "Permet de solidifier les contrats métier avant de découper"
            ],
            implementation_costs=["Rédaction de tests et métriques d'observabilité"],
            operational_risks=["Prolongation temporaire des lenteurs de livraison existantes"],
            prerequisites=["Création d'un harnais de tests de non-régression"],
            uncertainties=["Délai d'atteinte de la maturité de test"],
            complexity_rating="FAIBLE",
            operational_overhead="MINIME",
            suitability_score=postpone_suitability,
            is_recommended=False,
            recommendation_rationale="Recommandé impérativement si le monolithe ne dispose pas de tests suffisants pour valider la non-régression."
        ))

        # Determine best recommendation
        # If no tests and highly coupled, recommend POSTPONE or MODULAR_MONOLITH
        if not has_tests:
            recommended = ArchitectureOptionType.POSTPONE_MIGRATION if tight_domains_count > 1 else ArchitectureOptionType.MODULAR_MONOLITH
            synth = (
                "Absence de suite de tests automatisés robuste détectée. Découper vers des microservices maintenant violerait "
                "le Principe 7 de Hammad et al. (2023) (Vérification et Réversibilité). Nous recommandons de solidifier les tests "
                "ou d'adopter d'abord un Monolithe Modulaire."
            )
        elif small_team and objectives.primary_goal not in (MigrationGoalType.TARGETED_SCALABILITY, MigrationGoalType.TECH_DIVERSITY):
            recommended = ArchitectureOptionType.MODULAR_MONOLITH
            synth = (
                "Taille d'équipe restreinte et objectifs de modularité : le Monolithe Modulaire répond aux besoins sans infliger "
                "la complexité d'exploitation des systèmes distribués."
            )
        else:
            recommended = ArchitectureOptionType.STRANGLER_MICROSERVICES
            synth = (
                "Prérequis techniques réunis. Une migration progressive selon le patron Strangler Fig (Hammad et al., 2023) "
                "peut être initiée sur le sous-domaine le moins couplé."
            )

        for opt in evaluations:
            if opt.option_type == recommended:
                opt.is_recommended = True

        return OptionsComparisonMatrix(
            evaluations=evaluations,
            recommended_option=recommended,
            synthesis_fr=synth,
            key_tradeoffs=[
                "Complexité opérationnelle vs Autonomie de livraison",
                "Cohérence forte ACID vs Cohérence éventuelle distribuée",
                "Refactorisation interne in-process vs Services réseau indépendants"
            ]
        )

    def build_strangler_plan(
        self,
        domains: List[BoundedContextHypothesis],
        option: ArchitectureOptionType
    ) -> StranglerPlan:
        """Create verifiable, sequential, reversible steps starting with low coupling."""
        steps: List[StranglerStep] = []

        # Find best candidate: lowest coupling first (Principle 4)
        candidates = sorted(domains, key=lambda d: d.extraction_feasibility_score, reverse=True)

        if option == ArchitectureOptionType.MODULAR_MONOLITH:
            # Build modularization steps
            for idx, domain in enumerate(candidates, 1):
                steps.append(StranglerStep(
                    step_number=idx,
                    title=f"Modularisation interne du domaine {domain.name}",
                    description=f"Isoler les dépendances de {domain.name} derrière une interface interne stricte sans extraction réseau.",
                    target_bounded_context=domain.name,
                    files_in_scope=[e.file_or_symbol_path for e in domain.evidences if "/" in e.file_or_symbol_path],
                    routing_strategy=RoutingStrategyType.IN_PROCESS_ADAPTER,
                    routing_details=f"Façade de module interne pour {domain.name}",
                    data_ownership=DataOwnershipPlan(
                        strategy=DataSeparationStrategy.LOGICAL_SCHEMA_SPLIT,
                        source_tables=domain.shared_database_tables,
                        target_tables=domain.shared_database_tables,
                        consistency_model="ACID local au sein de la base unifiée",
                        data_rollback_strategy="Annulation du commit de refactoring de schéma"
                    ),
                    success_criteria=[
                        f"Aucun import direct non autorisé vers {domain.name}",
                        "100% des tests de régression unitaires au vert"
                    ],
                    rollback=RollbackProcedure(
                        steps_fr=[
                            "Rétablir l'interface monolithique précédente",
                            "Annuler la branche de refactoring"
                        ],
                        git_revert_command=f"git checkout main && git branch -D refactor/{domain.name.lower()}-module",
                        routing_fallback_action="Appels directs restaurés",
                        data_revert_action="Aucune scission de base à annuler",
                        estimated_time_to_recover_minutes=2
                    )
                ))
        else:
            # Microservices extraction steps
            for idx, domain in enumerate(candidates, 1):
                is_first = (idx == 1)
                steps.append(StranglerStep(
                    step_number=idx,
                    title=f"{'Phase Pilote : ' if is_first else ''}Extraction du service {domain.name}",
                    description=(
                        f"Découpage progressif de {domain.name} en microservice indépendant "
                        f"selon la méthode Strangler Fig (Hammad et al. 2023)."
                    ),
                    target_bounded_context=domain.name,
                    files_in_scope=[e.file_or_symbol_path for e in domain.evidences if "/" in e.file_or_symbol_path],
                    routing_strategy=RoutingStrategyType.API_GATEWAY_REVERSE_PROXY,
                    routing_details=f"Interception du trafic HTTP pour {domain.name} par la passerelle de routage",
                    data_ownership=DataOwnershipPlan(
                        strategy=DataSeparationStrategy.DATABASE_PER_SERVICE,
                        source_tables=domain.shared_database_tables,
                        target_tables=[f"{t}_extracted" for t in domain.shared_database_tables],
                        foreign_keys_handled=[f"Remplacement des FKs vers {t} par des identifiants logiques" for t in domain.shared_database_tables],
                        consistency_model="Cohérence éventuelle avec double-écriture temporaire",
                        dual_write_required=True,
                        data_rollback_strategy="Conservation du flux d'écriture miroir vers le monolithe jusqu'à coupure finale"
                    ),
                    success_criteria=[
                        f"Taux d'erreur HTTP < 0.05% sur les routes {domain.name}",
                        "Parité stricte des données vérifiée entre ancien et nouveau stockage",
                        "Temps de réponse P95 équivalent ou supérieur"
                    ],
                    rollback=RollbackProcedure(
                        steps_fr=[
                            f"Basculer la passerelle pour rediriger 100% du trafic {domain.name} vers le monolithe",
                            "Désactiver le service extrait",
                            "Arrêter la réplication de données"
                        ],
                        git_revert_command="git revert HEAD",
                        routing_fallback_action="Rétablissement immédiat de la route monolithe sur le reverse proxy",
                        data_revert_action="Réactivation de la source de vérité monolithe sans perte",
                        estimated_time_to_recover_minutes=5,
                        tested_in_sandbox=False
                    ),
                    is_destructive=False,
                    is_data_migration=len(domain.shared_database_tables) > 0
                ))

        return StranglerPlan(
            plan_id="PLAN-STRANGLER-001",
            target_architecture_summary=f"Trajectoire progressive {option.value} en {len(steps)} étapes séquentielles et réversibles.",
            steps=steps,
            estimated_total_steps=len(steps),
            prerequisites_met=True,
            principles_applied=[
                "Principe 3 : Évolution progressive plutôt que réécriture Big Bang",
                "Principe 4 : Composant le moins couplé en premier",
                "Principe 5 : Routage Strangler Fig réversible",
                "Principe 6 : Propriété exclusive des données et double-écriture temporaire",
                "Principe 7 : Procédure de retour arrière explicite par étape"
            ]
        )
