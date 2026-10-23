#!/usr/bin/env python3
"""Legenda dinâmica em ASS: grupo de palavras na tela, palavra falada em verde.

    # 1) rascunho dos grupos (um por linha), pra revisar antes
    python3 gerar_legenda.py palavras.json grupos.txt --rascunho [--inicio S] [--fim S]

    # 2) legenda a partir dos grupos revisados
    python3 gerar_legenda.py palavras.json grupos.txt --saida legenda.ass \
        [--inicio S] [--fim S] [--tela-cheia 27.9-37.08 ...]

palavras.json vem do transcrever.py. --inicio/--fim recortam a fala (tempo do vídeo
original); a legenda sai no relógio do reel (o --inicio vira zero).
--tela-cheia usa o relógio do reel: ali a legenda fica em y=960.
Destaque dourado (vídeo de IA, o padrão); --nutricao usa o verde.
"""
import argparse, json, os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(os.path.dirname(AQUI), "fonts", "inter-800.ttf")
TAM, LARG_MAX = 99, 960   # 1080 menos as margens de 60
VERDE, OURO, BRANCO = r"{\c&H005AB819&}", r"{\c&H0019A8EF&}", r"{\c&H00FFFFFF&}"
CAB = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter ExtraBold,99,&H00FFFFFF,&H00FFFFFF,&H40000000,&H00000000,0,0,0,0,100,100,0,0,1,11,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def norm(t):
    return re.sub(r"[^\wà-úç]", "", t.lower())


def limpo(t):
    return t if t.endswith("...") else re.sub(r"[.,;:!]+$", "", t)


def largura(txt):
    try:
        from PIL import ImageFont
        return ImageFont.truetype(FONTE, TAM).getlength(txt)
    except Exception:
        return len(txt) * 55


def ts(t):
    t = max(0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def carregar(p, inicio, fim):
    ws = json.load(open(p, encoding="utf-8"))["palavras"]
    ws = [w for w in ws if w["s"] >= inicio - 0.02 and (fim is None or w["s"] < fim - 0.05)]
    return [(w["s"] - inicio, w["e"] - inicio, w["w"]) for w in ws]


LIGA = {"que", "de", "da", "do", "o", "a", "os", "as", "e", "pra", "para", "com", "em", "no", "na",
        "um", "uma", "se", "não", "eu", "ela", "ele", "porque", "mas", "só", "é"}


def rascunho(ws):
    """Quebra simples: até 3 palavras, fecha em pontuação e não termina grupo em palavra
    de ligação ("que", "de", "pra"...). É ponto de partida: revise à mão depois."""
    grupos, g = [], []
    for i, (_, _, t) in enumerate(ws):
        g.append(t)
        prox_ne = i + 1 < len(ws) and ws[i + 1][2].lower().startswith("né")
        if (re.search(r"[.?!,…]$", t) and not prox_ne) or largura(" ".join(g)) > LARG_MAX - 120:
            grupos.append(" ".join(g)); g = []
        elif len(g) >= 3:
            if norm(g[-1]) in LIGA:
                grupos.append(" ".join(g[:-1])); g = [g[-1]]
            else:
                grupos.append(" ".join(g)); g = []
    if g:
        grupos.append(" ".join(g))
    return grupos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("palavras"); ap.add_argument("grupos")
    ap.add_argument("--rascunho", action="store_true")
    ap.add_argument("--saida")
    ap.add_argument("--inicio", type=float, default=0.0)
    ap.add_argument("--fim", type=float)
    ap.add_argument("--tela-cheia", nargs="*", default=[])
    ap.add_argument("--y-dividida", type=int, default=1040)
    ap.add_argument("--nutricao", action="store_true")
    ap.add_argument("--y-cheia", type=int, default=960)
    a = ap.parse_args()

    ws = carregar(a.palavras, a.inicio, a.fim)
    if a.rascunho:
        open(a.grupos, "w", encoding="utf-8").write("\n".join(rascunho(ws)) + "\n")
        print(f"rascunho com {len(ws)} palavras em {a.grupos}: revise os grupos (não partir ideia no meio)")
        return

    fim_reel = (a.fim - a.inicio) if a.fim else ws[-1][1] + 0.5
    cheia = [tuple(map(float, x.split("-"))) for x in a.tela_cheia]
    frases = [l.strip() for l in open(a.grupos, encoding="utf-8") if l.strip()]
    grupos, k = [], 0
    for fr in frases:
        n = len(fr.split()); g = ws[k:k + n]
        if [norm(x[2]) for x in g] != [norm(p) for p in fr.split()]:
            sys.exit(f"o grupo {fr!r} não bate com a fala: {' '.join(x[2] for x in g)!r}. "
                     "Os grupos precisam ter as palavras da transcrição, na ordem.")
        grupos.append(g); k += n
    if k != len(ws):
        sys.exit(f"sobraram palavras sem grupo: {' '.join(x[2] for x in ws[k:k + 8])}...")
    for fr in frases:
        if largura(fr) > LARG_MAX:
            print(f"aviso: {fr!r} passa da largura da tela ({largura(fr):.0f}px > {LARG_MAX}); parta em dois")

    ev = []
    for gi, g in enumerate(grupos):
        prox = grupos[gi + 1][0][0] if gi + 1 < len(grupos) else fim_reel
        fim_g = min(prox, g[-1][1] + 0.6, fim_reel)
        meio = (g[0][0] + g[-1][1]) / 2      # o grupo vai pra onde passa mais tempo
        y = a.y_cheia if any(x <= meio < z for x, z in cheia) else a.y_dividida

        def rot(j, x):   # mantém a vírgula antes de "né?", que é pergunta
            if j + 1 < len(g) and g[j + 1][2].lower().startswith("né") and x[2].endswith(","):
                return x[2]
            return limpo(x[2])
        for wi, w in enumerate(g):
            b = g[wi + 1][0] if wi + 1 < len(g) else fim_g
            if b - w[0] < 0.01:      # palavra de duração zero no Whisper: não vira evento
                continue
            txt = " ".join(((VERDE if a.nutricao else OURO) if j == wi else BRANCO) + rot(j, x) for j, x in enumerate(g))
            pop = r"{\fscx86\fscy86\t(0,100,\fscx100\fscy100)}" if wi == 0 else ""
            ev.append(f"Dialogue: 0,{ts(w[0])},{ts(b)},Cap,,0,0,0,,{{\\blur14\\an5\\pos(540,{y})}}{pop}{txt}")
    open(a.saida, "w", encoding="utf-8").write(CAB + "\n".join(ev) + "\n")
    print(f"{len(grupos)} grupos -> {a.saida}")


if __name__ == "__main__":
    main()
