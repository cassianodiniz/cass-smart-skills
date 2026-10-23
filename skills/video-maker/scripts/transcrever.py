#!/usr/bin/env python3
"""Transcreve um vídeo (ou um trecho) com o Whisper MLX local, palavra por palavra.

    python3 transcrever.py <video> <saida.json> [--inicio S] [--fim S]

Saídas:
- <saida.json>: {"fonte", "inicio", "fim", "palavras": [{"w","s","e"}], "segmentos": [{"s","e","texto"}]}
  com tempos no relógio do vídeo original (o --inicio já vem somado).
- <saida.md>: a mesma fala em blocos com [mm:ss], para ler e escolher trechos.

O JSON também guarda whisper_bruto, avisos e conferencias para investigar diferenças.
Reutiliza o mesmo arquivo/trecho somente na versão atual do processamento.
"""
import argparse, json, math, os, shutil, subprocess, sys, tempfile

MODELO = "mlx-community/whisper-large-v3-turbo" if shutil.which("mlx_whisper") else "faster-whisper/turbo"
VERSAO_PROCESSAMENTO = 2


def assinatura(video):
    st = os.stat(video)
    return {"tamanho": st.st_size, "mtime": int(st.st_mtime)}


def mmss(t):
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60:02d}:{t % 60:02d}"


def escrever_md(dados, caminho):
    linhas = [f"# Transcrição: {os.path.basename(dados['fonte'])}", ""]
    for s in dados["segmentos"]:
        linhas.append(f"[{mmss(s['s'])}] {s['texto']}")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas) + "\n")


def achar_travadas(segmentos, min_blocos=4, min_seg=20):
    """Trechos em que o Whisper entrou em laço: blocos curtos e repetidos ("É...", "E aí")
    por 20 s ou mais. Em aula longa isso esconde minutos de fala real (visto em 12/10/2026)."""
    travadas, i = [], 0
    while i < len(segmentos):
        j = i
        while j < len(segmentos) and len(segmentos[j]["texto"].split()) <= 3:
            j += 1
        bloco = segmentos[i:j]
        if (len(bloco) >= min_blocos and bloco[-1]["e"] - bloco[0]["s"] >= min_seg
                and len({b["texto"].lower() for b in bloco}) <= 2):
            travadas.append((bloco[0]["s"], bloco[-1]["e"]))
        i = max(j, i + 1)
    return travadas


