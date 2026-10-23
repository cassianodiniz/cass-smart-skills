#!/usr/bin/env python3
"""preparar VIDEO CORTES.json | verificar VIDEO.conferencia.json

Registra cobertura e versão de DECLARAÇÕES de escuta. Não ouve, não detecta
repetições e não comprova honestidade. Sem escuta direta, manter PENDENTE.
Usa só biblioteca padrão e ffmpeg/ffprobe; WAVs são recursos para revisão.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _ler(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _intervalo(value):
    if (not isinstance(value, list) or len(value) != 2 or
            any(isinstance(x, bool) or not isinstance(x, (int, float)) or
                not math.isfinite(x) for x in value) or not 0 <= value[0] < value[1]):
        raise ValueError("intervalo inválido: precisa [início, fim] finito e crescente")
    return value


def _geometria(plan):
    if not isinstance(plan, dict) or not plan.get("fonte"):
        raise ValueError("plano precisa identificar fonte")
    segs = plan.get("trechos_efetivos")
    if not isinstance(segs, list) or not segs:
        raise ValueError("plano sem trechos_efetivos")
    requested = plan.get("trechos_pedidos")
    if not isinstance(requested, list) or not requested:
        raise ValueError("plano sem trechos_pedidos")
    for seg in requested:
        _intervalo(seg)
    durations = plan.get("duracoes_saida")
    if "duracoes_saida" in plan and (not isinstance(durations, list) or len(durations) != len(segs)):
        raise ValueError("duracoes_saida precisa conter uma duração por trecho efetivo")
    trechos, cursor = [], 0
    timeline = []
    for i, seg in enumerate(segs):
        a, b = _intervalo(seg)
        length = b - a
        duration = durations[i] if durations is not None else length
        if (isinstance(duration, bool) or not isinstance(duration, (int, float)) or
                not math.isfinite(duration) or not length - 1e-9 <= duration <= length + 1 / 30 + 1e-9):
            raise ValueError("duração de saída inválida: deve preservar trecho e acrescentar até um quadro")
        end = cursor + duration
        timeline.append({"original": seg, "editado": [round(cursor, 6), round(end, 6)]})
        trechos.append({"id": f"trecho_{i + 1:03d}", **timeline[-1]})
        cursor = end
    if "timeline" in plan and plan["timeline"] != timeline:
        raise ValueError("timeline não corresponde aos trechos efetivos na ordem do plano")
    emendas = [{"id": f"emenda_{i:03d}",
                "editado": [round(max(0, t["editado"][0] - .7), 6),
                            round(min(cursor, t["editado"][0] + .7), 6)]}
               for i, t in enumerate(trechos[1:], 1)]
    return {"trechos": trechos, "emendas": emendas,
            "integral": {"id": "integral", "editado": [0, round(cursor, 6)]}}


def _duracao(video):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                             "-of", "csv=p=0", str(video)], check=True,
                            capture_output=True, text=True)
    return float(result.stdout.strip())


def _meta(path, base):
    return {"arquivo": os.path.relpath(path, base), "sha256": sha256(path)}


def _linhas(data):
    return data["trechos"] + data["emendas"] + [data["integral"]]


def preparar(video, cortes_json):
    """Cria sidecar PENDENTE e WAVs. Retorna Path; entrada inválida lança erro.

    Reexecutar substitui o sidecar: uma nova preparação exige nova declaração.
    """
    video, plano = Path(video).resolve(strict=True), Path(cortes_json).resolve(strict=True)
    report = video.with_suffix(".conferencia.json")
    base = report.parent
    plan = _ler(plano)
    geometria = _geometria(plan)
    duration = _duracao(video)
    if not math.isfinite(duration) or abs(duration - geometria["integral"]["editado"][1]) > .15:
        raise ValueError("duração do MP4 difere do plano de cortes (tolerância 0,15 s)")
    geometria["integral"]["editado"][1] = duration  # inclui eventual arredondamento do último frame
    chosen = plan.get("textos_escolhidos", [""] * len(geometria["trechos"]))
    if (not isinstance(chosen, list) or len(chosen) != len(geometria["trechos"]) or
            any(not isinstance(text, str) for text in chosen)):
        raise ValueError("textos_escolhidos deve conter um texto por trecho efetivo")
    for row, text in zip(geometria["trechos"], chosen):
        row["esperado"] = text
    data = {"schema": 1, "status": "PENDENTE",
            "limite": "Valida cobertura/versionamento da declaração; não comprova audição real.",
            "video": _meta(video, base), "plano": _meta(plano, base), **geometria}
    audio_dir = video.with_name(video.stem + "_conferencia")
    audio_dir.mkdir(exist_ok=True)
    for row in _linhas(data):
        audio = audio_dir / (row["id"] + ".wav")
        a, b = row["editado"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-ss", str(a),
                        "-t", str(b - a), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
                        "-c:a", "pcm_s16le", str(audio)], check=True, capture_output=True)
        row.update(audio=_meta(audio, base), resultado="pendente", observado="", metodo="",
                   evidencia={"recurso": os.path.relpath(audio, base), "registro": ""})
    if sha256(video) != data["video"]["sha256"] or sha256(plano) != data["plano"]["sha256"]:
        raise ValueError("MP4 ou plano mudou durante preparação; prepare novamente")
    report.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def verificar(relatorio):
    """Retorna lista de pendências; [] significa declaração completa, não audição provada."""
    erros = []
    try:
        report = Path(relatorio).resolve(strict=True)
        base, data = report.parent, _ler(report)
        if data.get("schema") != 1:
            raise ValueError("schema desconhecido")
        for key in ("video", "plano"):
            meta = data[key]
            path = (base / meta["arquivo"]).resolve(strict=True)
            if sha256(path) != meta["sha256"]:
                erros.append(f"{key}: hash mudou; prepare nova conferência")
        video = (base / data["video"]["arquivo"]).resolve(strict=True)
        geometry = _geometria(_ler(base / data["plano"]["arquivo"]))
        duration = _duracao(video)
        if not math.isfinite(duration) or abs(duration - geometry["integral"]["editado"][1]) > .15:
            erros.append("duração difere do plano")
        geometry["integral"]["editado"][1] = duration
        if data.get("status") != "DECLARACAO_COMPLETA":
            erros.append("status PENDENTE: declaração de escuta incompleta")
        for key in ("trechos", "emendas"):
            if not isinstance(data.get(key), list) or len(data[key]) != len(geometry[key]):
                raise ValueError(f"{key}: cobertura incompleta")
        expected = _linhas(geometry)
        rows = _linhas(data)
        for row, target in zip(rows, expected):
            label = target["id"]
            if any(row.get(k) != v for k, v in target.items()):
                erros.append(f"{label}: cobertura/tempos alterados")
            if label.startswith("trecho_"):
                text = row.get("esperado")
                if not isinstance(text, str) or not text.strip():
                    erros.append(f"{label}: falta texto literal esperado escolhido antes da revisão")
            if row.get("resultado") != "aprovado" or row.get("metodo") != "escuta_direta":
                erros.append(f"{label}: exige resultado aprovado e método escuta_direta")
            observed = row.get("observado")
            if not isinstance(observed, str) or not observed.strip():
                erros.append(f"{label}: falta texto literal/comentário observado")
            audio = row["audio"]
            expected_audio = video.with_name(video.stem + "_conferencia") / (label + ".wav")
            actual = (base / audio["arquivo"]).resolve(strict=True)
            if actual != expected_audio or sha256(actual) != audio["sha256"]:
                erros.append(f"{label}: recurso de áudio trocado")
            evidence = row.get("evidencia", {})
            registro = evidence.get("registro")
            if (evidence.get("recurso") != audio["arquivo"] or
                    not isinstance(registro, str) or not registro.strip()):
                erros.append(f"{label}: falta recurso + registro do que foi conferido")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as exc:
        erros.append(f"conferência inválida/incompleta: {exc}")
    return erros


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)
    prep = sub.add_parser("preparar")
    prep.add_argument("video")
    prep.add_argument("cortes_json")
    check = sub.add_parser("verificar")
    check.add_argument("relatorio")
    args = parser.parse_args()
    if args.comando == "verificar":
        errors = verificar(args.relatorio)
        print("\n".join(errors) if errors else
              "Declaração completa para estes arquivos; o programa não comprova a escuta.")
        return int(bool(errors))
    try:
        print(preparar(args.video, args.cortes_json))
        print("PENDENTE: WAVs preparados; ainda falta escuta direta e registro.")
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"Não foi possível preparar: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
