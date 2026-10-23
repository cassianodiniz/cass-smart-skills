import { cpSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { external } from '../../../scripts/runtime_paths.mjs';

const skill = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [destination, seconds, format, ...extra] = process.argv.slice(2);
const duration = Number(seconds);
if (!destination || !Number.isFinite(duration) || duration <= 0 || extra.length || (format && format !== 'tela-cheia')) {
  console.error('Uso: node scripts/novo.mjs <pasta-nova> <duracao-segundos-positiva> [tela-cheia]');
  process.exit(2);
}
const output = external(path.resolve(destination));
if (existsSync(output)) {
  console.error(`A pasta já existe; escolha outra para preservar seus arquivos: ${output}`);
  process.exit(2);
}
const height = format === 'tela-cheia' ? 1920 : 960;
const html = readFileSync(path.join(skill, 'assets', 'base.html'), 'utf8')
  .replaceAll('__W__', '1080').replaceAll('__H__', String(height)).replaceAll('__DUR__', String(duration));
mkdirSync(output, { recursive: true });
for (const name of ['fontes', 'gsap']) cpSync(path.join(skill, 'assets', name), path.join(output, name), { recursive: true });
writeFileSync(path.join(output, 'index.html'), html);
console.log(`Criado: ${path.join(output, 'index.html')} (1080×${height}, ${duration}s)`);
