import React, { useState } from 'react';
import { Copy, Check, Terminal } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

interface CommandStep {
  nodeCmd: string;
  pythonCmd: string;
  label: string;
  role: string;
  description: string;
  outputFr: string;
  outputEn: string;
}

export const CliTerminalDemo: React.FC = () => {
  const { language, t } = useLanguage();
  const [activeTab, setActiveTab] = useState<number>(0);
  const [useNodeSyntax, setUseNodeSyntax] = useState<boolean>(true);
  const [copied, setCopied] = useState<boolean>(false);

  const steps: CommandStep[] = [
    {
      nodeCmd: 'npx mono2micro analyze --path .',
      pythonCmd: 'agent analyze --path .',
      label: t.cli.step1Label,
      role: t.cli.step1Role,
      description: t.cli.step1Desc,
      outputFr: `MONO2MICRO AGENT — Modernisation Raisonnée de Monolithes
Réf. alphaXiv:2306.08851 (Hatem Hammad et al., 2023)

1. Inventaire Factuel (Lecture Seule)
├── Répertoire   : /workspace/monolith-app
├── Fichiers     : 142 fichiers (28,400 LOC)
├── Stack        : TypeScript, Express.js, Prisma ORM
└── Tests        : Jest (86 tests détectés)

2. Faits Empiriques Vérifiés
│ FACT-PKG-1 │ Express.js (express@^4.21.2) déclaré dans package.json
│ FACT-DB-2  │ Entités Prisma détectées : User, Order, Product, Notification

3. Hypothèses Déduites (À confirmer par le développeur)
│ ASM-ARCH-1 │ Monolithe centralisé à forte dépendance relationnelle (HIGH)`,
      outputEn: `MONO2MICRO AGENT — Rigorous Monolith Modernisation
Ref. alphaXiv:2306.08851 (Hatem Hammad et al., 2023)

1. Factual Inventory (Read-Only)
├── Directory   : /workspace/monolith-app
├── Files       : 142 files (28,400 LOC)
├── Stack       : TypeScript, Express.js, Prisma ORM
└── Tests       : Jest (86 tests detected)

2. Verified Empirical Facts
│ FACT-PKG-1 │ Express.js (express@^4.21.2) declared in package.json
│ FACT-DB-2  │ Prisma entities detected : User, Order, Product, Notification

3. Inferred Model Hypotheses (To confirm with domain engineers)
│ ASM-ARCH-1 │ Centralised monolith with high relational coupling (HIGH)`
    },
    {
      nodeCmd: 'npx mono2micro plan --goal CODEBASE_MODULARITY',
      pythonCmd: 'agent plan --goal CODEBASE_MODULARITY',
      label: t.cli.step2Label,
      role: t.cli.step2Role,
      description: t.cli.step2Desc,
      outputFr: `Objectif analysé : CODEBASE_MODULARITY (Équipe: 3 devs)
ℹ️ Principe 1 : Résoluble au sein du monolithe (Monolithe Modulaire).

Analyse des Domaines (Principe 4 : Composant le moins couplé en premier)
│ #1 (Pilote) │ Notifications │ LOOSE    │ Score: 0.92 │ Candidat pilote
│ #2          │ Catalog       │ MODERATE │ Score: 0.70 │ Façade interne
│ #3          │ Orders        │ TIGHT    │ Score: 0.35 │ Conserver au cœur

Comparatif des 4 Options
│ Conserver le Monolithe   │ Rejeté
│ Monolithe Modulaire      │ ✓ RECOMMANDÉ (Optimal pour l'équipe)
│ Strangler Microservices  │ Non recommandé (surcoût prématuré)
│ Repousser la Migration   │ Non requis (tests existants)`,
      outputEn: `Analyzed Driver : CODEBASE_MODULARITY (Team size: 3 engineers)
ℹ️ Principle 1 : Solvable inside monolith (Modular Monolith).

Domain & Context Analysis (Principle 4 : Least coupled first)
│ #1 (Pilot)  │ Notifications │ LOOSE    │ Score: 0.92 │ Pilot candidate
│ #2          │ Catalog       │ MODERATE │ Score: 0.70 │ Internal facade
│ #3          │ Orders        │ TIGHT    │ Score: 0.35 │ Keep in core monolith

Comparison of the 4 Architectural Options
│ Keep Monolith            │ Rejected
│ Modular Monolith         │ ✓ RECOMMENDED (Optimal for team size)
│ Strangler Microservices  │ Not recommended (Premature overhead)
│ Postpone Migration       │ Not needed (Automated test suite present)`
    },
    {
      nodeCmd: 'npx mono2micro test-plan --step 1',
      pythonCmd: 'agent test-plan --step 1',
      label: t.cli.step3Label,
      role: t.cli.step3Role,
      description: t.cli.step3Desc,
      outputFr: `⚖️ Intervention de l'Avocat du Diable sur l'Étape 1...

Objections & Risques Détectés :
│ WARNING │ Couplage table NotificationLog │ Accédée par checkout.ts
│         │ Action requise                 │ Utiliser l'interface INotifier

Scénarios de Tests Indépendants Conçus Avant Implémentation :
│ TEST-ADV-01 │ Parité de réception sous 200 événements concurrents
│ TEST-ADV-02 │ Drill de coupure : Bascule automatique vers fallback sans erreur 5xx

✓ Étape validée avec réserves. Prêt pour approbation.`,
      outputEn: `⚖️ Devil's Advocate Adversarial Challenge on Step 1...

Uncovered Objections & Hidden Couplings :
│ WARNING │ Table NotificationLog coupling │ Directly queried by checkout.ts
│         │ Mandatory remediation          │ Route via INotifier interface

Independent Verification Scenarios Authored Before Code Edit :
│ TEST-ADV-01 │ Delivery parity under 200 concurrent burst events
│ TEST-ADV-02 │ Circuit-breaker drill: Graceful fallback without 5xx errors

✓ Step authorized with conditions. Ready for human sign-off.`
    },
    {
      nodeCmd: 'npx mono2micro apply --step 1 --confirm OUI',
      pythonCmd: 'agent apply --step 1 --confirm OUI',
      label: t.cli.step4Label,
      role: t.cli.step4Role,
      description: t.cli.step4Desc,
      outputFr: `⚠️ DEMANDE D'APPROBATION HUMAINE FORMELLE POUR L'ÉTAPE 1 :
Titre    : Modularisation interne de Notifications
Fichiers : src/notifications/service.ts, src/interfaces/notifier.ts
Rollback : git checkout main && git branch -D refactor/notifications-module

✓ Approbation accordée (Jeton: 4f9e1a8b2c)
✓ Branche isolée 'mono2micro/step-1-notifications' initialisée
✓ Fichiers appliqués strictement dans le périmètre autorisé`,
      outputEn: `⚠️ FORMAL HUMAN APPROVAL REQUIRED FOR STEP 1 :
Title    : Internal modularisation of Notifications
Scope    : src/notifications/service.ts, src/interfaces/notifier.ts
Rollback : git checkout main && git branch -D refactor/notifications-module

✓ Approval granted (Token: 4f9e1a8b2c)
✓ Isolated branch 'mono2micro/step-1-notifications' checked out
✓ Scope strictly bounded to declared interfaces`
    },
    {
      nodeCmd: 'npx mono2micro verify --step 1 --test-cmd "npm test" --lang en',
      pythonCmd: 'agent verify --step 1 --test-cmd "npm test" --lang en',
      label: t.cli.step5Label,
      role: t.cli.step5Role,
      description: t.cli.step5Desc,
      outputFr: `🔍 Exécution des contrôles Quality Gate pour l'étape 1...

✓ QUALITY GATE VALIDÉ — PRÊT POUR LIVRAISON
Critères vérifiés: 2/2 | Échecs critiques: 0 | Non vérifiés: 0

Détail des Contrôles :
│ ✓ PASSED │ OUI │ ARCHITECTURAL_BOUNDARY │ Étanchéité vérifiée sans fuite
│ ✓ PASSED │ OUI │ REGRESSION_TESTS       │ Suite Jest (86 tests passés en 2.4s)

✓ Rapports complets exportés (Langue active: Français) :
  • .mono2micro/report.md (Actif)
  • .mono2micro/report_fr.md (Version française)
  • .mono2micro/report_en.md (English version)
  • .mono2micro/report.json (Données brutes structurées)
🎉 Succès : L'étape peut être fusionnée après relecture de PR.`,
      outputEn: `🔍 Running Quality Gate checks for step 1...

✓ QUALITY GATE PASSED — READY FOR PULL REQUEST
Verified criteria: 2/2 | Critical failures: 0 | Unverified: 0

Evaluation Detail :
│ ✓ PASSED │ YES │ ARCHITECTURAL_BOUNDARY │ Strict boundary verified
│ ✓ PASSED │ YES │ REGRESSION_TESTS       │ Jest suite (86 tests passed in 2.4s)

✓ Comprehensive audit reports generated (Active language: English) :
  • .mono2micro/report.md (Active: English)
  • .mono2micro/report_en.md (English version)
  • .mono2micro/report_fr.md (French version)
  • .mono2micro/report.json (Structured data)
🎉 Success : Step cleared for merge upon PR review.`
    },
    {
      nodeCmd: 'npx mono2micro config --lang en --team-size 3',
      pythonCmd: 'agent config --lang en --team-size 3',
      label: t.cli.step6Label,
      role: t.cli.step6Role,
      description: t.cli.step6Desc,
      outputFr: `✓ Langue par défaut configurée : English (en)
✓ Taille d'équipe persistée : 3 développeur(s)
✓ Spécifications enregistrées dans .mono2micro/user_specifications.json

Spécificités Utilisateur Persistées :
├── Langue des rapports : English (en)
├── Taille de l'équipe  : 3 développeurs
└── Architecture préférée : Auto-évaluation par l'architecte`,
      outputEn: `✓ Default language persisted : English (en)
✓ Team size configured : 3 engineers
✓ Specifications saved to .mono2micro/user_specifications.json

Persisted Team Constraints & Preferences :
├── Report Language     : English (en)
├── Team Size           : 3 engineers
└── Architecture Choice : Evaluated by architect`
    }
  ];

  const current = steps[activeTab] || steps[0];
  const activeCmd = useNodeSyntax ? current.nodeCmd : current.pythonCmd;
  const terminalText = language === 'en' ? current.outputEn : current.outputFr;

  const copyCurrentCmd = () => {
    navigator.clipboard.writeText(activeCmd);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="commandes" className="py-16 max-w-5xl mx-auto px-4 sm:px-6">
      
      {/* Section Header */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
            {t.cli.title}
          </h2>
          <p className="mt-1 text-sm text-zinc-400">
            {t.cli.subtitle}
          </p>
        </div>

        {/* Syntax Selector */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="text-xs text-zinc-400">{t.cli.viewMode}</span>
          <div className="inline-flex p-1 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-medium">
            <button
              onClick={() => setUseNodeSyntax(true)}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                useNodeSyntax ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              npx mono2micro
            </button>
            <button
              onClick={() => setUseNodeSyntax(false)}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                !useNodeSyntax ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              agent
            </button>
          </div>
        </div>
      </div>

      {/* 5-Step Horizontal Tab List */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mb-4">
        {steps.map((st, idx) => (
          <button
            key={st.label}
            onClick={() => setActiveTab(idx)}
            className={`px-3 py-2.5 rounded-lg text-left transition-all border ${
              activeTab === idx
                ? 'bg-zinc-800/90 border-zinc-600 text-white shadow-sm'
                : 'bg-zinc-900/40 border-zinc-800/80 text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
            }`}
          >
            <div className="font-mono text-xs font-semibold">{st.label}</div>
            <div className="text-[10px] text-zinc-400 truncate mt-0.5">{st.role}</div>
          </button>
        ))}
      </div>

      {/* Terminal Display Box */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-950 shadow-2xl overflow-hidden">
        
        {/* Terminal Header */}
        <div className="px-4 py-3 bg-zinc-900/80 border-b border-zinc-800 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
              <div className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
              <div className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
            </div>
            <span className="text-xs font-mono text-zinc-400 ml-2 truncate">
              {current.description}
            </span>
          </div>

          <button
            onClick={copyCurrentCmd}
            className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white px-2.5 py-1 rounded bg-zinc-800/60 hover:bg-zinc-800 border border-zinc-700/60 transition-colors shrink-0"
            title="Copier la commande"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-mono text-[11px]">{language === 'fr' ? 'Copié' : 'Copied'}</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span className="font-mono text-[11px]">{language === 'fr' ? 'Copier' : 'Copy'}</span>
              </>
            )}
          </button>
        </div>

        {/* Command banner */}
        <div className="px-5 py-2.5 bg-zinc-900/30 border-b border-zinc-800/60 font-mono text-xs text-zinc-200 flex items-center gap-2">
          <span className="text-zinc-500 select-none">$</span>
          <span className="font-semibold text-zinc-100">{activeCmd}</span>
        </div>

        {/* Terminal Output */}
        <pre className="p-5 font-mono text-xs text-zinc-300 leading-relaxed overflow-x-auto whitespace-pre select-text max-h-[380px]">
          {terminalText}
        </pre>

      </div>

    </section>
  );
};
