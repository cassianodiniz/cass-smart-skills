#!/usr/bin/env python3
"""Monta o reel de tela dividida a partir de um plano em JSON. Uma passada só de ffmpeg.

    python3 montar.py plano.json

Plano (tempos em segundos do reel, que começa em `fala_inicio` do vídeo da fala):
{
  "fala": "/caminho/fala.mp4",          # quem fala: vai embaixo (e em tela cheia)
  "fala_inicio": 0,                     # opcional: de onde começa no vídeo da fala
  "fim": 37.08,                         # duração do reel
  "foco_x": 0.5,                        # opcional, fala horizontal: centro do rosto (0 = esquerda, 1 = direita)
  "corte_fala": "1080:960:0:170",       # opcional: crop do painel de baixo (senão, automático)
  "cenas": [                            # metade de cima, em sequência, cobrindo todo o tempo dividido
    {"arquivo": "tela 1.mov", "ss": 3.7, "dur": 3.4, "corte": "1080:960:0:760"},
    {"arquivo": "picole.mp4", "ss": 5.8, "dur": 2.0, "foco_y": 0.45},   # sem corte: centro, com foco vertical
    {"arquivo": "motion.mp4", "dur": 7.2}
  ],
  "tela_cheia": [[27.9, 37.08]],        # opcional: trechos com a fala ocupando a tela toda
  "efeitos": [{"de": 12.0, "ate": 14.5, "zoom": 1.3, "pb": true}],   # opcional, na fala
                                        # zoom que anda: "zoom": [1.30, 1.48], "centro": [590, 1090] (px da fala)
  "foco_y_fala": 0.35,                  # opcional: altura do rosto, para o zoom
  "legenda": "legenda.ass",             # opcional: queima a legenda na mesma passada
  "sobreposicoes": [                    # opcional, por cima de tudo (antes da legenda): headline, motion em
    {"arquivo": "headline.png", "de": 0, "ate": 3.5, "y": 882},          # tela cheia, pílula do final.
    {"arquivo": "motion_cheio.mp4", "de": 25.3, "ate": 29.6}             # PNG entra com fade (no zero, sem); vídeo começa em "de"
  ],
  "saida": "reel.mp4"
}
Caminhos relativos são lidos a partir da pasta do plano.
"""
import json, os, shutil, subprocess, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(AQUI), "fonts")
W, H, TOP = 1080, 1920, 960


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,color_transfer:stream_side_data=rotation", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    w, h = s["width"], s["height"]
    rot = next((abs(int(d.get("rotation", 0))) for d in s.get("side_data_list", []) if "rotation" in d), 0)
    probe.hdr = s.get("color_transfer") == "arib-std-b67"   # iPhone grava em HDR (HLG)
    return (h, w) if rot in (90, 270) else (w, h)


def intervalos(fim, cheia):
    """Divide [0, fim] em pedaços ('div' ou 'cheia'), em ordem."""
    pts, t = [], 0.0
    for a, b in sorted(cheia):
        a, b = max(0.0, a), min(fim, b)
        if a > t + 1e-3:
            pts.append(("div", t, a))
        if b > a:
            pts.append(("cheia", a, b))
        t = max(t, b)
    if t < fim - 1e-3:
        pts.append(("div", t, fim))
    return pts


