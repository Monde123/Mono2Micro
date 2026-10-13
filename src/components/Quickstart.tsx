import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const Quickstart: React.FC = () => {
  const { language, t } = useLanguage();
  const [activeTab, setActiveTab] = useState<'node' | 'python'>('node');
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const currentSteps = activeTab === 'node' ? t.quickstart.nodeSteps : t.quickstart.pythonSteps;

  const copyCmd = (cmd: string, index: number) => {
    navigator.clipboard.writeText(cmd);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <section id="installation" className="py-16 max-w-5xl mx-auto px-4 sm:px-6">
      
      <div className="mb-6 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
            {t.quickstart.title}
          </h2>
          <p className="mt-1 text-sm text-zinc-400">
            {t.quickstart.subtitle}
          </p>
        </div>

        {/* Runtime Switcher */}
        <div className="inline-flex p-1 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-medium">
          <button
            onClick={() => setActiveTab('node')}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === 'node' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            {t.quickstart.nodeTab}
          </button>
          <button
            onClick={() => setActiveTab('python')}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === 'python' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            {t.quickstart.pythonTab}
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {currentSteps.map((st, i) => (
          <div
            key={st.title}
            className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-zinc-700/80 transition-colors"
          >
            <div>
              <h3 className="text-sm font-semibold text-white">{st.title}</h3>
              <p className="text-xs text-zinc-400 mt-0.5">{st.note}</p>
            </div>

            <div className="flex items-center gap-2 bg-zinc-950 px-3 py-2 rounded-lg border border-zinc-800 font-mono text-xs text-zinc-200 shrink-0">
              <span className="text-zinc-500 select-none">$</span>
              <span>{st.cmd}</span>
              <button
                onClick={() => copyCmd(st.cmd, i)}
                className="p-1 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors ml-1"
                title={language === 'fr' ? 'Copier la commande' : 'Copy command'}
              >
                {copiedIndex === i ? (
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>
        ))}
      </div>

    </section>
  );
};
