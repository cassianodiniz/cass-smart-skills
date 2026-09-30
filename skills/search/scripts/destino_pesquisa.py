#!/usr/bin/env python3
"""Arquiva pesquisas dentro da skill, independentemente do diretório de trabalho."""
from __future__ import annotations
import argparse
import datetime
import os
import re
import sys
import unicodedata
from pathlib import Path

def slug(texto: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return (re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower() or "pesquisa")[:60]

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tema", nargs="?")
    parser.add_argument("--data", type=datetime.date.fromisoformat, help="AAAA-MM-DD")
    parser.add_argument("--conferir", action="store_true", help="verifica sem criar arquivos")
    args = parser.parse_args(argv)
    raiz = Path(__file__).resolve().parent.parent
    destino = raiz / "pesquisas"
    try:
        if destino.is_symlink() or destino.resolve() != destino or (destino.exists() and not destino.is_dir()):
            raise OSError("pesquisas/ deve ser uma pasta dentro desta skill, sem redirecionamento")
        if args.conferir:
            base = destino if destino.exists() else raiz
            if not os.access(base, os.W_OK | os.X_OK):
                raise PermissionError("a instalação da skill não permite gravar pesquisas")
            print(f"pesquisas: {destino} [ok]")
            return 0
        destino.mkdir(exist_ok=True)
        if not args.tema:
            print(destino)
            return 0
        data = args.data or datetime.date.today()
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
    except OSError as exc:
        print(f"ERRO ao arquivar em {destino}: {exc}. Nenhum outro destino será usado.", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
