"""Contrato da conferência: fixtures declaram cobertura, nunca audição real."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import wave

SCRIPT = Path(__file__).with_name("conferencia_fala.py")
spec = importlib.util.spec_from_file_location("conferencia_fala", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class GeometriaQuantizadaTests(unittest.TestCase):
    def plan(self):
        segs = [[i, i + .11] for i in range(12)]
        durations = [4 / 30] * 12
        timeline, cursor = [], 0
        for seg, duration in zip(segs, durations):
            timeline.append({"original": seg, "editado": [round(cursor, 6),
                                                         round(cursor + duration, 6)]})
            cursor += duration
        return {"fonte": "fixture.mp4", "trechos_pedidos": segs,
                "trechos_efetivos": segs, "duracoes_saida": durations, "timeline": timeline}

    def test_quantized_manifest_uses_output_duration_without_accumulating_rounding(self):
        plan = self.plan()
        geometry = gate._geometria(plan)
        self.assertEqual([r["editado"] for r in geometry["trechos"]],
                         [r["editado"] for r in plan["timeline"]])
        self.assertEqual(geometry["integral"]["editado"], [0, 1.6])
        self.assertEqual(len(geometry["emendas"]), 11)

    def test_reject_invalid_or_arbitrary_output_durations(self):
        for durations in (None, [], [4 / 30] * 11, [float("nan")] * 12,
                          [float("inf")] * 12, [.10] * 12, [.15] * 12,
                          [-.11] * 12, [True] * 12, ["0.133333"] * 12):
            plan = self.plan()
            plan.pop("timeline")
            plan["duracoes_saida"] = durations
            with self.subTest(durations=durations), self.assertRaises(ValueError):
                gate._geometria(plan)

    def test_reject_inverted_timeline_despite_valid_output_durations(self):
        plan = self.plan()
        plan["timeline"][0]["editado"].reverse()
        with self.assertRaises(ValueError):
            gate._geometria(plan)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "precisa ffmpeg/ffprobe")
class ConferenciaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.video = cls.root / "fixture.mp4"
        # Som sintético de teste, sem alegar voz, transcrição ou escuta humana.
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                        "color=c=blue:s=32x32:r=10:d=3", "-f", "lavfi", "-i",
                        "sine=frequency=440:sample_rate=16000:duration=3", "-c:v",
                        "libx264", "-c:a", "aac", "-shortest", str(cls.video)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.plan = self.root / "fixture.cortes.json"
        self.plan.write_text(json.dumps({"fonte": "original.mp4", "trechos_pedidos": [[2, 4], [8, 9]],
                                        "trechos_efetivos": [[2, 4], [8, 9]]}))
        self.report = gate.preparar(self.video, self.plan)
        self.data = json.loads(self.report.read_text())

    def save(self, data=None):
        self.report.write_text(json.dumps(self.data if data is None else data))

    def complete(self):
        self.data["status"] = "DECLARACAO_COMPLETA"
        for row in self.data["trechos"]:
            row["esperado"] = "FIXTURE: texto escolhido, sem voz real neste teste."
        for row in self.data["trechos"] + self.data["emendas"] + [self.data["integral"]]:
            row.update(resultado="aprovado", metodo="escuta_direta",
                       observado="FIXTURE: declaração artificial, nenhuma escuta real foi feita.")
            row["evidencia"] = {"recurso": row["audio"]["arquivo"],
                                "registro": "FIXTURE: cobertura preenchida para teste do contrato."}
        self.save()

    def test_preparar_pending_with_all_audio_and_coverage(self):
        self.assertEqual(self.data["status"], "PENDENTE")
        self.assertEqual([r["editado"] for r in self.data["trechos"]], [[0, 2], [2, 3]])
        self.assertEqual(self.data["emendas"][0]["editado"], [1.3, 2.7])
        for row in self.data["trechos"] + self.data["emendas"] + [self.data["integral"]]:
            with wave.open(str(self.report.parent / row["audio"]["arquivo"])) as wav:
                self.assertGreater(wav.getnframes(), 100)
                self.assertTrue(any(wav.readframes(wav.getnframes())))
        self.assertTrue(gate.verificar(self.report))

    def test_reject_missing_expected_literal_for_each_segment(self):
        self.complete()
        self.data["trechos"][0]["esperado"] = " "
        self.save()
        self.assertTrue(gate.verificar(self.report))

    def test_expected_empty_by_default_and_optional_plan_selection(self):
        self.assertEqual(self.data["trechos"][0].get("esperado"), "")
        plan = json.loads(self.plan.read_text())
        plan["textos_escolhidos"] = ["Texto escolhido A.", "Texto escolhido B."]
        self.plan.write_text(json.dumps(plan))
        result = json.loads(gate.preparar(self.video, self.plan).read_text())
        self.assertEqual([r["esperado"] for r in result["trechos"]], plan["textos_escolhidos"])
        self.assertTrue(gate.verificar(self.report))

    def test_accept_complete_fixture_declaration(self):
        self.complete()
        self.assertEqual(gate.verificar(self.report), [])

    def test_reject_missing_plan_video_and_report(self):
        with self.assertRaises((ValueError, OSError)):
            gate.preparar(self.video, self.root / "missing.json")
        self.assertTrue(gate.verificar(self.root / "missing.conferencia.json"))
        self.complete()
        for key in ("video", "plano"):
            data = copy.deepcopy(self.data)
            data[key]["arquivo"] = "missing"
            self.save(data)
            self.assertTrue(gate.verificar(self.report), key)

    def test_reject_empty_fields_and_transcript_or_images(self):
        self.complete()
        for field, value in (("observado", " "), ("metodo", "whisper"),
                             ("metodo", "transcricao+imagens"), ("resultado", "pendente")):
            data = copy.deepcopy(self.data)
            data["trechos"][0][field] = value
            self.save(data)
            self.assertTrue(gate.verificar(self.report), field)
        for field in ("registro", "recurso"):
            data = copy.deepcopy(self.data)
            data["integral"]["evidencia"][field] = ""
            self.save(data)
            self.assertTrue(gate.verificar(self.report), field)

    def test_reject_incomplete_or_changed_coverage(self):
        self.complete()
        for key in ("trechos", "emendas", "integral"):
            data = copy.deepcopy(self.data)
            data.pop(key)
            self.save(data)
            self.assertTrue(gate.verificar(self.report), key)
        data = copy.deepcopy(self.data)
        data["trechos"][0]["editado"] = [0, 1]
        self.save(data)
        self.assertTrue(gate.verificar(self.report))

    def test_reject_stale_plan_and_video_hashes(self):
        self.complete()
        for key in ("plano", "video"):
            data = copy.deepcopy(self.data)
            data[key]["sha256"] = "0" * 64
            self.save(data)
            self.assertTrue(gate.verificar(self.report), key)
        self.save()
        self.plan.write_text(self.plan.read_text() + " ")
        self.assertTrue(gate.verificar(self.report))

    def test_reject_replaced_audio(self):
        self.complete()
        audio = self.report.parent / self.data["trechos"][0]["audio"]["arquivo"]
        original = audio.read_bytes()
        audio.write_bytes(original + b"changed")
        try:
            self.assertTrue(gate.verificar(self.report))
        finally:
            audio.write_bytes(original)

    def test_reject_missing_or_invalid_plan_intervals(self):
        for value in ({}, {"trechos_efetivos": []}, {"trechos_efetivos": [[2, 1]]},
                      {"trechos_efetivos": [[0, float("nan")]]}):
            self.plan.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                gate.preparar(self.video, self.plan)

    def test_cli_pending_fails_complete_fixture_passes(self):
        cmd = [shutil.which("python3"), str(SCRIPT), "verificar", str(self.report)]
        self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
        self.complete()
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
