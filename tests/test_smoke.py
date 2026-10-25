import os
import unittest

class TestProjectStructure(unittest.TestCase):
    def test_smoke(self):
        """Sanity check that tests execute."""
        self.assertTrue(True)

    def test_dvc_pointers_exist(self):
        """Verify DVC split pointers are committed to git."""
        self.assertTrue(os.path.exists("data/splits/train.parquet.dvc"))
        self.assertTrue(os.path.exists("data/splits/val.parquet.dvc"))
        self.assertTrue(os.path.exists("data/splits/test.parquet.dvc"))

    def test_report_exists(self):
        """Verify delivery report is present."""
        self.assertTrue(os.path.exists("REPORT.md"))

if __name__ == "__main__":
    unittest.main()
