# Rapport d'Évolution Architecturale — Monolithe E-Commerce "ShopCore"

**Projet cible** : `/var/apps/shopcore-monolith`  
**Généré le** : 2026-10-12 09:15:00 UTC  
**Référence théorique** : [Convert Monolithic Application to Microservice Application](https://www.alphaxiv.org/abs/2306.08851) (Hatem Hammad, Thaer Sahmoud et Abed Al Rahman Abu Ghazala, 2023)  

---

## 1. Synthèse Exécutive
**Recommandation Retenue : MODULAR_MONOLITH (Monolithe Modulaire)**

L'analyse démontre que l'équipe de développement comprend 3 ingénieurs et que l'objectif déclaré est la réduction de la dette technique et l'isolation des règles de facturation. Conformément au **Principe 1 de Hammad et al. (2023)** (Clarifier l'objectif avant de choisir une architecture), une scission en microservices distribués introduirait une complexité opérationnelle disproportionnée (latence réseau, cohérence éventuelle, déploiements multiples). La modularisation interne du monolithe répond à 100% des besoins sans imposer la taxe distribuée.

---

## 2. Clarification des Objectifs Métier
- **Objectif principal** : `CODEBASE_MODULARITY` (Modularisation du code et clarté des responsabilités)
- **Motivation de l'équipe** : "Les règles de calcul de TVA et de promotions se mélangent avec le panier et les commandes."
- **Taille de l'équipe** : 3 développeurs
- **Résoluble au sein du monolithe ?** : **OUI** (via frontières de modules et schémas logiques isolés)

---

## 3. Découverte Empirique du Dépôt (Lecture Seule)
- **Langages** : TypeScript (Node.js)
- **Frameworks** : Express.js, Prisma ORM
- **Fichiers scannés** : 184 fichiers (34 200 lignes de code)
- **Faits empiriques vérifiés** :
  - `[PACKAGE_DEPENDENCY]` Prisma ORM v5.4.0 (`package.json`)
  - `[ROUTE_DEFINITION]` Routes HTTP d'administration (`src/routes/admin.ts`)
  - `[ROUTE_DEFINITION]` Routes de paiement (`src/routes/checkout.ts`)
  - `[DATABASE_MIGRATION]` Modèles relationnels centraux (`User`, `Order`, `OrderItem`, `Product`, `TaxRate`)

---

## 4. Analyse des Domaines Métier & Couplages (DDD)
| Domaine Candidat | Couplage Estimé | Score Faisabilité | Tables Partagées | Recommandation |
| :--- | :--- | :--- | :--- | :--- |
| **TaxEngine** | `LOOSE` | 0.90 | `TaxRate` | Priorité 1 : Isolation modulaire immédiate |
| **Catalog** | `MODERATE` | 0.70 | `Product` | Priorité 2 : Interface interne de consultation |
| **OrdersCheckout** | `TIGHT` | 0.35 | `Order`, `OrderItem`, `User` | Maintenir dans le noyau transactionnel |

---

## 5. Comparaison des 4 Options Architecturales
| Option | Complexité | Surcoût Opérationnel | Verdict |
| :--- | :--- | :--- | :--- |
| **Conserver le Monolithe Tel Quel** | Faible | Minime | Rejeté : Ne résout pas le spaghetti fiscal |
| **Monolithe Modulaire (Modular Monolith)** | **Moyenne** | **Modéré** | **✓ RECOMMANDÉE** |
| **Extraction Microservices Strangler Fig** | Élevée | Important | Déconseillé : Équipe trop petite pour le multi-déploiement |
| **Repousser la Migration** | Faible | Minime | Non requis : Des tests de régression existent |

---

## 6. Revue Contradictoire de l'Avocat du Diable
- **Objection [WARNING]** : Attention à la table partagée `Order` : ne pas tenter d'accès direct depuis `TaxEngine`. L'accès doit obligatoirement transiter par l'interface `ITaxCalculationService`.
- **Scénarios de test préparés** :
  - `TEST-ADV-REG-01` : Vérification du calcul de TVA multi-pays sous 500 requêtes concurrentes.
  - `TEST-ADV-BOUNDARY-02` : Linter architectural confirmant l'absence d'import de `PrismaClient` dans le module `TaxEngine`.

---

## 7. Quality Gate et Procédure de Retour Arrière
- **Critères obligatoires** :
  - Étanchéité architecturale : **PASSED** (0 import illégal)
  - Suite de tests Jest : **PASSED** (142 tests passés en 4.2s)
  - Intégrité transactionnelle SQL : **PASSED**
- **Commande de Rollback** : `git checkout main && git branch -D refactor/tax-module` (Restauration en 30 secondes).
