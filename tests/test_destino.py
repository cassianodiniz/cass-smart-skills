import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "skills/search/scripts/destino_pesquisa.py"

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.skill = self.root / "skill"
        self.script = self.skill / "scripts/destino_pesquisa.py"
        self.script.parent.mkdir(parents=True)
        shutil.copy2(SOURCE, self.script)
    def tearDown(self):
        self.tmp.cleanup()
    def run_script(self, *args):
        return subprocess.run([sys.executable, str(self.script), *args], cwd=self.root,
                              capture_output=True, text=True, timeout=10)
    def module(self):
        spec = importlib.util.spec_from_file_location("archive_test", self.script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    def test_destination_ignores_working_directory(self):
        result = self.run_script("Nutrição / revisão", "--data", "2026-09-30")
        self.assertEqual(result.returncode, 0, result.stderr)
        target = Path(result.stdout.strip())
        self.assertEqual(target, self.skill / "pesquisas/nutricao-revisao-2026-09-30")
        self.assertTrue((target / "referencias").is_dir())
        self.assertFalse((self.root / "pesquisas").exists())
    def test_repeated_run_preserves_previous_content(self):
        first = Path(self.run_script("tema", "--data", "2026-09-30").stdout.strip())
        marker = first / "estudo.md"
        marker.write_text("pesquisa anterior")
        second_result = self.run_script("tema", "--data", "2026-09-30")
        self.assertEqual(second_result.returncode, 0, second_result.stderr)
        second = Path(second_result.stdout.strip())
        self.assertNotEqual(first, second)
        self.assertEqual(marker.read_text(), "pesquisa anterior")
    def test_check_does_not_create_output(self):
        self.assertEqual(self.run_script("--conferir").returncode, 0)
        self.assertFalse((self.skill / "pesquisas").exists())
    def test_invalid_date_cannot_escape_destination(self):
        result = self.run_script("tema", "--data", "../../outside")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.skill / "pesquisas").exists())
    def test_symlink_redirect_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.skill / "pesquisas").symlink_to(outside, target_is_directory=True)
        result = self.run_script("tema")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(outside.iterdir()), [])
    def test_readonly_check_reports_failure(self):
        with patch("os.access", return_value=False):
            self.assertEqual(self.module().main(["--conferir"]), 2)
        self.assertFalse((self.skill / "pesquisas").exists())
    def test_write_failure_does_not_choose_another_folder(self):
        with patch.object(Path, "mkdir", side_effect=PermissionError("read only")):
            self.assertEqual(self.module().main(["tema"]), 2)
        self.assertFalse((self.root / "pesquisas").exists())
        self.assertFalse((self.skill / "pesquisas").exists())

if __name__ == "__main__":
    unittest.main()