def transcrever(video, saida, inicio=None, fim=None, forcar=False, conferir=True):
    video = os.path.abspath(video)
    if not os.path.exists(video):
        sys.exit(f"não achei o vídeo: {video}")
    assin = assinatura(video)
    if os.path.exists(saida) and not forcar:
        with open(saida, encoding="utf-8") as arquivo:
            d = json.load(arquivo)
        if (d.get("assinatura") == assin and d.get("inicio") == inicio
                and d.get("fim_pedido") == fim and d.get("modelo") == MODELO
                and d.get("versao_processamento") == VERSAO_PROCESSAMENTO
                and d.get("conferir") == conferir):
            print(f"transcrição já existe, reaproveitando: {saida}")
            return d
    mlx = shutil.which("mlx_whisper")
    comando_whisper = [mlx] if mlx else [sys.executable, os.path.join(os.path.dirname(__file__), "whisper_local.py")]
    print("Transcrição local: " + ("Whisper MLX" if mlx else "faster-whisper CPU int8") + " · large-v3-turbo")

    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "voz.wav")
        cmd = ["ffmpeg", "-v", "error", "-y"]
        if inicio:
            cmd += ["-ss", str(inicio)]
        cmd += ["-i", video]
        if fim is not None:
            cmd += ["-t", str(fim - (inicio or 0))]
        cmd += ["-vn", "-ac", "1", "-ar", "16000", wav]
        subprocess.run(cmd, check=True)
        # Mesmas opções da video-ads-machine. Não ligue --condition-on-previous-text False:
        # testado em 10/10/2026, ele "formaliza" a fala ("pro" vira "para o", "tá" vira
        # "está") e chega a pular palavra. A alucinação do fim é tratada abaixo.
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "csv=p=0", wav], capture_output=True, text=True).stdout)
        r = subprocess.run(comando_whisper + [wav, "--model", MODELO, "--language", "pt", "--task", "transcribe",
                            "--word-timestamps", "True",
                            "--output-format", "json", "--output-dir", tmp],
                           capture_output=True, text=True)
        bruto_p = os.path.join(tmp, "voz.json")
        if r.returncode != 0 or not os.path.exists(bruto_p):
            sys.exit("a transcrição falhou: " + (r.stderr or r.stdout or "")[-600:])
        with open(bruto_p, encoding="utf-8") as arquivo:
            bruto = json.load(arquivo)

    off = inicio or 0.0
    palavras, segmentos, avisos, conferencias, ultimo = [], [], [], [], None
    for numero, seg in enumerate(bruto.get("segments", [])):
        texto = seg.get("text", "").strip()
        # Texto igual pode ser uma nova tentativa real. Igualdade sinaliza revisão,
        # nunca autoriza apagar fala; só o tempo delimita o que cabe no áudio.
        if texto and texto == ultimo:
            avisos.append({"tipo": "repeticao_consecutiva", "segmento": numero,
                           "mensagem": "Texto repetido preservado; conferir no áudio."})
        ultimo = texto
        ws, ajustado = [], False
        for w in seg.get("words", []):
            if not w["word"].strip():
                continue
            s, e = w["start"], w["end"]
            if not (math.isfinite(s) and math.isfinite(e) and e >= s and e >= 0 and s < dur):
                avisos.append({"tipo": "tempo_fora_do_audio", "segmento": numero,
                               "palavra": w, "mensagem": "Palavra sem intervalo válido no áudio; veja whisper_bruto."})
                ajustado = True
                continue
            ini, fi = max(0., s), min(dur, e)
            if ini == fi:
                avisos.append({"tipo": "tempo_ambiguo", "segmento": numero, "palavra": w,
                               "mensagem": "Palavra preservada com duração zero; conferir no áudio."})
            if (ini, fi) != (s, e):
                avisos.append({"tipo": "tempo_limitado_ao_audio", "segmento": numero,
                               "palavra": w, "mensagem": "Tempo limitado à duração real do áudio."})
                ajustado = True
            ws.append({"w": w["word"].strip(), "s": round(ini + off, 3), "e": round(fi + off, 3)})
        if not ws:
            continue
        palavras += ws
        if ajustado:
            texto = " ".join(w["w"] for w in ws)
        segmentos.append({"s": ws[0]["s"], "e": ws[-1]["e"], "texto": texto})
    if not palavras:
        sys.exit("o Whisper não devolveu nenhuma palavra com tempo")

    # Whisper às vezes trava num trecho e repete "É..." por minutos com fala real por baixo.
    # A segunda leitura pode recuperar fala. Ambas ficam registradas: repetição
    # persistente não prova silêncio, e precisa ser conferida no áudio.
    if conferir:
        for s, e in achar_travadas(segmentos):
            ini, fi = max(off, s - 10), min(off + dur, e + 10)
            aviso = {"tipo": "possivel_travada", "s": s, "e": e,
                     "mensagem": "Sequência repetida; comparar as duas leituras com o áudio."}
            avisos.append(aviso)
            registro = {"inicio": ini, "fim": fi,
                        "segmentos_anteriores": [x for x in segmentos if ini <= x["s"] < fi],
                        "palavras_anteriores": [p for p in palavras if ini <= p["s"] < fi]}
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    novo = transcrever(video, os.path.join(tmp, "t.json"), ini, fi, conferir=False)
            except SystemExit as erro:
                registro.update(estado="sem_resultado", erro=str(erro))
                conferencias.append(registro)
                print(f"aviso: rechecagem em {mmss(s)}–{mmss(e)} sem resultado; fala original preservada")
                continue
            registro.update({chave: novo[chave] for chave in ("whisper_bruto", "palavras", "segmentos", "avisos")})
            conferencias.append(registro)
            if achar_travadas(novo["segmentos"]):
                registro["estado"] = "persistente"
                print(f"aviso: {mmss(s)}–{mmss(e)} continua só com 'É...'; pode ser silêncio, confira")
                continue
            registro["estado"] = "recuperada"
            palavras = sorted([p for p in palavras if not ini <= p["s"] < fi] + novo["palavras"], key=lambda p: p["s"])
            segmentos = sorted([x for x in segmentos if not ini <= x["s"] < fi] + novo["segmentos"], key=lambda x: x["s"])
            print(f"travada em {mmss(s)}–{mmss(e)} refeita")

    dados = {"fonte": video, "assinatura": assin, "inicio": inicio, "fim_pedido": fim,
             "modelo": MODELO, "versao_processamento": VERSAO_PROCESSAMENTO, "conferir": conferir,
             "palavras": palavras, "segmentos": segmentos, "whisper_bruto": bruto,
             "avisos": avisos, "conferencias": conferencias}
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=0)
    escrever_md(dados, os.path.splitext(saida)[0] + ".md")
    print(f"{len(palavras)} palavras, {len(segmentos)} blocos -> {saida}")
    return dados


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("saida")
    ap.add_argument("--inicio", type=float)
    ap.add_argument("--fim", type=float)
    ap.add_argument("--forcar", action="store_true", help="transcreve mesmo se já existir")
    a = ap.parse_args()
    transcrever(a.video, a.saida, a.inicio, a.fim, a.forcar)
