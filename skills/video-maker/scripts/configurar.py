#!/usr/bin/env python3
"""Verificar ambiente ou salvar configuração local; não instala nem edita vídeos."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import sys


def validar(dados):
    if not isinstance(dados, dict) or dados.get('versao') != 1:
        raise ValueError('Configuração inválida: versão esperada 1.')
    if dados.get('sistema') not in {'mac-apple-silicon', 'mac-intel', 'windows', 'linux'}:
        raise ValueError('Escolha o sistema do computador.')
    if dados.get('origem') != 'pasta' or dados.get('entrega') != 'pasta':
        raise ValueError('Esta distribuição recebe e entrega somente arquivos em pastas locais.')
    if dados.get('perfil') not in {'ia', 'nutricao'}:
        raise ValueError('Escolha o visual IA ou nutrição.')
    for key in ['headline', 'legendas']:
        if not isinstance(dados.get(key), bool):
            raise ValueError('Headline e legendas devem ser verdadeiro ou falso.')
    pastas = dados.get('pastas')
    if not isinstance(pastas, dict):
        raise ValueError('Informe as pastas de trabalho.')
    for key in ['entrada', 'trabalho', 'saida', 'aulas', 'transcricoes']:
        if not isinstance(pastas.get(key), str) or not pastas[key].strip() or '\x00' in pastas[key]:
            raise ValueError('Informe uma pasta válida para ' + key + '.')
    if not isinstance(dados.get('perfil_instagram'), str):
        raise ValueError('Perfil do Instagram inválido.')
    return dados


def verificar():
    tools = {name: bool(shutil.which(name)) for name in ['ffmpeg', 'ffprobe', 'mlx_whisper', 'yt-dlp', 'node']}
    tools.update({'Pillow': importlib.util.find_spec('PIL') is not None,
                  'numpy': importlib.util.find_spec('numpy') is not None,
                  'faster_whisper': importlib.util.find_spec('faster_whisper') is not None})
    apple = platform.system() == 'Darwin' and platform.machine().lower() in {'arm64', 'aarch64'}
    return {'sistema_detectado': platform.system(), 'arquitetura': platform.machine(),
            'python': platform.python_version(), 'ferramentas': tools,
            'montagem_pronta': tools['ffmpeg'] and tools['ffprobe'] and tools['Pillow'] and tools['numpy'],
            'transcricao_pronta': ((apple and tools['mlx_whisper']) or tools['faster_whisper']) and tools['ffmpeg'] and tools['ffprobe'],
            'observacao': 'Presença de ferramenta não comprova funcionamento. Teste com arquivos sintéticos antes de usar mídia pessoal.'}


def salvar(projeto, origem):
    projeto = Path(projeto).expanduser().resolve()
    if not projeto.is_dir():
        raise ValueError('A pasta do projeto não existe; escolha uma pasta existente.')
    dados = validar(json.loads(Path(origem).read_text(encoding='utf-8')))
    destino = projeto / '.video-maker.json'
    if destino.exists():
        anterior = validar(json.loads(destino.read_text(encoding='utf-8')))
        if anterior == dados:
            return destino
        backup = projeto / '.video-maker.anterior.json'
        if backup.exists():
            raise ValueError('Já existe uma configuração anterior guardada. Preserve-a com outro nome antes de alterar de novo.')
        shutil.copy2(destino, backup)
    temporario = projeto / '.video-maker.json.tmp'
    with temporario.open('x', encoding='utf-8') as file:
        json.dump(dados, file, ensure_ascii=False, indent=2)
        file.write('\n')
    os.replace(temporario, destino)
    return destino


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='acao', required=True)
    sub.add_parser('verificar')
    save = sub.add_parser('salvar')
    save.add_argument('--projeto', required=True)
    save.add_argument('--dados', required=True)
    args = parser.parse_args()
    try:
        if args.acao == 'verificar':
            print(json.dumps(verificar(), ensure_ascii=False, indent=2))
        else:
            print('Configuração salva: ' + str(salvar(args.projeto, args.dados)))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
