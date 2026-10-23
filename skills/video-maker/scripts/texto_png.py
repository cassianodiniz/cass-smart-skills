#!/usr/bin/env python3
"""Textos do reel em PNG transparente (1080 de largura), pra entrar como sobreposição no montar.py.

    python3 texto_png.py headline "Ele resolveu o maior problema de quem usa Claude e GPT" saida.png \
        --destaque "maior problema" [--emoji 🤯] [--nutricao]
    python3 texto_png.py segue "@seu_perfil" saida.png      (ou saida.mov: animada, com o clique)

headline: caixa alta, Inter ExtraBold, caixa preta, palavras do --destaque na cor de destaque
(dourado em IA, verde com --nutricao), sem ponto final. Uma linha só em 62 px quando cabe; senão
2 linhas da mesma largura em 52 px: o script testa as quebras sem partir o destaque e espaça as letras
da linha mais curta (ela cresce até 25% antes, pra não abrir buracos). --emoji aceita um ou dois
emojis, no fim do texto; com --emoji-inicio, no começo.
segue: pílula escura numa linha, ícone do Instagram à esquerda, "Segue o" branco e o @ em dourado.
Com saída .mov, a pílula entra com mola, recebe um toque (anel dourado) e solta o balão vermelho de
novo seguidor; vídeo transparente de 3,5 s (--dur muda). Em sobreposicoes, use o y da pílula - 246.
A primeira linha impressa é a altura do PNG (pra calcular o y: centro na divisa = 960 - altura/2).
"""
import argparse, os, re
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts", "inter-800.ttf")
EMOJI = "/System/Library/Fonts/Apple Color Emoji.ttc"
OURO, VERDE, BRANCO = (239, 168, 25, 255), (25, 184, 90, 255), (255, 255, 255, 255)


