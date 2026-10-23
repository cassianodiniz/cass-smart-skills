import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

import { external } from '../../../scripts/runtime_paths.mjs';

function seconds(value) {
  if (!/^\d+(?::\d+){0,2}(?:\.\d+)?$/.test(value ?? '')) return NaN;
  return value.split(':').reverse().reduce((sum, part, i) => sum + Number(part) * 60 ** i, 0);
}
function run(command, args) {
  const result = spawnSync(command, args, { encoding: 'utf8', shell: false });
  if (result.error || result.status !== 0) throw new Error(`${command}: ${result.error?.message || result.stderr || 'falhou'}`);
  return result.stdout;
}
try {
  const [video, start, end, destination, ...extra] = process.argv.slice(2);
  const a = seconds(start), b = seconds(end);
  if (!video || !destination || extra.length || !existsSync(video) || !Number.isFinite(a) || !Number.isFinite(b) || b <= a) {
    throw new Error('Uso: node scripts/trecho.mjs <video-existente> <inicio> <fim-maior-que-inicio> <pasta-nova>');
  }
  const output = external(path.resolve(destination));
  if (existsSync(output)) throw new Error('A pasta de fala já existe; escolha outra para preservar os arquivos.');
  run('ffmpeg', ['-version']);
  run('mlx_whisper', ['--help']);
  mkdirSync(output, { recursive: true });
  const wav = path.join(output, 'trecho.wav');
  run('ffmpeg', ['-v', 'error', '-ss', String(a), '-i', path.resolve(video), '-t', String(b - a), '-vn', '-ac', '1', '-ar', '16000', wav]);
  run('mlx_whisper', [wav, '--model', 'mlx-community/whisper-large-v3-turbo', '--language', 'pt', '--task', 'transcribe', '--word-timestamps', 'True', '--output-format', 'json', '--output-dir', output]);
  const transcript = JSON.parse(readFileSync(path.join(output, 'trecho.json'), 'utf8'));
  writeFileSync(path.join(output, 'fala.txt'), `${(transcript.text ?? '').trim()}\n`);
  writeFileSync(path.join(output, 'fala_tempos.txt'), (transcript.segments ?? []).flatMap(s => s.words ?? []).map(w => `${Number(w.start).toFixed(2)}  ${w.word.trim()}\n`).join(''));
  console.log(`Fala e tempos por palavra: ${output} (${b - a}s)`);
} catch (error) {
  console.error(`${error.message}\nSe MLX estiver ausente ou incompatível, peça a fala escrita e a duração; não envie o vídeo a outro serviço automaticamente.`);
  process.exit(2);
}
