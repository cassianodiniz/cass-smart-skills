"""Regressões do processamento; MLX/ffmpeg controlados, sem GPU ou modelo baixado.

TRANSCRICAO_SCRIPT permite executar os mesmos casos contra uma cópia congelada.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(os.environ.get("TRANSCRICAO_SCRIPT", Path(__file__).with_name("transcrever.py")))
spec = importlib.util.spec_from_file_location("transcrever_em_teste", SCRIPT)
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)


def segmento(texto, inicio, fim, palavras=None):
    return {"start": inicio, "end": fim, "text": " " + texto,
            "words": palavras or [{"word": " " + texto, "start": inicio, "end": fim}]}


class TranscricaoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.video = Path(self.tmp.name) / "fala.wav"
        self.video.write_bytes(b"audio controlado no teste")
        self.saida = Path(self.tmp.name) / "fala.json"
        self.chamadas_mlx = []

    def executar(self, bruto, dur=4.0, **opcoes):
        respostas = list(bruto) if isinstance(bruto, list) else [bruto]

        def rodar(args, **kwargs):
            if args[0] == "ffprobe":
                return subprocess.CompletedProcess(args, 0, str(dur), "")
            if args[0] == "whisper-teste":
                self.chamadas_mlx.append(args)
                pasta = Path(args[args.index("--output-dir") + 1])
                resposta = respostas.pop(0) if len(respostas) > 1 else respostas[0]
                (pasta / "voz.json").write_text(json.dumps(resposta), encoding="utf-8")
            else:
                self.assertEqual(args[0], "ffmpeg")
            return subprocess.CompletedProcess(args, 0, "", "")

        with patch.object(modulo.shutil, "which", return_value="whisper-teste"), \
                patch.object(modulo.subprocess, "run", side_effect=rodar):
            return modulo.transcrever(str(self.video), str(self.saida), **opcoes)

    def test_preserva_duas_tentativas_iguais_do_diagnostico(self):
        bruto = {"segments": [segmento("Um carrossel", .2, .8),
                              segmento("Um carrossel", 1.4, 2.0),
                              segmento("bem escrito", 2.1, 2.5)]}
        dados = self.executar(bruto)
        self.assertEqual([s["texto"] for s in dados["segmentos"]],
                         ["Um carrossel", "Um carrossel", "bem escrito"])
        self.assertEqual([p["s"] for p in dados["palavras"]], [.2, 1.4, 2.1])
        self.assertTrue(any(a["tipo"] == "repeticao_consecutiva" for a in dados["avisos"]))

    def test_preserva_palavras_repetidas_dentro_de_um_segmento(self):
        bruto = {"segments": [segmento("não não", .2, .8, [
            {"word": " não", "start": .2, "end": .4},
            {"word": " não", "start": .5, "end": .8}])]}
        dados = self.executar(bruto)
        self.assertEqual([p["w"] for p in dados["palavras"]], ["não", "não"])

    def test_tempo_de_duracao_zero_e_ambiguo_sem_apagar_palavra(self):
        bruto = {"segments": [segmento("não não", .2, .8, [
            {"word": " não", "start": .2, "end": .4},
            {"word": " não", "start": .5, "end": .5}])]}
        dados = self.executar(bruto)
        self.assertEqual([p["w"] for p in dados["palavras"]], ["não", "não"])
        self.assertTrue(any(a["tipo"] == "tempo_ambiguo" for a in dados["avisos"]))

    def test_preserva_palavra_valida_nos_ultimos_200ms(self):
        dados = self.executar({"segments": [segmento("abre", .2, .8),
                                             segmento("fim", 3.9, 4.0)]})
        self.assertEqual([p["w"] for p in dados["palavras"]], ["abre", "fim"])

    def test_limita_tempos_a_duracao_real_antes_de_somar_inicio(self):
        bruto = {"segments": [segmento("fora entra termina fantasma", 0, 6, [
            {"word": " fora", "start": -2., "end": -1.},
            {"word": " entra", "start": -.1, "end": .2},
            {"word": " termina", "start": 3.8, "end": 4.2},
            {"word": " fantasma", "start": 5., "end": 6.}]),
            segmento("depois do fim", 4.1, 5.)]}
        dados = self.executar(bruto, inicio=10, fim=14)
        self.assertEqual(dados["palavras"], [{"w": "entra", "s": 10., "e": 10.2},
                                            {"w": "termina", "s": 13.8, "e": 14.}])
        self.assertEqual(dados["segmentos"][0]["texto"], "entra termina")
        self.assertTrue(dados["avisos"])

    def test_guarda_saida_whisper_inteira_sem_mudar_a_fonte(self):
        bruto = {"language": "pt", "text": " repetição repetição", "segments": [
            segmento("repetição", .2, .8), segmento("repetição", 1.4, 2.0),
            segmento("alucinação após o fim", 7., 8.)]}
        original = copy.deepcopy(bruto)
        dados = self.executar(bruto)
        self.assertEqual(dados.get("whisper_bruto"), original)
        salvo = json.loads(self.saida.read_text(encoding="utf-8"))
        self.assertEqual(salvo["whisper_bruto"], original)
        self.assertEqual(bruto, original)

    def test_nao_reaproveita_cache_sem_versao_ou_de_versao_antiga(self):
        for versao in (None, -1):
            with self.subTest(versao=versao):
                antigo = {"assinatura": modulo.assinatura(self.video), "inicio": None,
                          "fim_pedido": None, "palavras": [{"w": "cache que perdeu fala"}]}
                if versao is not None:
                    antigo["versao_processamento"] = versao
                self.saida.write_text(json.dumps(antigo), encoding="utf-8")
                dados = self.executar({"segments": [segmento("recuperado", .2, .8)]})
                self.assertEqual(dados["palavras"][0]["w"], "recuperado")
                self.assertIsNotNone(dados.get("versao_processamento"))

    def test_reaproveita_cache_atual_sem_rodar_mlx(self):
        bruto = {"segments": [segmento("fala", .2, .8)]}
        primeiro = self.executar(bruto)
        segundo = self.executar(bruto)
        self.assertEqual(primeiro, segundo)
        self.assertEqual(len(self.chamadas_mlx), 1)

    def test_travada_persistente_fica_sinalizada_sem_apagar_fala(self):
        bruto = {"segments": [segmento("É", s, s + 5.) for s in (0., 7., 14., 21.)]}
        dados = self.executar(bruto, dur=30.)
        self.assertEqual(len(dados["segmentos"]), 4)
        self.assertEqual(len(self.chamadas_mlx), 2)
        self.assertTrue(any(a["tipo"] == "possivel_travada" for a in dados["avisos"]))
        self.assertEqual(dados["conferencias"][0]["estado"], "persistente")
        self.assertEqual(dados["conferencias"][0]["whisper_bruto"], bruto)

    def test_recuperacao_de_travada_preserva_as_duas_leituras(self):
        bruto = {"segments": [segmento("É", s, s + 5.) for s in (0., 7., 14., 21.)]}
        recuperado = {"segments": [segmento("fala recuperada", 0., 10.),
                                    segmento("continuação", 10., 26.)]}
        dados = self.executar([bruto, recuperado], dur=30.)
        self.assertEqual([s["texto"] for s in dados["segmentos"]], ["fala recuperada", "continuação"])
        self.assertEqual(dados["whisper_bruto"], bruto)
        self.assertEqual(dados["conferencias"][0]["whisper_bruto"], recuperado)
        self.assertEqual(dados["conferencias"][0]["estado"], "recuperada")
        self.assertEqual(len(dados["conferencias"][0]["segmentos_anteriores"]), 4)

    def test_preserva_motor_e_opcoes_mlx(self):
        self.executar({"segments": [segmento("fala", .2, .8)]})
        args = self.chamadas_mlx[0]
        self.assertEqual(args[2:-2], ["--model", modulo.MODELO, "--language", "pt", "--task",
                                     "transcribe", "--word-timestamps", "True", "--output-format", "json"])
        self.assertNotIn("--condition-on-previous-text", args)


if __name__ == "__main__":
    unittest.main()