def emoji_img(e, alt):
    """Um ou mais emojis lado a lado, na altura alt (sequências com ZWJ ficam juntas)."""
    partes = re.findall(r"[^\s\u200d\ufe0f]\ufe0f?(?:\u200d[^\s\u200d\ufe0f]\ufe0f?)*", e)
    ims = []
    for p in partes:
        im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), p.replace("\ufe0f", ""), font=ImageFont.truetype(EMOJI, 160), embedded_color=True)
        ims.append(im.crop(im.getbbox()).resize((alt, alt), Image.LANCZOS))
    gap = alt // 6
    out = Image.new("RGBA", (len(ims) * alt + gap * (len(ims) - 1), alt), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        out.alpha_composite(im, (i * (alt + gap), 0))
    return out


def headline(texto, saida, destaque, emoji, cor, tam=52, larg_max=950, inicio=False, uma=62, larg_uma=1000):
    palavras = re.sub(r"[.!]+$", "", texto.strip()).upper().split()
    dest = set(destaque.upper().split())
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))

    def medir(t):
        f = ImageFont.truetype(FONTE, t); esp = d0.textlength(" ", font=f)
        H = f.getbbox("ÉG")[3] - f.getbbox("ÉG")[1]
        E = emoji_img(emoji, H) if emoji else None
        larg = lambda ws, e: sum(d0.textlength(w, font=f) for w in ws) + esp * (len(ws) - 1) + ((esp + E.width) if e else 0)
        return f, E, larg

    melhor = None
    if uma:  # primeiro tenta tudo numa linha só, maior
        f, E, larg = medir(uma)
        l1 = larg(palavras, bool(E))
        if l1 <= larg_uma:
            melhor, tam = (0, [(palavras, bool(E), l1)]), uma
    if melhor is None:
        f, E, larg = medir(tam)
    for k in range(1, len(palavras)) if melhor is None else []:
        a, b = palavras[:k], palavras[k:]
        if dest and dest & set(re.sub(r"\W", "", w) for w in a) and dest & set(re.sub(r"\W", "", w) for w in b):
            continue  # o destaque não se parte entre as linhas
        # emoji no fim da última linha (ou no começo da primeira); sem a opção "sem emoji",
        # que ganhava quando equilibrava melhor as linhas e sumia com ele (visto em 12/10/2026)
        for ea, eb in ([(1, 0)] if E and inicio else [(0, 1)] if E else [(0, 0)]):
            la, lb = larg(a, ea), larg(b, eb)
            if max(la, lb) > larg_max:
                continue
            nota = abs(la - lb)
            if melhor is None or nota < melhor[0]:
                melhor = (nota, [(a, ea, la), (b, eb, lb)])
    if melhor is None:
        return headline(texto, saida, destaque, emoji, cor, tam - 4, larg_max, inicio, uma=0)
    linhas = melhor[1]; W = max(l[2] for l in linhas)
    # a linha mais curta cresce até 25% e o resto vira espaço entre letras (sem buracos)
    fl = []
    for ws, e, nat in linhas:
        k = min(1.25, W / nat) if nat < W * 0.97 else 1.0
        fk = ImageFont.truetype(FONTE, round(tam * k)) if k > 1 else f
        fl.append((ws, e, fk))
    px, py, lg = 30, 20, 14
    alt = [fk.getbbox("ÉG")[3] - fk.getbbox("ÉG")[1] for _, _, fk in fl]
    Ht = py * 2 + sum(alt) + lg
    img = Image.new("RGBA", (1080, Ht), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    x0 = (1080 - W) / 2
    d.rounded_rectangle((x0 - px, 0, x0 + W + px, Ht), radius=20, fill=(0, 0, 0, 255))
    y = py
    for (ws, e, fk), h in zip(fl, alt):
        tp = fk.getbbox("ÉG")[1]; ek = fk.getlength(" ")
        Ek = E.resize((round(E.width * h / E.height), h), Image.LANCZOS) if e else None
        nat = sum(fk.getlength(w) for w in ws) + ek * (len(ws) - 1) + ((ek + Ek.width) if e else 0)
        nch = sum(len(w) for w in ws) + len(ws) - 1 + (1 if e else 0)
        tr = (W - nat) / max(1, nch); x = x0
        if e and inicio:
            img.alpha_composite(Ek, (int(x), int(y))); x += Ek.width + ek + tr
        for i, w in enumerate(ws):
            for c in w:
                d.text((x, y - tp), c, font=fk, fill=cor if re.sub(r"\W", "", w) in dest else BRANCO)
                x += fk.getlength(c) + tr
            if i < len(ws) - 1:
                x += ek + tr
        if e and not inicio:
            img.alpha_composite(Ek, (int(x + ek), int(y)))
        y += h + lg
    img.save(saida); print(Ht)


def segue(arroba, saida, tam=62, dur=3.5):
    f = ImageFont.truetype(FONTE, tam)
    pre = "Segue o "
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    w1, w2 = d0.textlength(pre, font=f), d0.textlength(arroba, font=f)
    ic, gap, px, py = 80, 26, 34, 22
    W = int(px * 2 + ic + gap + w1 + w2); Hh = ic + py * 2
    img = Image.new("RGBA", (1080, Hh + 50), (0, 0, 0, 0)); x0, y0 = (1080 - W) // 2, 20
    sombra = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((x0, y0 + 8, x0 + W, y0 + Hh + 8), radius=Hh // 2, fill=(0, 0, 0, 120))
    img.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0, y0, x0 + W, y0 + Hh), radius=Hh // 2, fill=(14, 14, 14, 225), outline=(255, 255, 255, 45), width=2)
    # ícone do Instagram: degradê amarelo → rosa → azul, câmera branca
    g = Image.new("RGBA", (ic, ic)); gp = g.load()
    paradas = [(0, (253, 244, 151)), (.3, (253, 89, 73)), (.6, (214, 36, 159)), (1, (40, 90, 235))]
    for yy in range(ic):
        for xx in range(ic):
            t = 1 - min(1, max(0, ((ic - xx) * 0.3 + yy * 0.9) / (ic * 1.2)))
            for i in range(3):
                (a, ca), (b, cb) = paradas[i], paradas[i + 1]
                if a <= t <= b:
                    k = (t - a) / (b - a); gp[xx, yy] = tuple(int(ca[j] + (cb[j] - ca[j]) * k) for j in range(3)) + (255,)
    m = Image.new("L", (ic, ic), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, ic - 1, ic - 1), radius=22, fill=255)
    icone = Image.new("RGBA", (ic, ic), (0, 0, 0, 0)); icone.paste(g, (0, 0), m); di = ImageDraw.Draw(icone)
    di.rounded_rectangle((16, 16, ic - 16, ic - 16), radius=15, outline=BRANCO, width=6)
    di.ellipse((27, 27, ic - 27, ic - 27), outline=BRANCO, width=6); di.ellipse((52, 21, 58, 27), fill=BRANCO)
    img.alpha_composite(icone, (x0 + px, y0 + py))
    bb = f.getbbox("S"); ty = round(y0 + Hh / 2 - (bb[1] + bb[3]) / 2); tx = x0 + px + ic + gap  # na altura do ícone
    d.text((tx, ty), pre, font=f, fill=BRANCO); d.text((tx + w1, ty), arroba, font=f, fill=OURO)
    if saida.lower().endswith(".mov"):
        return segue_clique(img, saida, dur)
    img.save(saida); print(img.size[1])


