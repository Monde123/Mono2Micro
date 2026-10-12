# Rapport d'Évolution Architecturale — Plateforme Média "StreamPulse"

**Projet cible** : `/opt/apps/streampulse-core`  
**Généré le** : 2026-10-12 09:30:00 UTC  
**Référence théorique** : [Convert Monolithic Application to Microservice Application](https://www.alphaxiv.org/abs/2306.08851) (Hatem Hammad, Thaer Sahmoud et Abed Al Rahman Abu Ghazala, 2023)  

---

## 1. Synthèse Exécutive
**Recommandation Retenue : STRANGLER_MICROSERVICES (Extraction Progressive Strangler Fig)**

La plateforme subit des saturations CPU aiguës sur la conversion vidéo et l'envoi de flux push, alors que l'équipe compte 12 ingénieurs répartis en 3 squads. L'ensemble des prérequis (**Principe 1** : scalabilité ciblée et autonomie d'équipe ; **Principe 7** : suites de tests complètes CI/CD) sont réunis.
Conformément au **Principe 4 de Hammad et al. (2023)** (Composant le moins couplé en premier), le sous-domaine `NotificationTranscoder` est sélectionné comme premier service à extraire selon le patron Strangler Fig avec routage réversible.

---

## 2. Clarification des Objectifs Métier
- **Objectif principal** : `TARGETED_SCALABILITY` (Mise à l'échelle spécifique des traitements lourds)
- **Objectif secondaire** : `FAULT_ISOLATION` (Un crash d'encodage ne doit pas interrompre l'authentification ni la lecture)
- **Taille de l'équipe** : 12 développeurs
- **Résoluble au sein du monolithe ?** : **NON** (Les pics de charge d'encodage cannibalisent les ressources du serveur web)

---

## 3. Découverte Empirique du Dépôt (Lecture Seule)
- **Langages** : Python, TypeScript
- **Frameworks** : FastAPI, Celery, SQLAlchemy
- **Suites de test** : Pytest (420 tests unitaires et intégration)
- **CI/CD** : GitHub Actions (`.github/workflows/ci.yml`)
- **Modèles de données identifiés** : `User`, `Subscription`, `MediaAsset`, `TranscodeTask`, `PushNotification`

---

## 4. Analyse des Domaines Métier & Priorité d'Extraction
| Domaine Candidat | Couplage Estimé | Score Faisabilité | Priorité Strangler Fig |
| :--- | :--- | :--- | :--- |
| **NotificationService** | `LOOSE` | **0.92** | **Phase Pilote #1 (Extraction prioritaire)** |
| **TranscodingWorker** | `MODERATE` | **0.78** | **Phase #2 (File de messages asynchrone)** |
| **Subscriptions** | `TIGHT` | **0.40** | **Phase #3 (Scission de base de données)** |
| **IdentityCore** | `TIGHT` | **0.25** | **Maintenir au cœur du monolithe** |

---

## 5. Plan de Migration Strangler Fig — Étape Pilote 1
- **Service extrait** : `NotificationService`
- **Stratégie de routage** : `API_GATEWAY_REVERSE_PROXY` (Bascule progressive du trafic HTTP `/api/v1/notifications` vers le nouveau microservice)
- **Gestion des données** : `DATABASE_PER_SERVICE` avec double-écriture miroir temporaire (`dual write`)
- **Vérifications de sécurité** :
  - Parité stricte des statuts HTTP 200
  - Latence P95 < 80ms
  - Zéro accès direct à la base Postgres du monolithe depuis le conteneur extrait
- **Procédure de Rollback (Réversibilité)** :
  - Basculer la règle Envoy / Nginx vers l'IP interne du monolithe (délai : < 5 secondes)
  - Désactiver la file d'attente secondaire
  - Rétablir le mode mono-écriture

---

## 6. Avis de l'Avocat du Diable & Quality Gate
- **Contradiction** : L'avocat du diable a exigé un drill de coupure réseau inopiné (`TEST-ADV-ROLLBACK-02`).
- **Quality Gate** :
  - 100% des tests de contrat d'API validés (**PASSED**)
  - Aucune dérive de données constatée sur 10 000 notifications simulées (**PASSED**)
  - Zéro critère manquant ou moyenné.
