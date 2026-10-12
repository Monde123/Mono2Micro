import React, { useState } from 'react';
import { Copy, Check, ArrowRight, ExternalLink } from 'lucide-react';

export const Hero: React.FC = () => {
  const [runtime, setRuntime] = useState<'node' | 'python'>('node');
  const [copied, setCopied] = useState(false);

  const command = runtime === 'node' ? 'npx mono2micro analyze' : 'agent analyze';

  const copyCommand = () => {
    navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="pt-20 pb-16 sm:pt-28 sm:pb-24 max-w-4xl mx-auto px-4 sm:px-6 text-center">
      
      {/* Quiet Academic Reference */}
      <div className="mb-6 inline-flex items-center gap-2 text-xs text-zinc-500 font-mono">
        <span>Hatem Hammad et al. (2023)</span>
        <span aria-hidden="true">·</span>
        <a
          href="https://www.alphaxiv.org/abs/2306.08851"
          target="_blank"
          rel="noopener noreferrer"
          className="text-zinc-400 hover:text-zinc-200 underline underline-offset-4 inline-flex items-center gap-1"
        >
          alphaXiv:2306.08851 <ExternalLink className="w-3 h-3 text-zinc-600" />
        </a>
      </div>

      {/* Main Headline */}
      <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-white max-w-3xl mx-auto leading-tight">
        Modernisez vos monolithes avec discernement
      </h1>

      {/* Subtitle */}
      <p className="mt-5 text-base sm:text-lg text-zinc-400 max-w-2xl mx-auto leading-relaxed">
        Un agent local pour inspecter votre architecture en lecture seule, challenger les hypothèses et évaluer le <strong>Monolithe Modulaire</strong> avant toute extraction distribuée.
      </p>

      {/* Interactive Runtime Selector & Quick Command */}
      <div className="mt-9 flex flex-col items-center justify-center gap-3">
        
        {/* Node vs Python toggle */}
        <div className="inline-flex p-1 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-medium">
          <button
            onClick={() => setRuntime('node')}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              runtime === 'node'
                ? 'bg-zinc-800 text-white shadow-sm'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            Node.js (npx)
          </button>
          <button
            onClick={() => setRuntime('python')}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              runtime === 'python'
                ? 'bg-zinc-800 text-white shadow-sm'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            Python (CLI)
          </button>
        </div>

        {/* Command Box */}
        <div className="flex items-center gap-3 px-4 py-2.5 bg-zinc-900/90 border border-zinc-800 rounded-lg font-mono text-sm text-zinc-200 shadow-sm">
          <span className="text-zinc-500 select-none">$</span>
          <span>{command}</span>
          <button
            onClick={copyCommand}
            className="p-1 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors ml-2"
            title="Copier la commande"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>

      </div>

      {/* 3 Key Tenets */}
      <div className="mt-12 pt-8 border-t border-zinc-800/60 flex flex-wrap items-center justify-center gap-y-2 gap-x-6 text-xs text-zinc-500">
        <div>100% Local & Privé</div>
        <div>·</div>
        <div>Avocat du diable bloquant</div>
        <div>·</div>
        <div>Réversibilité Git garantie</div>
      </div>

    </section>
  );
};
