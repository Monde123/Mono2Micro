import React from 'react';
import { Target, Layers, GitMerge } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const CorePrinciples: React.FC = () => {
  const { t } = useLanguage();

  return (
    <section id="demarche" className="py-16 max-w-5xl mx-auto px-4 sm:px-6">
      
      <div className="mb-8">
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
          {t.principles.title}
        </h2>
        <p className="mt-1 text-sm text-zinc-400">
          {t.principles.subtitle}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        {/* Card 1 */}
        <div className="p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/80 flex flex-col justify-between hover:border-zinc-700/80 transition-colors">
          <div>
            <div className="w-8 h-8 rounded-lg bg-zinc-800 text-zinc-300 flex items-center justify-center mb-4">
              <Target className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-2">
              {t.principles.c1Title}
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              {t.principles.c1Desc}
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-zinc-800/60 text-[11px] font-mono text-zinc-500">
            {t.principles.c1Ref}
          </div>
        </div>

        {/* Card 2 */}
        <div className="p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/80 flex flex-col justify-between hover:border-zinc-700/80 transition-colors">
          <div>
            <div className="w-8 h-8 rounded-lg bg-zinc-800 text-zinc-300 flex items-center justify-center mb-4">
              <Layers className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-2">
              {t.principles.c2Title}
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              {t.principles.c2Desc}
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-zinc-800/60 text-[11px] font-mono text-zinc-500">
            {t.principles.c2Ref}
          </div>
        </div>

        {/* Card 3 */}
        <div className="p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/80 flex flex-col justify-between hover:border-zinc-700/80 transition-colors">
          <div>
            <div className="w-8 h-8 rounded-lg bg-zinc-800 text-zinc-300 flex items-center justify-center mb-4">
              <GitMerge className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-2">
              {t.principles.c3Title}
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              {t.principles.c3Desc}
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-zinc-800/60 text-[11px] font-mono text-zinc-500">
            {t.principles.c3Ref}
          </div>
        </div>

      </div>

    </section>
  );
};
