import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type Language = 'fr' | 'en';

export interface Translations {
  nav: {
    approach: string;
    commands: string;
    installation: string;
    reports: string;
    security: string;
    copyPrompt: string;
  };
  hero: {
    paperCite: string;
    headline: string;
    subtitle: string;
    runtimeNode: string;
    runtimePython: string;
    tenetLocal: string;
    tenetAdversary: string;
    tenetGit: string;
  };
  principles: {
    badge: string;
    title: string;
    subtitle: string;
    c1Title: string;
    c1Desc: string;
    c1Ref: string;
    c2Title: string;
    c2Desc: string;
    c2Ref: string;
    c3Title: string;
    c3Desc: string;
    c3Ref: string;
  };
  cli: {
    title: string;
    subtitle: string;
    viewMode: string;
    switchLangNote: string;
    step1Label: string;
    step1Role: string;
    step1Desc: string;
    step2Label: string;
    step2Role: string;
    step2Desc: string;
    step3Label: string;
    step3Role: string;
    step3Desc: string;
    step4Label: string;
    step4Role: string;
    step4Desc: string;
    step5Label: string;
    step5Role: string;
    step5Desc: string;
    step6Label: string;
    step6Role: string;
    step6Desc: string;
  };
  reports: {
    badge: string;
    title: string;
    subtitle: string;
    frTab: string;
    enTab: string;
    frDesc: string;
    enDesc: string;
    cliOptionNote: string;
  };
  quickstart: {
    title: string;
    subtitle: string;
    nodeTab: string;
    pythonTab: string;
    nodeSteps: Array<{ title: string; cmd: string; note: string }>;
    pythonSteps: Array<{ title: string; cmd: string; note: string }>;
  };
  safety: {
    title: string;
    subtitle: string;
    s1Title: string;
    s1Desc: string;
    s2Title: string;
    s2Desc: string;
    s3Title: string;
    s3Desc: string;
  };
  footer: {
    tagline: string;
    academic: string;
    disclaimer: string;
  };
}

