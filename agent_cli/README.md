# Mono2Micro Agent — Modernisation Raisonnée de Monolithes

> **Agent IA local en ligne de commande** pour faire évoluer des architectures logicielles monolithiques selon les principes empiriques du papier de recherche :  
> **"Convert Monolithic Application to Microservice Application"**  
> *Hatem Hammad, Thaer Sahmoud et Abed Al Rahman Abu Ghazala (2023)* — [alphaXiv:2306.08851](https://www.alphaxiv.org/abs/2306.08851)

---

## 🎯 Philosophie & Principes Directeurs

Cet outil n'a **pas** pour postulat que « monolithe = problème à découper ». Selon l'analyse du projet, la meilleure recommandation peut être de **conserver le monolithe**, de le **modulariser en interne (Modular Monolith)**, ou d'engager une **migration progressive par étapes (Strangler Fig)**.

L'agent opérationnalise les 7 principes centraux du papier de recherche :
1. **Clarification préalable des objectifs** : Ne jamais découper sans motivation technique ou d'affaires établie.
2. **Découpage par domaines métier (DDD)** : Frontières basées sur les *Bounded Contexts*, pas sur les couches techniques.
3. **Évolution incrémentale** : Proscrire la réécriture totale (anti-Big Bang).
4. **Composant le moins couplé en premier** : Réduire le risque en débutant par un service périphérique.
5. **Routage Strangler Fig réversible** : Dérivation graduelle du trafic via passerelle ou adaptateur.
6. **Propriété exclusive des données** : Pas de scission de base de données aveugle sans gestion de la cohérence.
7. **Quality Gate et réversibilité systématique** : Aucun passage sans tests indépendants et procédure de retour arrière vérifiée.

---

## 🔒 Confidentialité & Sécurité

- **Exécution 100% Locale** : L'agent tourne sur votre machine de travail et ne transmet aucun code à des tiers ou au site vitrine.
- **Gestion des Clés API** : Vos clés (`OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.) restent locales et ne sont jamais enregistrées dans le dépôt cible ni exposées dans les rapports.
- **Masquage Automatique des Secrets** : Détection et occultation des tokens, clés API et mots de passe dans les sorties et prompts.
- **Isolation Git & Approbation Humaine** : Aucune écriture n'est effectuée sans approbation explicite. Les changements sont appliqués sur des branches isolées (`mono2micro/step-X`).

---

## 🚀 Installation Rapide

```bash
# Depuis le répertoire agent_cli
pip install -e .

# Ou installation globale directe
pip install mono2micro-agent
```

Vérifiez l'installation :
```bash
agent --help
```

---

## 🛠️ Les 5 Commandes Officielles

### 1. `agent analyze` — Découverte en Lecture Seule
Scanne le dépôt, inventorie les composants, frameworks, modèles de données et suites de tests. Sépare strictement les **faits vérifiés** des **hypothèses** du modèle.
```bash
agent analyze --path .
```

### 2. `agent plan` — Objectifs & Trajectoire
Clarifie la motivation (scalabilité, autonomie, etc.), identifie les domaines métier candidats, compare les 4 options architecturales et génère un plan de migration progressif.
```bash
agent plan --path . --goal CODEBASE_MODULARITY --team-size 3
```

### 3. `agent test-plan` — L'Avocat du Diable
Le sous-agent contradicteur remet en question les hypothèses, détecte les dépendances croisées de données et conçoit des scénarios de test indépendants **avant** tout changement.
```bash
agent test-plan --path . --step 1
```

### 4. `agent apply` — Application Contrôlée
Applique une étape préalablement approuvée sur une branche Git dédiée. Requiert une confirmation formelle (`OUI`).
```bash
agent apply --path . --step 1 --confirm OUI
```

### 5. `agent verify` — Quality Gate Inflexible
Exécute les contrôles autorisés, vérifie l'absence d'accès direct à l'ancienne base et évalue le Quality Gate (tolérance zéro : aucun critère obligatoire en échec ne peut être moyenné).
```bash
agent verify --path . --step 1 --test-cmd "npm test"
```

---

## 📊 Artefacts Générés Localement

Toutes les sorties d'analyse sont stockées dans `.mono2micro/` (ajouté automatiquement à `.gitignore`) :
- `.mono2micro/discovery.json` : Données de l'analyse statique.
- `.mono2micro/strangler_plan.json` : Plan par étapes et stratégie de rollback.
- `.mono2micro/report.md` : Rapport complet prêt pour la revue d'architecture.
- `.mono2micro/report.json` : Rapport structuré.
