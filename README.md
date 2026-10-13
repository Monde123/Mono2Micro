# Mono_Micro — Agent IA Local de Modernisation Architecturale

> **CLI local pour évaluer, modulariser ou extraire des applications monolithiques par étapes progressives, testables et réversibles.**  
> Fondé sur les principes de recherche de :  
> **"Convert Monolithic Application to Microservice Application"**  
> *Hatem Hammad, Thaer Sahmoud et Abed Al Rahman Abu Ghazala (2023)* — [alphaXiv:2306.08851](https://www.alphaxiv.org/abs/2306.08851)

---

## 🎯 Philosophie & Démarche

Mono_Micro ne part **jamais** du principe que « monolithe = problème à découper ». L'agent :
- **Clarifie l'objectif** avant de recommander une architecture (Principe 1).
- Évalue en priorité le **Monolithe Modulaire** pour éviter la « taxe distribuée » (latence réseau, indisponibilités partielles, sagas complexes).
- Si une extraction est justifiée, applique le patron **Strangler Fig** avec routage réversible (Principe 5) et composant le moins couplé en premier (Principe 4).
- Traite rigoureusement la **propriété des données** (pas de scission magique aveugle) (Principe 6).
- Fait intervenir un **avocat du diable bloquant** et un **Quality Gate binaire sans moyenne** (Principe 7).

---

## 🚀 Installation & Exécution (Node.js & Python)

### Option A : Écosystème Node.js (Recommandé pour projets JavaScript / TypeScript)

```bash
# Exécution directe via npx (zéro installation préalable)
npx mono2micro analyze
npx mono2micro plan --goal CODEBASE_MODULARITY
npx mono2micro config

# Ou installation globale npm
npm install -g mono2micro
mono2micro analyze
```

### Option B : Écosystème Python (pip / pipx)

```bash
# Installation globale ou en environnement virtuel
pip install mono2micro-agent

# Ou en mode développement local depuis la racine
pip install -e agent_cli/

# Vérification
agent --help
```

---

## 🛠️ Les Commandes du CLI

| Commande | Rôle | Comportement & Sécurité |
| :--- | :--- | :--- |
| **`mono2micro analyze`** | **Découverte passive** | Lecture seule stricte. Inventorie sans exécuter aucun script du projet. Sépare faits vérifiés et hypothèses. |
| **`mono2micro plan`** | **Trajectoire & 4 Options** | Clarifie l'objectif, identifie les Bounded Contexts et compare : *Conserver*, *Monolithe Modulaire*, *Strangler Fig* ou *Reporter*. |
| **`mono2micro test-plan`** | **Avocat du Diable** | Sous-agent critique : recherche les couplages cachés, formule des objections et conçoit des tests indépendants. Bloque l'étape si des risques persistent. |
| **`mono2micro apply`** | **Implémentation contrôlée** | Applique l'étape approuvée sur branche Git dédiée (`mono2micro/step-X`). Requiert validation explicite (`OUI`). |
| **`mono2micro verify`** | **Quality Gate & Rapports** | Exécute les tests autorisés, valide les frontières et exporte les rapports bilingues (`--lang en` ou `--lang fr`). |
| **`mono2micro config`** | **Spécifications & Langue** | Gère les règles métier, domaines personnalisés, et configure la langue par défaut (`--lang en` / `--lang fr`). |

---

## ⚙️ Persistance & Spécifications Utilisateur

L'agent persiste son état et vos préférences dans le répertoire `.mono2micro/` (ajouté automatiquement à `.gitignore`) :

### Configuration via la commande `config`

```bash
# Définir un domaine métier explicite avec ses chemins
mono2micro config --set-domain "Billing=src/billing/**,src/payments/**"

# Interdire formellement l'extraction d'un module sensible
mono2micro config --forbid "LedgerCore"

# Définir la taille de l'équipe et l'architecture cible préférée
mono2micro config --team-size 3 --prefer MODULAR_MONOLITH

# Configurer la langue par défaut des rapports ('en' ou 'fr')
mono2micro config --lang en

# Ajouter une commande de test autorisée pour le Quality Gate
mono2micro config --add-test-cmd "npm run test:e2e"

# Ajuster la politique de confidentialité (FULL_CODE_REDACTED ou METADATA_ONLY)
mono2micro config --privacy METADATA_ONLY
```

### 🌍 Internationalisation & Génération de Rapports (EN / FR)

Le projet supporte nativement le bilinguisme complet :
1. **Rapports générés simultanément** : à chaque exécution de `verify`, l'agent produit :
   - `.mono2micro/report.md` : rapport dans la langue active (Français ou Anglais)
   - `.mono2micro/report_fr.md` : version française complète pour l'équipe locale
   - `.mono2micro/report_en.md` : version anglaise pour l'ingénierie internationale
   - `.mono2micro/report.json` : données brutes d'audit structurées et bilingues
2. **Choix à la volée** :
   ```bash
   # Exporter le rapport en anglais
   mono2micro verify --step 1 --lang en

   # Exporter le rapport en français
   mono2micro verify --step 1 --lang fr
   ```

### Structure de `.mono2micro/user_specifications.json`

Ce fichier est directement éditable :

```json
{
  "custom_domains": {
    "Billing": ["src/billing/**", "src/payments/**"],
    "Catalog": ["src/catalog/**"]
  },
  "forbidden_extractions": [
    "LedgerCore",
    "SecurityAuth"
  ],
  "preferred_architecture": "MODULAR_MONOLITH",
  "language": "en",
  "team_size": 3,
  "authorized_test_commands": [
    "npm test",
    "pytest"
  ],
  "privacy_level": "FULL_CODE_REDACTED",
  "business_rules_notes": "Le calcul de TVA doit rester synchrone avec le panier."
}
```

---

## 🔒 Sécurité & Confidentialité

- **100% Local** : Le CLI fonctionne exclusivement sur votre machine. Aucun code source, fichier ou rapport privé n'est téléversé vers un tiers ou vers la vitrine web.
- **Gestion des Clés API** : Vos clés (`OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.) résident uniquement dans vos variables d'environnement locales. Elles sont masquées automatiquement par regex dans les journaux.
- **Dépôt traité comme non fiable** : Pas d'exécution automatique de scripts arbitraires, validation stricte de confinement de chemins (`SafePathValidator`), et interdiction des écritures hors du périmètre approuvé.

---

## 🧪 Tests & Qualité

Pour lancer la suite de tests automatisés :

```bash
# Tests unitaires et d'intégration Python (33 tests)
pytest agent_cli/tests -v

# Vérification TypeScript de l'interface
npm run lint
npm run build
```

---

## 📊 Benchmark & Évaluation Comparative

Pour évaluer et benchmarker l'agent face à d'autres approches ou sur des applications de référence :

### 1. Jeux d'évaluation recommandés (Benchmarks de référence)
- **Monolithes open-source réels** :
  - Applications Node.js/Express/TypeScript (ex. Ghost core, Cal.com, Strapi modules)
  - Applications Python (ex. Django/FastAPI monoliths, Saleor core)
  - Applications Java/Spring Boot (ex. PetClinic monolithic vs microservice)
- **Métriques d'évaluation clés** :
  - **Précision de découverte passive** (0 exécution de code non approuvé, exhaustivité des routes et modèles)
  - **Couplage & Bounded Contexts** (taux de détection des couplages de base de données et tables partagées)
  - **Pertinence décisionnelle** (évitement de la taxe distribuée : l'agent préconise-t-il le Monolithe Modulaire quand les microservices sont contre-indiqués ?)
  - **Efficacité de l'avocat du diable** (détection proactive des points de défaillance réseau et régression)

### 2. Protocole de test de benchmark automatisé
```bash
# 1. Audit passif sans risque
mono2micro analyze --path ./benchmarks/target-app

# 2. Planification d'architecture et matrice
mono2micro plan --path ./benchmarks/target-app --goal FASTER_SCALING

# 3. Export des rapports comparatifs bilingues
mono2micro verify --path ./benchmarks/target-app --lang en
# Les rapports synthétisés sont disponibles dans .mono2micro/report_en.md et report_fr.md
```

---

## 📄 Licence & Conditions d'Utilisation

Ce projet est distribué sous **Licence Source-Available Non Commerciale** (voir [`LICENSE`](./LICENSE)) :

- **Usage autorisé sans frais** : Utilisation personnelle, académique, recherche scientifique, tests de benchmark et évaluation technique interne hors production.
- **Usage commercial restreint** : Toute utilisation commerciale, intégration en SaaS commercial, déploiement en production d'entreprise ou prestation de conseil facturée est **strictement interdite sauf accord écrit / convention bilatérale préalable** entre les parties.
- **Convention & Partenariats** : Pour établir une convention d'exploitation commerciale ou pour toute demande d'intégration d'entreprise :
  - Contact : `koudankomoise@gmail.com`

---

## 📚 Référence Académique

```bibtex
@article{hammad2023convert,
  title={Convert Monolithic Application to Microservice Application},
  author={Hammad, Hatem and Sahmoud, Thaer and Abu Ghazala, Abed Al Rahman},
  journal={alphaXiv preprint},
  eprint={2306.08851},
  url={https://www.alphaxiv.org/abs/2306.08851},
  year={2023}
}
```
