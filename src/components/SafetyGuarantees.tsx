import React from 'react';
import { ShieldCheck, ShieldAlert, CheckSquare2 } from 'lucide-react';

export const SafetyGuarantees: React.FC = () => {
  return (
    <section id="securite" className="py-16 max-w-5xl mx-auto px-4 sm:px-6">
      
      <div className="mb-8">
        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
          Garanties de sécurité
        </h2>
        <p className="mt-1 text-sm text-zinc-400">
          Trois règles d'or pour préserver votre code et vos secrets.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        <div className="p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
          <div className="w-8 h-8 rounded-lg bg-zinc-800 text-zinc-300 flex items-center justify-center mb-4">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-white mb-2">
            100% Local & Étanche
          </h3>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Le CLI s'exécute sur votre machine. Vos clés API restent dans votre environnement local. Ce site web vitrine est purement informatif et ne reçoit aucun code de projet.
          </p>
        </div>

        <div className="p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
          <div className="w-8 h-8 rounded-lg bg-zinc-800 text-zinc-300 flex items-center justify-center mb-4">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-white mb-2">
            L'Avocat du Diable Bloquant
          </h3>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Avant toute modification, un sous-agent contradicteur recherche les couplages cachés. Il bloque l'étape si une table de base de données est partagée sans abstraction.
          </p>
        </div>

        <div className="p-6 rounded-xl bg-zinc-900/40 border border-zinc-800/80">
          <div className="w-8 h-8 rounded-lg bg-zinc-800 text-zinc-300 flex items-center justify-center mb-4">
            <CheckSquare2 className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-white mb-2">
            Quality Gate sans Moyenne
          </h3>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Le passage en production est strictement binaire. Aucun calcul de moyenne ne peut compenser un échec critique. Si un test obligatoire échoue, la livraison est rejetée.
          </p>
        </div>

      </div>

    </section>
  );
};
