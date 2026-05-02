import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_text_integrity.py"


class TextIntegrityTests(unittest.TestCase):
    def run_validator(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
        )

    def test_validator_flags_private_use_and_replacement_characters(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bad_file = root / "bad.md"
            bad_file.write_text("正常文本\ue000\ufffd\n" + "?" * 4 + "\n", encoding="utf-8")

            result = self.run_validator("--root", str(root), "--all")

            self.assertNotEqual(result.returncode, 0)
            output = result.stdout + result.stderr
            self.assertIn("bad.md", output)
            self.assertIn("U+E000", output)
            self.assertIn("U+FFFD", output)
            self.assertIn("question-mark run", output)

    def test_repository_text_files_have_no_known_bad_characters(self) -> None:
        result = self.run_validator("--root", str(REPO_ROOT))

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("text integrity: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
