#!/usr/bin/env node

/**
 * Mono2Micro Node.js CLI Runner
 * Proxies commands to the local mono2micro engine.
 * Allows running via `npx mono2micro <command>` or `npm install -g mono2micro`.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const args = process.argv.slice(2);

// Check if python3 is available
const pythonBin = process.env.PYTHON_BIN || 'python3';
const cliScript = path.resolve(__dirname, '../agent_cli/mono2micro/cli.py');

const env = {
  ...process.env,
  PYTHONPATH: [
    path.resolve(__dirname, '../agent_cli'),
    process.env.PYTHONPATH || ''
  ].filter(Boolean).join(path.delimiter)
};

const child = spawn(pythonBin, ['-m', 'mono2micro.cli', ...args], {
  stdio: 'inherit',
  env
});

child.on('error', (err) => {
  if (err.code === 'ENOENT') {
    console.error(`[mono2micro] Erreur : Python 3 est requis pour exécuter l'agent. Veuillez installer python3 ou définir PYTHON_BIN.`);
  } else {
    console.error(`[mono2micro] Erreur d'exécution :`, err.message);
  }
  process.exit(1);
});

child.on('close', (code) => {
  process.exit(code ?? 0);
});
