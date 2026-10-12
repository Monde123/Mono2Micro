import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface CommandStep {
  nodeCmd: string;
  pythonCmd: string;
  label: string;
  role: string;
  description: string;
  output: string;
}

export const CliTerminalDemo: React.FC = () => {
  const [activeTab, setActiveTab] = useState<number>(0);
  const [useNodeSyntax, setUseNodeSyntax] = useState<boolean>(true);
  const [copied, setCopied] = useState<boolean>(false);

  const steps: CommandStep[] = [
    {
      nodeCmd: 'npx mono2micro analyze --path .',
      pythonCmd: 'agent analyze --path .',
      label: '1. analyze',
      role: 'Lecture seule',
      description: 'Découverte statique passive sans exécuter de scripts.',
      output: `MONO2MICRO AGENT — Modernisation Raisonnée de Monolithes
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
│ ASM-ARCH-1 │ Monolithe centralisé à forte dépendance relationnelle (HIGH)`
    },
    {
      nodeCmd: 'npx mono2micro plan --goal CODEBASE_MODULARITY',
      pythonCmd: 'agent plan --goal CODEBASE_MODULARITY',
      label: '2. plan',
      role: 'Architecture',
      description: 'Clarification des objectifs, Bounded Contexts et comparaison des 4 options.',
      output: `Objectif analysé : CODEBASE_MODULARITY (Équipe: 3 devs)
ℹ️ Principe 1 : Résoluble au sein du monolithe (Monolithe Modulaire).

Analyse des Domaines (Principe 4 : Composant le moins couplé en premier)
│ #1 (Pilote) │ Notifications │ LOOSE    │ Score: 0.92 │ Candidat pilote
│ #2          │ Catalog       │ MODERATE │ Score: 0.70 │ Façade interne
│ #3          │ Orders        │ TIGHT    │ Score: 0.35 │ Conserver au cœur

Comparatif des 4 Options
│ Conserver le Monolithe   │ Rejeté
│ Monolithe Modulaire      │ ✓ RECOMMANDÉ (Optimal pour l'équipe)
│ Strangler Microservices  │ Non recommandé (surcoût prématuré)
│ Repousser la Migration   │ Non requis (tests existants)`
    },
    {
      nodeCmd: 'npx mono2micro test-plan --step 1',
      pythonCmd: 'agent test-plan --step 1',
      label: '3. test-plan',
      role: 'Avocat du diable',
      description: 'L\'avocat du diable cherche les couplages cachés et conçoit des tests.',
      output: `⚖️ Intervention de l'Avocat du Diable sur l'Étape 1...

Objections & Risques Détectés :
│ WARNING │ Couplage table NotificationLog │ Accédée par checkout.ts
│         │ Action requise                 │ Utiliser l'interface INotifier

Scénarios de Tests Indépendants Conçus Avant Implémentation :
│ TEST-ADV-01 │ Parité de réception sous 200 événements concurrents
│ TEST-ADV-02 │ Drill de coupure : Bascule automatique vers fallback sans erreur 5xx

✓ Étape validée avec réserves. Prêt pour approbation.`
    },
    {
      nodeCmd: 'npx mono2micro apply --step 1 --confirm OUI',
      pythonCmd: 'agent apply --step 1 --confirm OUI',
      label: '4. apply',
      role: 'Branche isolée',
      description: 'Application de l\'étape validée sur branche Git dédiée.',
      output: `⚠️ DEMANDE D'APPROBATION HUMAINE FORMELLE POUR L'ÉTAPE 1 :
Titre    : Modularisation interne de Notifications
Fichiers : src/notifications/service.ts, src/interfaces/notifier.ts
Rollback : git checkout main && git branch -D refactor/notifications-module

✓ Approbation accordée (Jeton: 4f9e1a8b2c)
✓ Branche isolée 'mono2micro/step-1-notifications' initialisée
✓ Fichiers appliqués strictement dans le périmètre autorisé`
    },
    {
      nodeCmd: 'npx mono2micro verify --step 1 --test-cmd "npm test"',
      pythonCmd: 'agent verify --step 1 --test-cmd "npm test"',
      label: '5. verify',
      role: 'Quality gate',
      description: 'Contrôles autorisés et barrière d\'étanchéité sans moyenne.',
      output: `🔍 Exécution des contrôles Quality Gate pour l'étape 1...

✓ QUALITY GATE VALIDÉ — PRÊT POUR LIVRAISON
Critères vérifiés: 2/2 | Échecs critiques: 0 | Non vérifiés: 0

Détail des Contrôles :
│ ✓ PASSED │ OUI │ ARCHITECTURAL_BOUNDARY │ Étanchéité vérifiée
│ ✓ PASSED │ OUI │ REGRESSION_TESTS       │ Suite Jest (86 tests passés en 2.4s)

✓ Rapport final exporté dans .mono2micro/report.md et report.json
🎉 Succès : L'étape peut être fusionnée après relecture de PR.`
    }
  ];

  const current = steps[activeTab];
  const activeCmd = useNodeSyntax ? current.nodeCmd : current.pythonCmd;

  const copyCurrentCmd = () => {
    navigator.clipboard.writeText(activeCmd);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="commandes" className="py-16 max-w-5xl mx-auto px-4 sm:px-6">
      
      <div className="mb-6 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
            Les 5 commandes d'exécution
          </h2>
          <p className="mt-1 text-sm text-zinc-400">
            Disponibles nativement via Node.js (<code className="text-zinc-300">npx</code>) ou Python (<code className="text-zinc-300">agent</code>).
          </p>
        </div>

        {/* Syntax switcher */}
        <div className="inline-flex p-0.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-mono">
          <button
            onClick={() => setUseNodeSyntax(true)}
            className={`px-2.5 py-1 rounded transition-colors ${
              useNodeSyntax ? 'bg-zinc-800 text-white font-semibold' : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            npx (Node)
          </button>
          <button
            onClick={() => setUseNodeSyntax(false)}
            className={`px-2.5 py-1 rounded transition-colors ${
              !useNodeSyntax ? 'bg-zinc-800 text-white font-semibold' : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            agent (Python)
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mb-3">
        {steps.map((st, i) => (
          <button
            key={st.label}
            onClick={() => setActiveTab(i)}
            className={`px-3 py-2 rounded-lg text-left text-xs font-mono transition-all border ${
              activeTab === i
                ? 'bg-zinc-800 border-zinc-600 text-white font-semibold'
                : 'bg-zinc-900/60 border-zinc-800/80 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
            }`}
          >
            <div className="truncate">{st.label}</div>
            <div className="text-[10px] text-zinc-500 truncate">{st.role}</div>
          </button>
        ))}
      </div>

      {/* Terminal View */}
      <div className="rounded-xl border border-zinc-800 bg-[#101114] overflow-hidden shadow-xl">
        
        {/* Terminal Header */}
        <div className="bg-zinc-900/80 px-4 py-2.5 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
            <span className="ml-2 font-mono text-xs text-zinc-400 hidden sm:inline">{current.description}</span>
          </div>
          <button
            onClick={copyCurrentCmd}
            className="flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-zinc-400" />}
            <span>Copier</span>
          </button>
        </div>

        {/* Command bar */}
        <div className="px-5 py-2.5 bg-zinc-900/30 border-b border-zinc-800/60 font-mono text-xs sm:text-sm text-zinc-200 flex items-center gap-2">
          <span className="text-zinc-500 select-none">$</span>
          <span>{activeCmd}</span>
        </div>

        {/* Output */}
        <div className="p-5 font-mono text-xs sm:text-sm text-zinc-300 whitespace-pre-wrap leading-relaxed overflow-x-auto">
          {current.output}
        </div>

      </div>

    </section>
  );
};