const translations: Record<Language, Translations> = {
  fr: {
    nav: {
      approach: 'Démarche',
      commands: 'Commandes',
      installation: 'Installation Node & Python',
      reports: 'Rapports EN / FR',
      security: 'Sécurité',
      copyPrompt: 'Copier la commande npx',
    },
    hero: {
      paperCite: 'Hatem Hammad et al. (2023)',
      headline: 'Modernisez vos monolithes avec discernement',
      subtitle:
        'Un agent local pour inspecter votre architecture en lecture seule, challenger les hypothèses et évaluer le Monolithe Modulaire avant toute extraction distribuée.',
      runtimeNode: 'Node.js (npx)',
      runtimePython: 'Python (CLI)',
      tenetLocal: '100% Local & Privé',
      tenetAdversary: 'Avocat du diable bloquant',
      tenetGit: 'Réversibilité Git garantie',
    },
    principles: {
      badge: 'FONDEMENTS DU PAPIER',
      title: 'La démarche méthodologique',
      subtitle: 'Les 3 piliers opérationnels issus de Hatem Hammad et al. (2023).',
      c1Title: "01. L'objectif avant l'architecture",
      c1Desc:
        "Découper n'est pas un but en soi. L'agent interroge vos motivations (charge ciblée, indépendance d'équipe ou simple lisibilité) et signale si le monolithe peut être conservé.",
      c1Ref: 'Hammad et al. (2023) § I & II',
      c2Title: '02. Priorité au Monolithe Modulaire',
      c2Desc:
        "L'agent évalue en priorité la modularisation interne. Vous bénéficiez de frontières DDD nettes sans subir la taxe distribuée (latence réseau, indisponibilités partielles, sagas).",
      c2Ref: 'Optimal pour équipes < 8 devs',
      c3Title: '03. Découpage progressif & Réversible',
      c3Desc:
        "Pattern Strangler Fig : le composant le moins couplé est isolé en premier. Chaque étape est testée indépendamment sur branche Git dédiée avec retour arrière immédiat.",
      c3Ref: 'Quality Gate binaire sans moyenne',
    },
    cli: {
      title: 'Les 5 Commandes Fondamentales',
      subtitle: "Un workflow en boucle fermée fondé sur l'expérimentation et le contradictoire.",
      viewMode: 'Syntaxe affichée :',
      switchLangNote: 'Sorties de terminal et rapports disponibles en Français et en Anglais.',
      step1Label: '1. analyze',
      step1Role: 'Lecture seule',
      step1Desc: 'Découverte statique passive sans exécuter de scripts ni modifier le projet.',
      step2Label: '2. plan',
      step2Role: 'Architecture',
      step2Desc: 'Clarification des objectifs, Bounded Contexts et comparaison des 4 options.',
      step3Label: '3. test-plan',
      step3Role: 'Avocat du diable',
      step3Desc: "L'avocat du diable cherche les couplages cachés et conçoit des tests indépendants.",
      step4Label: '4. apply',
      step4Role: 'Branche isolée',
      step4Desc: "Application de l'étape validée sur branche Git dédiée après approbation humaine formelle.",
      step5Label: '5. verify',
      step5Role: 'Quality gate',
      step5Desc: "Contrôles autorisés, étanchéité architecturale et génération des rapports FR et EN.",
      step6Label: '6. config',
      step6Role: 'Persistance',
      step6Desc: "Personnalisation des règles métier, taille d'équipe et langue par défaut (fr/en).",
    },
    reports: {
      badge: 'BILINGUISME & RAPPORTS',
      title: 'Rapports d’audit en Français ou en Anglais',
      subtitle:
        'Chaque audit génère simultanément le rapport dans votre langue choisie, ainsi que les versions report_fr.md et report_en.md.',
      frTab: 'Rapport en Français (report_fr.md)',
      enTab: 'English Report (report_en.md)',
      frDesc: 'Format structuré complet avec synthèse, faits empiriques, analyse DDD et principes Hammad 2023.',
      enDesc: 'International engineering format with Executive Summary, verified facts, DDD and research citations.',
      cliOptionNote:
        'Basculez à la volée avec --lang en ou persistez votre préférence avec agent config --lang en.',
    },
    quickstart: {
      title: 'Installation & Démarrage',
      subtitle: 'Choisissez votre environnement : exécution immédiate sans installation ou paquet CLI.',
      nodeTab: 'Node.js (npm / npx)',
      pythonTab: 'Python (pip / pipx)',
      nodeSteps: [
        {
          title: '1. Exécution directe (Zéro installation)',
          cmd: 'npx mono2micro analyze',
          note: "Télécharge et exécute temporairement l'agent sur le répertoire courant.",
        },
        {
          title: '2. Choisir la langue (Anglais ou Français)',
          cmd: 'npx mono2micro config --lang en',
          note: 'Configure la langue de génération des rapports et de travail.',
        },
        {
          title: "3. Clarifier l'objectif & Planifier",
          cmd: 'npx mono2micro plan --goal CODEBASE_MODULARITY',
          note: 'Compare les 4 options et évalue le Monolithe Modulaire.',
        },
      ],
      pythonSteps: [
        {
          title: '1. Installer via pip / pipx',
          cmd: 'pip install mono2micro-agent',
          note: 'Package Python autonome indépendant de votre projet cible.',
        },
        {
          title: '2. Lancer la découverte (Lecture Seule)',
          cmd: 'agent analyze --path .',
          note: 'Scanne le dépôt sans jamais exécuter les scripts du projet.',
        },
        {
          title: '3. Vérifier & exporter le rapport en anglais ou français',
          cmd: 'agent verify --step 1 --lang en',
          note: 'Génère report.md, report_en.md et report_fr.md dans .mono2micro/.',
        },
      ],
    },
    safety: {
      title: 'Garanties de sécurité',
      subtitle: 'Trois règles fondamentales pour préserver votre code et vos secrets.',
      s1Title: '100% Local & Étanche',
      s1Desc:
        'Le CLI tourne sur votre machine. Vos clés API restent dans votre environnement local. Ce site vitrine est purement informatif et ne reçoit aucun code.',
      s2Title: "L'Avocat du Diable Bloquant",
      s2Desc:
        "Avant toute modification, un sous-agent contradicteur recherche les couplages cachés. Il bloque l'étape si une table de base de données est partagée sans abstraction.",
      s3Title: 'Quality Gate sans Moyenne',
      s3Desc:
        'Le passage en production est strictement binaire. Aucun calcul de moyenne ne peut compenser un échec critique. Si un test obligatoire échoue, la livraison est rejetée.',
    },
    footer: {
      tagline: 'CLI d’ingénierie logicielle pour développeurs & architectes',
      academic:
        'Rendu opérationnel des principes de Hatem Hammad, Thaer Sahmoud et Abed Al Rahman Abu Ghazala (2023).',
      disclaimer: 'Site vitrine statique · Zéro transit de code ou de données privées',
    },
  },
  en: {
    nav: {
      approach: 'Approach',
      commands: 'Commands',
      installation: 'Installation Node & Python',
      reports: 'Reports EN / FR',
      security: 'Safety',
      copyPrompt: 'Copy npx command',
    },
    hero: {
      paperCite: 'Hatem Hammad et al. (2023)',
      headline: 'Modernize Monoliths with Grounded Rigor',
      subtitle:
        'A local engineering agent to inspect architecture in read-only mode, challenge hidden assumptions, and evaluate the Modular Monolith before any distributed microservice split.',
      runtimeNode: 'Node.js (npx)',
      runtimePython: 'Python (CLI)',
      tenetLocal: '100% Local & Private',
      tenetAdversary: "Blocking Devil's Advocate",
      tenetGit: 'Guaranteed Git Rollback',
    },
    principles: {
      badge: 'RESEARCH GROUNDING',
      title: 'Methodological Principles',
      subtitle: 'The 3 operational pillars from Hatem Hammad et al. (2023).',
      c1Title: '01. Purpose Before Architecture',
      c1Desc:
        'Splitting is never an end in itself. The agent interrogates your business drivers (targeted scale, team autonomy, or simple readability) and flags when the monolith should be kept.',
      c1Ref: 'Hammad et al. (2023) § I & II',
      c2Title: '02. Modular Monolith as First Priority',
      c2Desc:
        'The agent prioritizes internal modularization first. You gain clear Domain-Driven Design boundaries without paying the distributed tax (network latency, partial failures, distributed sagas).',
      c2Ref: 'Optimal for teams < 8 engineers',
      c3Title: '03. Progressive & Reversible Decomposition',
      c3Desc:
        'Strangler Fig pattern: the least coupled component is extracted first. Every step is tested on an isolated Git branch with an instant rollback procedure.',
      c3Ref: 'Binary non-negotiable Quality Gate',
    },
    cli: {
      title: 'The 5 Core Commands',
      subtitle: 'A closed-loop workflow grounded in empirical evidence and adversarial review.',
      viewMode: 'Syntax display:',
      switchLangNote: 'Terminal outputs and reports are fully available in English and French.',
      step1Label: '1. analyze',
      step1Role: 'Read-only',
      step1Desc: 'Passive static discovery without executing scripts or modifying the codebase.',
      step2Label: '2. plan',
      step2Role: 'Architecture',
      step2Desc: 'Objectives clarification, DDD bounded contexts, and 4-options comparison.',
      step3Label: '3. test-plan',
      step3Role: "Devil's advocate",
      step3Desc: "Devil's advocate exposes hidden couplings and designs independent tests.",
      step4Label: '4. apply',
      step4Role: 'Isolated branch',
      step4Desc: 'Controlled step application on a dedicated Git branch upon explicit human approval.',
      step5Label: '5. verify',
      step5Role: 'Quality gate',
      step5Desc: 'Authorized tests, architectural boundary verification, and bilingual report export.',
      step6Label: '6. config',
      step6Role: 'Persistence',
      step6Desc: 'Team size, custom domains, forbidden extractions, and default language (en/fr).',
    },
    reports: {
      badge: 'INTERNATIONALIZATION & REPORTS',
      title: 'Audit Reports in English or French',
      subtitle:
        'Every audit simultaneously generates the active report in your preferred language along with report_fr.md and report_en.md.',
      frTab: 'French Report (report_fr.md)',
      enTab: 'English Report (report_en.md)',
      frDesc: 'Complete structured audit with Executive Summary, verified facts, DDD, and Hammad 2023 principles.',
      enDesc: 'International engineering report with Executive Summary, verified facts, DDD domains, and research citations.',
      cliOptionNote:
        'Switch on the fly using --lang en / --lang fr or set permanently via agent config --lang en.',
    },
    quickstart: {
      title: 'Installation & Quickstart',
      subtitle: 'Choose your preferred runtime: zero-install npx or standalone Python CLI.',
      nodeTab: 'Node.js (npm / npx)',
      pythonTab: 'Python (pip / pipx)',
      nodeSteps: [
        {
          title: '1. Direct Execution (Zero install)',
          cmd: 'npx mono2micro analyze',
          note: 'Downloads and temporarily runs the agent on current directory.',
        },
        {
          title: '2. Configure Language (English / French)',
          cmd: 'npx mono2micro config --lang en',
          note: 'Sets default language for reports and team specifications.',
        },
        {
          title: '3. Clarify Goal & Plan Modernization',
          cmd: 'npx mono2micro plan --goal CODEBASE_MODULARITY',
          note: 'Compares all 4 options and evaluates Modular Monolith.',
        },
      ],
      pythonSteps: [
        {
          title: '1. Install via pip / pipx',
          cmd: 'pip install mono2micro-agent',
          note: 'Self-contained Python package independent of your target project.',
        },
        {
          title: '2. Run Discovery (Read-Only)',
          cmd: 'agent analyze --path .',
          note: 'Inspects repository without executing any project scripts.',
        },
        {
          title: '3. Verify & Export Reports in English or French',
          cmd: 'agent verify --step 1 --lang en',
          note: 'Generates report.md, report_en.md and report_fr.md in .mono2micro/.',
        },
      ],
    },
    safety: {
      title: 'Safety Guarantees',
      subtitle: 'Three golden rules preserving code integrity and developer trust.',
      s1Title: '100% Local & Isolated',
      s1Desc:
        'The CLI executes entirely on your machine. API credentials remain in your local environment. This web documentation site never receives any project code.',
      s2Title: "Blocking Devil's Advocate",
      s2Desc:
        'Before any code modification, an adversarial sub-agent uncovers hidden couplings and blocks the step if database tables are shared without encapsulation.',
      s3Title: 'Strict Binary Quality Gate',
      s3Desc:
        'Quality Gate validation is non-negotiable and strictly binary. No scoring average compensates for a critical failure. If a mandatory test fails, delivery is blocked.',
    },
    footer: {
      tagline: 'Software engineering CLI for developers & system architects',
      academic:
        'Operational implementation of principles by Hatem Hammad, Thaer Sahmoud, and Abed Al Rahman Abu Ghazala (2023).',
      disclaimer: 'Static documentation website · Zero telemetry, zero private data transfer',
    },
  },
};

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    try {
      const saved = localStorage.getItem('mono2micro_lang');
      if (saved === 'en' || saved === 'fr') return saved;
    } catch {}
    return 'fr'; // default to French, seamlessly switchable
  });

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    try {
      localStorage.setItem('mono2micro_lang', lang);
    } catch {}
  };

  const t = translations[language];

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return ctx;
};
