import React from 'react';
import { ShieldCheck, ShieldAlert, CheckSquare2 } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const SafetyGuarantees: React.FC = () => {
  const { t } = useLanguage();

  return (
    <section id="securite" className="py-16 max-w-5xl mx-auto px-4 sm:px-6">
      
      <div className="mb-8">
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
          {t.safety.title}
        </h2>
        <p className="mt-1 text-sm text-zinc-400">
          {t.safety.subtitle}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        <div className="p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
          <div className="w-8 h-8 rounded-lg bg-zinc-800 text-zinc-300 flex items-center justify-center mb-4">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-white mb-2">
            {t.safety.s1Title}
          </h3>
          <p className="text-xs text-zinc-400 leading-relaxed">
            {t.safety.s1Desc}
          </p>
        </div>

        <div className="p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
          <div className="w-8 h-8 rounded-lg bg-zinc-800 text-zinc-300 flex items-center justify-center mb-4">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-white mb-2">
            {t.safety.s2Title}
          </h3>
          <p className="text-xs text-zinc-400 leading-relaxed">
            {t.safety.s2Desc}
          </p>
        </div>

        <div className="p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
          <div className="w-8 h-8 rounded-lg bg-zinc-800 text-zinc-300 flex items-center justify-center mb-4">
            <CheckSquare2 className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-white mb-2">
            {t.safety.s3Title}
          </h3>
          <p className="text-xs text-zinc-400 leading-relaxed">
            {t.safety.s3Desc}
          </p>
        </div>

      </div>

    </section>
  );
};
