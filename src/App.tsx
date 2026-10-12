/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { Header } from './components/Header';
import { Hero } from './components/Hero';
import { CorePrinciples } from './components/CorePrinciples';
import { CliTerminalDemo } from './components/CliTerminalDemo';
import { Quickstart } from './components/Quickstart';
import { SafetyGuarantees } from './components/SafetyGuarantees';
import { Footer } from './components/Footer';

export default function App() {
  return (
    <div className="min-h-screen bg-[#141519] text-zinc-100 flex flex-col font-sans selection:bg-zinc-700 selection:text-white">
      <Header />
      <main className="flex-1">
        <Hero />
        <CorePrinciples />
        <CliTerminalDemo />
        <Quickstart />
        <SafetyGuarantees />
      </main>
      <Footer />
    </div>
  );
}
