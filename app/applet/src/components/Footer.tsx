import React from 'react';
import { ExternalLink } from 'lucide-react';
import { useLanguage } from '@/src/context/LanguageContext';

export const Footer: React.FC = () => {
  const { t } = useLanguage();

  return (
    <footer className="bg-[#101114] border-t border-zinc-800/80 py-10 text-xs text-zinc-500">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-6 text-center sm:text-left">
        <div>
          <span className="font-semibold text-zinc-300">Mono2Micro</span>
          <p className="mt-1 text-[11px] text-zinc-500 max-w-sm">
            {t.footer.academic}
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-6 text-xs text-zinc-400">
          <a
            href="https://www.alphaxiv.org/abs/2306.08851"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-white transition-colors inline-flex items-center gap-1"
          >
            alphaXiv:2306.08851 <ExternalLink className="w-3 h-3 text-zinc-600" />
          </a>
          <a href="#demarche" className="hover:text-white transition-colors">{t.nav.approach}</a>
          <a href="#commandes" className="hover:text-white transition-colors">{t.nav.commands}</a>
          <a href="#rapports" className="hover:text-white transition-colors">{t.nav.reports}</a>
          <a href="#installation" className="hover:text-white transition-colors">{t.nav.installation}</a>
          <a href="#securite" className="hover:text-white transition-colors">{t.nav.security}</a>
        </div>
      </div>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 mt-6 pt-5 border-t border-zinc-800/40 text-[11px] text-zinc-500 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4 text-center sm:text-left">
          <span>© 2026 Mono2Micro · {t.footer.tagline}</span>
          <span className="hidden sm:inline text-zinc-700">|</span>
          <span className="inline-flex items-center gap-1 text-amber-400/90 font-medium">
            📜 {t.footer.license}
          </span>
        </div>
        <div className="text-zinc-500 text-center sm:text-right">
          <span>{t.footer.benchmarks}</span>
        </div>
      </div>
    </footer>
  );
};
