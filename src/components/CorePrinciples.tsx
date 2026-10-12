import React from 'react';
import { Target, Layers, GitMerge } from 'lucide-react';

export const CorePrinciples: React.FC = () => {
  return (
    <section id="demarche" className="py-16 max-w-5xl mx-auto px-4 sm:px-6">
      
      <div className="mb-8">
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
          La démarche méthodologique
        </h2>
        <p className="mt-1 text-sm text-zinc-400">
          Les 3 fondements du papier de recherche Hammad et al. (2023).
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
              01. L'objectif avant l'architecture
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Découper n'est pas un but en soi. L'agent interroge vos motivations (charge ciblée, indépendance d'équipe ou simple lisibilité) et signale si le monolithe peut être conservé.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-zinc-800/60 text-[11px] font-mono text-zinc-500">
            Hammad et al. (2023) § I & II
          </div>
        </div>

        {/* Card 2 */}
        <div className="p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/80 flex flex-col justify-between hover:border-zinc-700/80 transition-colors">
          <div>
            <div className="w-8 h-8 rounded-lg bg-zinc-800 text-zinc-300 flex items-center justify-center mb-4">
              <Layers className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-2">
              02. Priorité au Monolithe Modulaire
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              L'agent évalue en priorité la modularisation interne. Vous bénéficiez de frontières DDD nettes sans subir la taxe distribuée (latence réseau, indisponibilités partielles, sagas).
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-zinc-800/60 text-[11px] font-mono text-zinc-500">
            Optimal pour équipes &lt; 8 devs
          </div>
        </div>

        {/* Card 3 */}
        <div className="p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/80 flex flex-col justify-between hover:border-zinc-700/80 transition-colors">
          <div>
            <div className="w-8 h-8 rounded-lg bg-zinc-800 text-zinc-300 flex items-center justify-center mb-4">
              <GitMerge className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-semibold text-white mb-2">
              03. Strangler Fig & Propriété des Données
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Si une extraction est justifiée, elle commence par le domaine le moins couplé, avec routage réversible et synchronisation miroir des données pour prévenir toute régression.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-zinc-800/60 text-[11px] font-mono text-zinc-500">
            Hammad et al. (2023) § IV, V & VI
          </div>
        </div>

      </div>

    </section>
  );
};
