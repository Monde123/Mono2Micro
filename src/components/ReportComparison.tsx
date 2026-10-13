import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { FileText, Copy, Check, Globe } from 'lucide-react';

export const ReportComparison: React.FC = () => {
  const { language, t } = useLanguage();
  const [activeReportTab, setActiveReportTab] = useState<'en' | 'fr'>('en');
  const [copied, setCopied] = useState(false);

  const reportFrSample = `# Rapport d'Évolution Architecturale — Mono2Micro
**Projet cible** : \`/workspace/ecommerce-app\`
**Généré le** : 2026-10-12 18:30:00 UTC
**Référence théorique** : [Convert Monolithic Application to Microservice Application](https://www.alphaxiv.org/abs/2306.08851) (Hatem Hammad et al., 2023)

## 1. Synthèse Exécutive
Audit architectural basé sur le papier de Hatem Hammad et al. (2023).
Option recommandée : MODULAR_MONOLITH.
Le monolithe modulaire résout l'objectif sans surcoût distribué (latence réseau, sagas, complexité d'exploitation).

**Recommandation retenue** : \`MODULAR_MONOLITH\`

## 2. Clarification des Objectifs Métier
- **Objectif principal** : CODEBASE_MODULARITY
- **Motivation utilisateur** : Amélioration de la lisibilité et autonomie de code
- **Résoluble au sein du monolithe ?** : OUI (Principe 1 du papier)

## 3. Découverte Empirique du Dépôt
- **Fichiers scannés** : 142 fichiers (~28,400 LOC)
- **Langages détectés** : TypeScript, SQL
- **Faits vérifiés** : 14 | **Hypothèses déduites** : 3

## 4. Analyse des Domaines Métier & Couplages
### Domaine : Notifications (Candidat pilote)
- **Couplage estimé** : \`LOOSE\` (Score faisabilité: 0.92)
### Domaine : Orders (Noyau transactionnel)
- **Couplage estimé** : \`TIGHT\` (Score faisabilité: 0.35)

## 5. Quality Gate et Vérifications
**Résultat global** : SUCCÈS (2/2 critères obligatoires validés sans moyenne)
- Critères totaux : 2 | Échecs critiques : 0`;

  const reportEnSample = `# Architectural Evolution Report — Mono2Micro
**Target Project** : \`/workspace/ecommerce-app\`
**Generated On** : 2026-10-12 18:30:00 UTC
**Theoretical Reference** : [Convert Monolithic Application to Microservice Application](https://www.alphaxiv.org/abs/2306.08851) (Hatem Hammad et al., 2023)

## 1. Executive Summary
Architectural modernisation audit based on research by Hatem Hammad et al. (2023).
Recommended strategy: MODULAR_MONOLITH.
Modular monolith satisfies the primary driver without paying the distributed system penalty (network latency, partial failures, distributed transactions).

**Selected Strategy** : \`MODULAR_MONOLITH\`

## 2. Business Objectives Clarification
- **Primary Goal** : CODEBASE_MODULARITY
- **User Rationale** : Code clarity and maintainability for small engineering team
- **Can be solved within monolith?** : YES (Research Principle 1)

## 3. Empirical Repository Discovery
- **Total Files Scanned** : 142 files (~28,400 LOC)
- **Detected Languages** : TypeScript, SQL
- **Verified Empirical Facts** : 14 | **Inferred Hypotheses** : 3

## 4. Business Domains & Coupling Analysis
### Domain : Notifications (Pilot Candidate)
- **Estimated Coupling** : \`LOOSE\` (Feasibility score: 0.92)
### Domain : Orders (Transactional Core)
- **Estimated Coupling** : \`TIGHT\` (Feasibility score: 0.35)

## 5. Quality Gate & Binary Verification
**Overall Result** : PASSED (2/2 mandatory criteria strictly validated)
- Total Criteria : 2 | Critical Failures : 0`;

  const activeContent = activeReportTab === 'en' ? reportEnSample : reportFrSample;

  const copyReport = () => {
    navigator.clipboard.writeText(activeContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="rapports" className="py-16 max-w-5xl mx-auto px-4 sm:px-6">
      <div className="mb-6 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-mono text-zinc-400 mb-2">
            <Globe className="w-3.5 h-3.5 text-zinc-400" />
            <span>{t.reports.badge}</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
            {t.reports.title}
          </h2>
          <p className="mt-1 text-sm text-zinc-400 max-w-2xl">
            {t.reports.subtitle}
          </p>
        </div>

        {/* Tab switch */}
        <div className="inline-flex p-1 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-medium">
          <button
            onClick={() => setActiveReportTab('en')}
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
              activeReportTab === 'en'
                ? 'bg-zinc-800 text-white shadow-sm'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            <span>English (report_en.md)</span>
          </button>
          <button
            onClick={() => setActiveReportTab('fr')}
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
              activeReportTab === 'fr'
                ? 'bg-zinc-800 text-white shadow-sm'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            <span>Français (report_fr.md)</span>
          </button>
        </div>
      </div>

      {/* Terminal / Markdown card preview */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden shadow-lg">
        {/* Header bar */}
        <div className="px-4 py-3 bg-zinc-950/80 border-b border-zinc-800 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
            <FileText className="w-3.5 h-3.5 text-zinc-500" />
            <span>.mono2micro/{activeReportTab === 'en' ? 'report_en.md' : 'report_fr.md'}</span>
            <span className="text-zinc-600 hidden sm:inline">· {activeReportTab === 'en' ? 'English export' : 'Version française'}</span>
          </div>
          <button
            onClick={copyReport}
            className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-emerald-400" />
                <span className="text-emerald-400">{language === 'fr' ? 'Copié !' : 'Copied!'}</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>{language === 'fr' ? 'Copier le Markdown' : 'Copy Markdown'}</span>
              </>
            )}
          </button>
        </div>

        {/* Content viewer */}
        <pre className="p-5 font-mono text-xs text-zinc-300 leading-relaxed overflow-x-auto max-h-96 select-text">
          {activeContent}
        </pre>
      </div>

      {/* Helper note */}
      <div className="mt-4 p-3.5 rounded-lg bg-zinc-900/30 border border-zinc-800/80 text-xs text-zinc-400 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <span>{t.reports.cliOptionNote}</span>
        <code className="text-[11px] font-mono text-zinc-300 bg-zinc-950 px-2 py-1 rounded border border-zinc-800 shrink-0">
          agent verify --lang {activeReportTab === 'en' ? 'en' : 'fr'}
        </code>
      </div>
    </section>
  );
};
