import React, { useState } from 'react';
import { ExternalLink, Copy, Check } from 'lucide-react';

export const Header: React.FC = () => {
  const [copied, setCopied] = useState(false);

  const copyQuickNpx = () => {
    navigator.clipboard.writeText('npx mono2micro analyze');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <header className="sticky top-0 z-50 bg-[#141519]/90 backdrop-blur-md border-b border-zinc-800/80">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-8">
        
        {/* Zone 1: Single text element wordmark */}
        <a href="/" className="text-base font-semibold tracking-tight text-white whitespace-nowrap shrink-0 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-zinc-400" />
          Mono_Micro
        </a>

        {/* Zone 2: Clean single-line text navigation links */}
        <nav className="hidden md:flex items-center gap-7 text-xs font-medium text-zinc-400">
          <a href="#demarche" className="hover:text-white transition-colors whitespace-nowrap shrink-0">Démarche</a>
          <a href="#commandes" className="hover:text-white transition-colors whitespace-nowrap shrink-0">Commandes</a>
          <a href="#installation" className="hover:text-white transition-colors whitespace-nowrap shrink-0">Installation Node & Python</a>
          <a href="#securite" className="hover:text-white transition-colors whitespace-nowrap shrink-0">Sécurité</a>
        </nav>

        {/* Zone 3: Single primary action */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={copyQuickNpx}
            className="inline-flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-md bg-zinc-800/80 hover:bg-zinc-800 text-zinc-300 border border-zinc-700/60 transition-colors whitespace-nowrap shrink-0"
            title="Copier la commande npx"
          >
            <span className="text-zinc-500">$</span>
            <span>npx mono2micro</span>
            {copied ? <Check className="w-3.5 h-3.5 text-zinc-200 ml-1" /> : <Copy className="w-3.5 h-3.5 text-zinc-500 ml-1" />}
          </button>
          
          <a
            href="https://www.alphaxiv.org/abs/2306.08851"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 font-medium transition-colors whitespace-nowrap shrink-0"
          >
            <span>alphaXiv (2023)</span>
            <ExternalLink className="w-3 h-3 text-zinc-700" />
          </a>
        </div>

      </div>
    </header>
  );
};
