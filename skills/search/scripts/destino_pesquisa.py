#!/usr/bin/env python3
"""Arquiva pesquisas na pasta externa configurada pelo usuário."""
from __future__ import annotations
import argparse
import datetime
import os
import re
import sys
import unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
import smart_config

def slug(texto: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return (re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower() or "pesquisa")[:60]

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tema", nargs="?")
    parser.add_argument("--data", type=datetime.date.fromisoformat, help="AAAA-MM-DD")
    parser.add_argument("--conferir", action="store_true", help="verifica sem criar arquivos")
    args = parser.parse_args(argv)
    destino = None
    try:
        destino = smart_config.externo(smart_config.carregar()['pastas']['pesquisas'])
        if args.conferir:
            base = destino if destino.exists() else destino.parent
            if not os.access(base, os.W_OK | os.X_OK):
                raise PermissionError("a pasta de pesquisas não permite gravação")
            print(f"pesquisas: {destino} [ok]")
            return 0
        destino.mkdir(parents=True, exist_ok=True)
        if not args.tema:
            print(destino)
            return 0
        data = args.data or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).date()
        nome = f"{slug(args.tema)}-{data.isoformat()}"
        contador = 1
        while True:
            estudo = destino / (nome if contador == 1 else f"{nome}-{contador}")
            try:
                estudo.mkdir(exist_ok=False)
                break
            except FileExistsError:
                contador += 1
        (estudo / "referencias").mkdir()
        print(estudo)
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERRO ao arquivar em {destino}: {exc}. Nenhum outro destino será usado.", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
