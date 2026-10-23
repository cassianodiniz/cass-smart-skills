"""Regressões: exclusões editoriais não podem ser desfeitas pelo aparo de volume."""
import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
SCRIPT = Path(os.environ.get("CORTAR_SCRIPT", Path(__file__).with_name("cortar_trechos.py")))
spec = importlib.util.spec_from_file_location("cortar_em_teste", SCRIPT)
cortador = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cortador)
colar = cortador.colar


class CortesEditoriais(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.audio = Path(cls.tmp.name) / 'voz.wav'
        sr = 16000
        x = (.2 * np.sin(2 * np.pi * 220 * np.arange(sr * 4) / sr)).astype('float32')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(sr),
                        '-ac', '1', '-i', '-', str(cls.audio)], input=x.tobytes(), check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_exclusao_curta_com_voz_permanece_excluida(self):
        for gap in (.05, .18, .20, .24, .25, .35):
            with self.subTest(gap=gap):
                real = colar(str(self.audio), [[0., 1.], [1. + gap, 2.]])
                reintroduzido = sum(max(0, min(b, 1. + gap) - max(a, 1.)) for a, b in real)
                self.assertAlmostEqual(reintroduzido, 0., places=6)
                self.assertEqual(len(real), 2)

    def test_ordem_editorial_pode_voltar_no_original(self):
        self.assertEqual(colar(str(self.audio), [[2., 3.], [0., 1.]]), [[2., 3.], [0., 1.]])

    def test_limites_de_cada_janela_sao_respeitados(self):
        pedido = [[.13, .97], [1.10, 1.63], [2.20, 3.71]]
        real = colar(str(self.audio), pedido)
        self.assertEqual(real, pedido)

    def test_aparo_nao_escolhe_tentativa_final_por_conta_propria(self):
        # Contrato: a escolha editorial é anterior ao aparo. Dois pedidos continuam dois.
        self.assertEqual(colar(str(self.audio), [[.2, .8], [1.4, 2.5]]), [[.2, .8], [1.4, 2.5]])

    def test_janelas_invalidas_rejeitadas(self):
        for ranges in ([], [[-1, 1]], [[1, 1]], [[2, 1]], [[0, float('nan')]]):
            with self.subTest(ranges=ranges):
                with self.assertRaises(ValueError):
                    colar(str(self.audio), ranges)


class AlinhamentoDeQuadros(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.video = cls.root / "fonte.mkv"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                        "testsrc2=size=32x64:rate=30:duration=4", "-f", "lavfi", "-i",
                        "sine=frequency=440:sample_rate=48000:duration=4", "-c:v", "libx264",
                        "-c:a", "pcm_s16le", "-shortest", str(cls.video)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def renderizar(self, trechos, nome):
        saida = self.root / (nome + ".mp4")

        def transcricao_controlada(video, json_saida, **kwargs):
            Path(json_saida).write_text('{"fixture": true}')
            Path(json_saida).with_suffix(".md").write_text("Fixture; nenhuma transcrição real.\n")

        with patch.object(sys, "argv", [str(SCRIPT), str(self.video), str(saida),
                                        json.dumps(trechos), "--solto"]), \
                patch.object(cortador, "transcrever", side_effect=transcricao_controlada):
            cortador.main()
        plano = json.loads(saida.with_suffix(".cortes.json").read_text())
        revisao = json.loads(saida.with_suffix(".conferencia.json").read_text())
        probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams",
                                          "-show_format", "-of", "json", str(saida)],
                                         check=True, capture_output=True, text=True).stdout)
        return plano, revisao, probe

    def test_doze_janelas_de_110ms_integram_render_e_conferencia(self):
        trechos = [[round(.1 + i * .2, 6), round(.21 + i * .2, 6)] for i in range(12)]
        plano, revisao, probe = self.renderizar(trechos, "doze")
        self.assertEqual(plano["trechos_efetivos"], trechos)
        self.assertEqual(plano["duracoes_saida"], [4 / 30] * 12)
        self.assertEqual(plano["timeline"][-1]["editado"][1], 1.6)
        video = next(s for s in probe["streams"] if s["codec_type"] == "video")
        self.assertEqual(int(video["nb_frames"]), 48)
        self.assertAlmostEqual(float(probe["format"]["duration"]), 1.6, delta=.025)
        self.assertEqual(revisao["status"], "PENDENTE")
        self.assertEqual(revisao["trechos"][-1]["editado"], [1.466667, 1.6])

    def test_fronteiras_de_frame_nao_ganham_um_quadro_por_erro_float(self):
        trechos = [[0., .1], [.2, .3], [.4, .4 + 1 / 30], [.6, .700001], [.9, 1.01]]
        plano, revisao, probe = self.renderizar(trechos, "fronteiras")
        frames = [3, 3, 1, 4, 4]
        self.assertEqual(plano["trechos_efetivos"], trechos)
        self.assertEqual(plano["duracoes_saida"], [n / 30 for n in frames])
        video = next(s for s in probe["streams"] if s["codec_type"] == "video")
        self.assertEqual(int(video["nb_frames"]), sum(frames))
        self.assertEqual(revisao["status"], "PENDENTE")
        for (a, b), dur in zip(trechos, plano["duracoes_saida"]):
            self.assertGreaterEqual(dur + 1e-9, b - a)
            self.assertLessEqual(dur - (b - a), 1 / 30 + 1e-9)


if __name__ == '__main__':
    unittest.main()
