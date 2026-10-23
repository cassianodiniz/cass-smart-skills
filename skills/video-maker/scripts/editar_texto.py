#!/usr/bin/env python3
"""Edição por texto: o Cassiano apaga palavras da transcrição e o vídeo perde os trechos.

    # 1) gera o .md editável (e abre no TextEdit com: open -e arquivo.md)
    python3 editar_texto.py preparar palavras.json edicao.md

    # 2) depois que ele salvou: corta o vídeo
    python3 editar_texto.py aplicar palavras.json edicao.md fala.mp4 fala_editada.mp4

O `aplicar` compara as palavras do .md com as da transcrição (em ordem), corta o que
sumiu e confere o resultado transcrevendo de novo. A transcrição do vídeo editado fica
em fala_editada.json, pronta pra legenda.
"""
import difflib, json, os, re, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcrever import transcrever

SEP = "-" * 40
AVISO = ("Apague as palavras ou frases que você NÃO quer no vídeo. Não precisa mexer em mais nada.\n"
         "Depois salve (Cmd+S), feche e escreva \"pronto\" no chat.\n" + SEP)


def norm(t):
    return re.sub(r"[^\wà-úç]", "", t.lower())


def preparar(pal, md):
    d = json.load(open(pal, encoding="utf-8"))
    ws, linhas, i = d["palavras"], [], 0
    for s in d["segmentos"]:          # um bloco por frase do Whisper, sem tempo nenhum
        bloco = []
        while i < len(ws) and ws[i]["s"] <= s["e"] + 1e-3:
            bloco.append(ws[i]["w"]); i += 1
        if bloco:
            linhas.append(" ".join(bloco))
    if i < len(ws):
        linhas.append(" ".join(w["w"] for w in ws[i:]))
    open(md, "w", encoding="utf-8").write(AVISO + "\n\n" + "\n\n".join(linhas) + "\n")
    print(f"{md} pronto ({len(ws)} palavras)")


def segmentos_manter(ws, manter, dur):
    """Trechos do vídeo que ficam. Entre palavras mantidas vizinhas nada é cortado."""
    segs, i, n = [], 0, len(ws)
    while i < n:
        if not manter[i]:
            i += 1; continue
        j = i
        while j + 1 < n and manter[j + 1]:
            j += 1
        ini = 0.0 if i == 0 else max(ws[i]["s"] - 0.06, ws[i - 1]["e"])
        fim = dur if j == n - 1 else min(ws[j]["e"] + 0.10, ws[j + 1]["s"])
        segs.append((round(ini, 3), round(fim, 3)))
        i = j + 1
    return segs


def aplicar(pal, md, video, saida):
    ws = json.load(open(pal, encoding="utf-8"))["palavras"]
    corpo = open(md, encoding="utf-8").read().split(SEP, 1)[-1]
    ed = [norm(t) for t in corpo.split() if norm(t)]
    orig = [norm(w["w"]) for w in ws]
    manter = [False] * len(ws)
    sm = difflib.SequenceMatcher(None, orig, ed, autojunk=False)
    novas = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i1, i2):
                manter[k] = True
        elif tag in ("insert", "replace") and j2 > j1:
            novas += ed[j1:j2]
    if novas:
        print(f"aviso: palavras novas ou trocadas no texto foram ignoradas (só dá pra apagar): {' '.join(novas[:12])}")
    removidas = [ws[k]["w"] for k in range(len(ws)) if not manter[k]]
    print(f"removendo {len(removidas)} de {len(ws)} palavras")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", video], capture_output=True, text=True).stdout)
    segs = segmentos_manter(ws, manter, dur)
    pv, pa = [], []
    for i, (a, b) in enumerate(segs):
        L = b - a
        pv.append(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{i}]")
        pa.append(f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,"
                  f"afade=t=in:d=0.015,afade=t=out:st={max(0, L - 0.015):.3f}:d=0.015[a{i}]")
    fc = ";".join(pv + pa) + ";" + "".join(f"[v{i}][a{i}]" for i in range(len(segs))) \
        + f"concat=n={len(segs)}:v=1:a=1[v][a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-filter_complex", fc, "-map", "[v]",
                    "-map", "[a]", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt",
                    "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", saida], check=True)

    # conferência: o vídeo cortado tem que dizer o texto editado, nem mais nem menos
    j2 = os.path.splitext(saida)[0] + ".json"
    d2 = transcrever(saida, j2, forcar=True)
    fala = [norm(w["w"]) for w in d2["palavras"]]
    esperado = [orig[k] for k in range(len(ws)) if manter[k]]
    r = difflib.SequenceMatcher(None, esperado, fala, autojunk=False).ratio()
    print(f"conferência: esperado {len(esperado)} palavras, o vídeo diz {len(fala)} (semelhança {r:.0%})")
    if r < 0.93:
        for tag, i1, i2, k1, k2 in difflib.SequenceMatcher(None, esperado, fala, autojunk=False).get_opcodes():
            if tag != "equal":
                print(f"  {tag}: esperado {' '.join(esperado[i1:i2])!r} | ouvido {' '.join(fala[k1:k2])!r}")
        sys.exit("CONFERÊNCIA REPROVADA: o corte comeu ou deixou palavra. Veja acima.")
    print(f"pronto: {saida} | transcrição nova em {j2}")


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "preparar":
        preparar(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 6 and sys.argv[1] == "aplicar":
        aplicar(*sys.argv[2:6])
    else:
        sys.exit(__doc__)
