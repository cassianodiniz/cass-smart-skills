#!/usr/bin/env python3
"""Junta os trechos escolhidos de uma gravação bruta (várias tentativas da mesma frase).

    python3 cortar_trechos.py <video> <saida.mp4> '[[ini,fim], ...]' [--solto] [--espelhar]

- Os trechos vêm em segundos do vídeo original, na ordem em que entram no reel (um trecho de antes
  pode vir depois de um de depois).
- Por padrão cada trecho é colado na voz: começa 0,03 s antes da primeira sílaba, termina
  0,08 s depois da última e perde respiração e pausa de 0,2 s ou mais. --solto corta
  exatamente nos tempos dados.
- --espelhar desinverte a imagem (câmera frontal com espelhamento ligado).
- Vídeo HDR do iPhone (HLG) é convertido pra cor comum sem lavar a pele.
- Sai em 1080x1920, 30 qps. No fim transcreve o resultado em <saida>.json e .md para conferir.
"""
import argparse, json, math, os, subprocess, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transcrever import transcrever

VOZ_DB, PRE, POS, PAUSA, JUNTA = -42, 0.03, 0.12, 0.20, 0.25  # POS 0.12: o "s" final é chiado fraco
HDR = ("zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,"
       "zscale=p=bt709,tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,")


def eh_hdr(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=color_transfer", "-of", "csv=p=0", video], capture_output=True, text=True)
    return "arib-std-b67" in r.stdout


def validar_trechos(trechos):
    if not trechos:
        raise ValueError("nenhum trecho selecionado")
    for par in trechos:
        if (len(par) != 2 or not all(isinstance(t, (int, float)) and math.isfinite(t) for t in par)
                or par[0] < 0 or par[1] <= par[0]):
            raise ValueError(f"intervalo inválido: {par!r}")


def colar(video, trechos):
    """Recorta cada trecho para onde há voz (acima de -42 dB; respiração fica em -50 a -60)."""
    validar_trechos(trechos)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-map", "0:a:0", "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32); H = 160  # janelas de 10 ms
    n = len(x) // H
    voz = 20 * np.log10(np.sqrt((x[:n * H].reshape(n, H) ** 2).mean(1)) + 1e-9) > VOZ_DB
    out = []
    for a, b in trechos:
        # Uma janela nova é uma decisão editorial. Nunca atravessar a exclusão
        # entre duas janelas, mesmo que seja menor que JUNTA.
        inicio_janela = len(out)
        i0 = int(a * 100); v = voz[i0:int(b * 100)]; regs, k = [], 0
        while k < len(v):
            if not v[k]:
                k += 1; continue
            j = k
            while j < len(v) and v[j]:
                j += 1
            if j - k >= 4:  # estalo de menos de 40 ms não é voz
                if regs and (i0 + k) / 100 - regs[-1][1] < PAUSA:
                    regs[-1][1] = (i0 + j) / 100
                else:
                    regs.append([(i0 + k) / 100, (i0 + j) / 100])
            k = j
        for s, e in regs:
            s, e = max(a, s - PRE), min(b, e + POS)
            if len(out) > inicio_janela and 0 <= s - out[-1][1] < JUNTA:
                out[-1][1] = e
            else:
                out.append([s, e])
    return [[round(s, 3), round(e, 3)] for s, e in out]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video"); p.add_argument("saida"); p.add_argument("trechos")
    p.add_argument("--solto", action="store_true"); p.add_argument("--espelhar", action="store_true")
    a = p.parse_args()
    segs = json.loads(a.trechos)
    validar_trechos(segs)
    pedidos = [list(p) for p in segs]
    if not a.solto:
        segs = colar(a.video, segs)
    if not segs:
        sys.exit("nenhum trecho com voz; não foi gerado vídeo")
    fl = ",hflip" if a.espelhar else ""
    cor = HDR if eh_hdr(a.video) else ""
    pv, pa, duracoes_saida = [], [], []
    for i, (s, e) in enumerate(segs):
        # Cada trecho precisa terminar na grade de 30 quadros/s ANTES do concat.
        # O preenchimento repete só o último quadro e acrescenta silêncio: nunca
        # amplia a janela original nem traz de volta um intervalo excluído.
        # Epsilon evita quadro extra por erro de ponto flutuante em e-s == n/30.
        quadros = max(1, math.ceil((e - s) * 30 - 1e-9))
        duracao = quadros / 30
        duracoes_saida.append(duracao)
        pv.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS,fps=30,"
                  f"tpad=stop_mode=clone:stop_duration={duracao},trim=end_frame={quadros},"
                  f"setpts=N/(30*TB),{cor}scale=1080:1920:flags=lanczos,setsar=1{fl}[v{i}]")
        pa.append(f"[0:a:0]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,"
                  f"afade=t=in:d=0.02,afade=t=out:st={max(0, e - s - 0.03):.6f}:d=0.03,"
                  f"apad=whole_dur={duracao},atrim=duration={duracao}[a{i}]")
    fc = ";".join(pv + pa) + ";" + "".join(f"[v{i}][a{i}]" for i in range(len(segs))) \
        + f"concat=n={len(segs)}:v=1:a=1[v][a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "30",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.saida], check=True)
    print(f"trechos usados: {json.dumps(segs)}")
    # Renderizar não aprova a fala. A revisão se refere a estes bytes e cortes.
    cortes_p = os.path.splitext(a.saida)[0] + ".cortes.json"
    cursor, timeline = 0.0, []
    for (s, e), duracao in zip(segs, duracoes_saida):
        timeline.append({"original": [s, e], "editado": [round(cursor, 6), round(cursor + duracao, 6)]})
        cursor += duracao
    with open(cortes_p, "w", encoding="utf-8") as f:
        json.dump({"fonte": os.path.abspath(a.video), "video": os.path.abspath(a.saida),
                   "trechos_pedidos": pedidos, "trechos_efetivos": segs,
                   "duracoes_saida": duracoes_saida, "timeline": timeline}, f, ensure_ascii=False, indent=2)
    from conferencia_fala import preparar
    revisao = preparar(a.saida, cortes_p)
    print(f"RASCUNHO: revisão da fala pendente em {revisao}")
    j = os.path.splitext(a.saida)[0] + ".json"
    transcrever(a.saida, j, forcar=True)
    with open(os.path.splitext(a.saida)[0] + ".md", encoding="utf-8") as arquivo:
        print(arquivo.read())


if __name__ == "__main__":
    main()