def segue_clique(base, saida, dur, FPS=30, W=1080, H=420, TOPO=246):
    """Pílula entra, afunda num toque e solta o balão de novo seguidor. Quadro 1080x420, pílula com topo em TOPO."""
    import math, subprocess, tempfile
    bb = base.getbbox(); pill = base.crop(bb); pw, ph = pill.size
    cx, cy = W / 2, TOPO + (bb[1] + bb[3]) / 2
    mola = lambda t, k=1.7: (t - 1) ** 2 * ((k + 1) * (t - 1) + k) + 1
    sai = lambda t: 1 - (1 - t) ** 3
    cl = lambda x: max(0.0, min(1.0, x))
    # balão de atividade do Instagram: vermelho, pessoa branca e "1", pontinha embaixo, sombra
    bw, ba = 176, 96
    bal = Image.new("RGBA", (bw + 60, ba + 86), (0, 0, 0, 0))
    ImageDraw.Draw(bal).rounded_rectangle((30, 40, bw + 30, ba + 40), radius=28, fill=(0, 0, 0, 110))
    bal = bal.filter(ImageFilter.GaussianBlur(12)); d = ImageDraw.Draw(bal)
    d.rounded_rectangle((30, 30, bw + 30, ba + 30), radius=28, fill=(255, 48, 64, 255))
    d.polygon([(bw / 2 + 12, ba + 29), (bw / 2 + 48, ba + 29), (bw / 2 + 30, ba + 52)], fill=(255, 48, 64, 255))
    d.ellipse((64, 46, 94, 76), fill=BRANCO); d.pieslice((52, 78, 106, 132), 180, 360, fill=BRANCO)
    d.text((126, 30 + ba / 2), "1", font=ImageFont.truetype(FONTE, 52), fill=BRANCO, anchor="lm")
    tmp = tempfile.mkdtemp(); T_TOQUE, T_BALAO = 0.75, 0.95
    for i in range(int(round(dur * FPS))):
        t = i / FPS; fr = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ov = ImageDraw.Draw(fr)
        k = mola(cl(t / 0.35)) if t < 0.35 else 1.0
        if T_TOQUE <= t < T_TOQUE + 0.22:
            k *= 1 - 0.06 * math.sin(math.pi * (t - T_TOQUE) / 0.22)
        if k > 0.02:
            p = pill.resize((max(1, int(pw * k)), max(1, int(ph * k))), Image.LANCZOS)
            if t < 0.15: p.putalpha(p.getchannel("A").point(lambda v: int(v * t / 0.15)))
            fr.alpha_composite(p, (int(cx - p.width / 2), int(cy - p.height / 2)))
        tx, ty = cx + 40, cy
        if T_TOQUE - 0.12 <= t < T_TOQUE + 0.25:  # dedo
            u = (t - T_TOQUE + 0.12) / 0.37; r = 34 - 8 * math.sin(math.pi * u)
            m = Image.new("RGBA", (W, H)); ImageDraw.Draw(m).ellipse((tx - r, ty - r, tx + r, ty + r), fill=(255, 255, 255, int(150 * math.sin(math.pi * u))))
            fr.alpha_composite(m)
        if T_TOQUE <= t < T_TOQUE + 0.5:  # anel dourado
            u = (t - T_TOQUE) / 0.5; r = 30 + 120 * sai(u)
            m = Image.new("RGBA", (W, H)); ImageDraw.Draw(m).ellipse((tx - r, ty - r, tx + r, ty + r), outline=OURO[:3] + (int(255 * (1 - u)),), width=6)
            fr.alpha_composite(m)
        if t >= T_BALAO:  # balão sobe e fica flutuando
            u = cl((t - T_BALAO) / 0.45); s = max(0.05, mola(u, 2.2))
            y = TOPO + bb[1] - bal.height + 20 - 40 * sai(u) + (4 * math.sin((t - T_BALAO) * 4) if u >= 1 else 0)
            b = bal.resize((max(1, int(bal.width * s)), max(1, int(bal.height * s))), Image.LANCZOS)
            fr.alpha_composite(b, (int(cx + pw / 2 - 150 + bal.width / 2 - b.width / 2), int(y + bal.height - b.height)))
        fr.save(f"{tmp}/f_{i:04d}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", f"{tmp}/f_%04d.png", "-c:v", "qtrle", saida], check=True)
    print(TOPO)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tipo", choices=["headline", "segue"]); ap.add_argument("texto"); ap.add_argument("saida")
    ap.add_argument("--destaque", default=""); ap.add_argument("--emoji", default="")
    ap.add_argument("--nutricao", action="store_true"); ap.add_argument("--dur", type=float, default=3.5)
    ap.add_argument("--emoji-inicio", action="store_true")
    a = ap.parse_args()
    if a.tipo == "headline":
        headline(a.texto, a.saida, a.destaque, a.emoji, VERDE if a.nutricao else OURO, inicio=a.emoji_inicio)
    else:
        segue(a.texto, a.saida, dur=a.dur)
