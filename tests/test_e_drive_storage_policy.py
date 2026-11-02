"""Fast static contract test: all bulk experiment paths must prefer E:."""
import json
import unittest
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]


class TestLocalStorageContract(unittest.TestCase):
    def test_bulk_paths_on_e_and_no_c_fallback(self):
        cfg = json.loads((ROOT / "research/revalidation/LOCAL_4070TI_FULL_V1.json").read_text(encoding="utf-8"))
        storage = cfg["storage_policy"]
        self.assertTrue(storage["forbid_silent_fallback_to_C"])
        self.assertTrue(storage["set_environment_per_process_not_global"])
        self.assertEqual(storage["windows_preferred_drive"].upper(), "E:")
        for k in ["root", "worktree", "venv", "public_datasets", "download_staging",
                  "caches", "temporary_files", "outputs", "checkpoints", "logs", "reports"]:
            with self.subTest(path=k):
                self.assertEqual(PureWindowsPath(storage[k]).drive.upper(), "E:")
        self.assertEqual(cfg["evidence_outputs"]["local_root"], storage["outputs"])
        self.assertEqual(cfg["hardware"]["scratch_directory"], storage["outputs"])

    def test_process_scoped_bootstrap_has_e_guard(self):
        ps1 = (ROOT / "scripts/prepare_local_e_drive.ps1").read_text(encoding="utf-8")
        self.assertIn("EnvironmentVariableTarget]::Process", ps1)
        self.assertIn("Refusing to use C: as fallback", ps1)
        self.assertIn("'E:\\GENESIS'", ps1)


if __name__ == "__main__":
    unittest.main()
