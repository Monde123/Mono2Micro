import React from 'react';
import { ExternalLink } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export const Footer: React.FC = () => {
  const { t } = useLanguage();

  return (
    <footer className="bg-[#101114] border-t border-zinc-800/80 py-10 text-xs text-zinc-500">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-6 text-center sm:text-left">
        
        <div>
          <span className="font-semibold text-zinc-300">Mono_Micro</span>
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

      <div className="max-w-5xl mx-auto px-4 sm:px-6 mt-6 pt-5 border-t border-zinc-800/40 text-[11px] text-zinc-600 flex flex-col sm:flex-row items-center justify-between gap-2">
        <span>© 2026 Mono_Micro · {t.footer.tagline}</span>
        <span>{t.footer.disclaimer}</span>
      </div>
    </footer>
  );
};
