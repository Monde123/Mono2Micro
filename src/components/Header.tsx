import React, { useState } from 'react';
import { ExternalLink, Copy, Check, Globe } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const Header: React.FC = () => {
  const { language, setLanguage, t } = useLanguage();
  const [copied, setCopied] = useState(false);

  const copyQuickNpx = () => {
    navigator.clipboard.writeText('npx mono2micro analyze');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <header className="sticky top-0 z-50 bg-[#141519]/90 backdrop-blur-md border-b border-zinc-800/80">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-6">
        
        {/* Zone 1: Wordmark */}
        <a href="/" className="text-base font-semibold tracking-tight text-white whitespace-nowrap shrink-0 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-zinc-400" />
          Mono_Micro
        </a>

        {/* Zone 2: Navigation links */}
        <nav className="hidden md:flex items-center gap-6 text-xs font-medium text-zinc-400">
          <a href="#demarche" className="hover:text-white transition-colors whitespace-nowrap shrink-0">{t.nav.approach}</a>
          <a href="#commandes" className="hover:text-white transition-colors whitespace-nowrap shrink-0">{t.nav.commands}</a>
          <a href="#rapports" className="hover:text-white transition-colors whitespace-nowrap shrink-0">{t.nav.reports}</a>
          <a href="#installation" className="hover:text-white transition-colors whitespace-nowrap shrink-0">{t.nav.installation}</a>
          <a href="#securite" className="hover:text-white transition-colors whitespace-nowrap shrink-0">{t.nav.security}</a>
        </nav>

        {/* Zone 3: Language Switcher & Actions */}
        <div className="flex items-center gap-3 shrink-0">
          
          {/* FR / EN Toggle Button */}
          <div className="inline-flex p-0.5 rounded-md bg-zinc-900 border border-zinc-800 text-xs font-mono">
            <button
              onClick={() => setLanguage('fr')}
              className={`px-2 py-1 rounded transition-colors ${
                language === 'fr'
                  ? 'bg-zinc-800 text-white font-semibold'
                  : 'text-zinc-500 hover:text-zinc-300'
              }`}
              title="Passer l'interface et les commandes en Français"
            >
              FR
            </button>
            <button
              onClick={() => setLanguage('en')}
              className={`px-2 py-1 rounded transition-colors ${
                language === 'en'
                  ? 'bg-zinc-800 text-white font-semibold'
                  : 'text-zinc-500 hover:text-zinc-300'
              }`}
              title="Switch interface and documentation to English"
            >
              EN
            </button>
          </div>

          <button
            onClick={copyQuickNpx}
            className="hidden sm:inline-flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-md bg-zinc-800/80 hover:bg-zinc-800 text-zinc-300 border border-zinc-700/60 transition-colors whitespace-nowrap shrink-0"
            title={t.nav.copyPrompt}
          >
            <span className="text-zinc-500">$</span>
            <span>npx mono2micro</span>
            {copied ? <Check className="w-3.5 h-3.5 text-zinc-200 ml-1" /> : <Copy className="w-3.5 h-3.5 text-zinc-500 ml-1" />}
          </button>
          
          <a
            href="https://www.alphaxiv.org/abs/2306.08851"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 font-medium transition-colors whitespace-nowrap shrink-0"
          >
            <span>alphaXiv (2023)</span>
            <ExternalLink className="w-3 h-3 text-zinc-700" />
          </a>
        </div>

      </div>
    </header>
  );
};