def main():
    plano_p = os.path.abspath(sys.argv[1])
    base = os.path.dirname(plano_p)
    P = json.load(open(plano_p, encoding="utf-8"))
    cam = lambda p: p if os.path.isabs(p) else os.path.join(base, p)

    fala, fim = cam(P["fala"]), float(P["fim"])
    pedacos = intervalos(fim, P.get("tela_cheia", []))
    t_div = sum(b - a for k, a, b in pedacos if k == "div")
    t_cenas = sum(float(c["dur"]) for c in P.get("cenas", []))
    if abs(t_div - t_cenas) > 0.05:
        sys.exit(f"as cenas somam {t_cenas:.2f}s, mas o tempo de tela dividida é {t_div:.2f}s. "
                 "Ajuste as durações para fecharem.")

    sw, sh = probe(fala)
    fx = float(P.get("foco_x", 0.5))
    if P.get("corte_fala"):
        crop_div = P["corte_fala"]
    elif sh >= sw:            # fala vertical: largura toda, recorte "de peito"
        ch = round(sw * TOP / W)
        crop_div = f"{sw}:{ch}:0:{min(round(sh * 0.0885), sh - ch)}"
    else:                     # fala horizontal: fatia 1080:960 em volta do rosto
        cw = min(sw, round(sh * W / TOP))
        crop_div = f"{cw}:{sh}:{round((sw - cw) * fx)}:0"
    if sh >= sw:
        cw = min(sw, round(sh * W / H)); crop_cheia = f"{cw}:{min(sh, round(cw * H / W))}:{(sw - cw) // 2}:0"
    else:
        cw = round(sh * W / H); crop_cheia = f"{cw}:{sh}:{round((sw - cw) * fx)}:0"

    args = ["ffmpeg", "-v", "error", "-y",
            "-ss", str(P.get("fala_inicio", 0)), "-t", f"{fim:.3f}", "-i", fala]
    f = []

    # fala, com efeitos (zoom, preto e branco) aplicados por trecho
    efs = sorted(P.get("efeitos", []), key=lambda e: e["de"])
    cortes = sorted({0.0, fim, *[min(fim, max(0.0, x)) for e in efs for x in (e["de"], e["ate"])]})
    fy = float(P.get("foco_y_fala", 0.35))
    fala_partes = []
    for i, (a, b) in enumerate(zip(cortes, cortes[1:])):
        e = next((e for e in efs if e["de"] <= a + 1e-3 and e["ate"] >= b - 1e-3), None)
        cadeia = f"trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS"
        if e and isinstance(e.get("zoom"), list):        # zoom que anda, liso: amplia 4x e usa zoompan
            z0, z1 = map(float, e["zoom"]); cx, cy = e.get("centro", [sw / 2, sh / 2])
            nq = max(1, round((b - a) * 30) - 1)
            cadeia += (f",scale={sw * 4}:{sh * 4}:flags=lanczos,zoompan=z='{z0}+{z1 - z0}*on/{nq}':"
                       f"x='{cx}*4-iw/zoom/2':y='{cy}*4-ih/zoom/2':d=1:s={sw}x{sh}:fps=30")
        elif e and e.get("zoom", 1) != 1:
            z = float(e["zoom"])
            cadeia += f",scale=trunc(iw*{z}/2)*2:-2,crop={sw}:{sh}:(iw-{sw})*{fx}:(ih-{sh})*{fy}"
        if e and e.get("pb"):
            cadeia += ",hue=s=0"
        fala_partes.append(f"[fz{i}]")
        f.append(f"[fs{i}]{cadeia}[fz{i}]")
    n = len(fala_partes)
    hdr = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,"
           "zscale=p=bt709,tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,") if probe.hdr else ""
    f.insert(0, f"[0:v]{hdr}fps=30,setsar=1,scale={sw}:{sh},split={n}" + "".join(f"[fs{i}]" for i in range(n)))
    f.append("".join(fala_partes) + f"concat=n={n}:v=1:a=0[fala]")

    # cenas da metade de cima
    tops = []
    for j, c in enumerate(P.get("cenas", [])):
        d = float(c["dur"])
        if "ss" in c:
            args += ["-ss", str(c["ss"])]
        args += ["-t", f"{d + 1:.3f}", "-i", cam(c["arquivo"])]
        if c.get("corte"):
            crop = f"crop={c['corte']}"
        else:
            fyc = float(c.get("foco_y", 0.5)); fxc = float(c.get("foco_x", 0.5))
            crop = (f"crop='min(iw,ih*{W}/{TOP})':'min(ih,iw*{TOP}/{W})':"
                    f"'(iw-ow)*{fxc}':'(ih-oh)*{fyc}'")
        f.append(f"[{j + 1}:v]fps=30,{crop},scale={W}:{TOP}:flags=lanczos,setsar=1,"
                 f"tpad=stop_mode=clone:stop_duration={d:.3f},trim=duration={d:.3f},setpts=PTS-STARTPTS[c{j}]")
        tops.append(f"[c{j}]")
    if tops:
        f.append("".join(tops) + f"concat=n={len(tops)}:v=1:a=0[top]")

    # pedaços: dividido (cima + baixo + degradê na emenda) ou tela cheia
    ndiv = sum(1 for k, *_ in pedacos if k == "div")
    f.append(f"[fala]split={len(pedacos)}" + "".join(f"[s{i}]" for i in range(len(pedacos))))
    if ndiv:
        f.append(f"[top]split={ndiv}" + "".join(f"[t{i}]" for i in range(ndiv)))
    saidas, cur, ti = [], 0.0, 0
    for i, (k, a, b) in enumerate(pedacos):
        L = b - a
        f.append(f"[s{i}]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[r{i}]")
        if k == "div":
            f.append(f"[r{i}]crop={crop_div},scale={W}:{TOP}:flags=lanczos,setsar=1[b{i}]")
            f.append(f"[t{ti}]trim=start={cur:.3f}:end={cur + L:.3f},setpts=PTS-STARTPTS[u{i}]")
            f.append(f"color=c=black:s={W}x90:r=30:d={L:.3f},format=rgba,"
                     f"geq=r=0:g=0:b=0:a='255*0.62*pow(Y/89,1.6)'[g{i}]")
            f.append(f"[u{i}][b{i}]vstack[v{i}];[v{i}][g{i}]overlay=0:{TOP - 90}:shortest=1[p{i}]")
            cur += L; ti += 1
        else:
            f.append(f"[r{i}]crop={crop_cheia},scale={W}:{H}:flags=lanczos,setsar=1[p{i}]")
        saidas.append(f"[p{i}]")
    final = "".join(saidas) + f"concat=n={len(saidas)}:v=1:a=0,format=yuv420p"
    for k, s in enumerate(P.get("sobreposicoes", [])):
        de, ate, y = float(s["de"]), float(s["ate"]), int(s.get("y", 0))
        idx = args.count("-i")
        if s["arquivo"].lower().endswith(".png"):
            args += ["-loop", "1", "-t", f"{fim:.3f}", "-i", cam(s["arquivo"])]
            entra = f"fade=t=in:st={de:.3f}:d=0.15:alpha=1," if de > 0 else ""  # no zero já aparece inteira
            f.append(f"[{idx}:v]format=rgba,{entra}"
                     f"fade=t=out:st={ate - 0.14:.3f}:d=0.14:alpha=1[o{k}]")
        else:
            args += ["-i", cam(s["arquivo"])]
            f.append(f"[{idx}:v]setpts=PTS-STARTPTS+{de:.3f}/TB[o{k}]")
        f.append(final + f"[sb{k}]")
        final = f"[sb{k}][o{k}]overlay=0:{y}:enable='between(t,{de:.3f},{ate:.3f})':eof_action=pass"

    tmp = tempfile.mkdtemp(prefix="montar_")
    if P.get("legenda"):
        ass = os.path.join(tmp, "legenda.ass")       # caminho sem espaço nem dois-pontos pro filtro
        shutil.copy(cam(P["legenda"]), ass)
        shutil.copytree(FONTS, os.path.join(tmp, "fontes"))
        final += ",ass=legenda.ass:fontsdir=fontes"
    f.append(final + "[vout]")
    f.append(f"[0:a]atrim=0:{fim:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={max(0, fim - 0.1):.3f}:d=0.1[aout]")

    saida = cam(P["saida"])
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    args += ["-filter_complex", ";".join(f), "-map", "[vout]", "-map", "[aout]",
             "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-r", "30",
             "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", saida]
    open(os.path.join(tmp, "comando.txt"), "w", encoding="utf-8").write(" ".join(args))
    subprocess.run(args, check=True, cwd=tmp)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", saida],
                         capture_output=True, text=True).stdout.strip()
    print(f"pronto: {saida} ({float(dur):.2f}s, esperado {fim:.2f}s)")


if __name__ == "__main__":
    main()
