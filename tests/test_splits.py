import os
import unittest

class TestSplits(unittest.TestCase):
    def test_pointer_files(self):
        for split in ["train", "val", "test"]:
            path = f"data/splits/{split}.parquet.dvc"
            self.assertTrue(os.path.exists(path), f"Missing pointer file: {path}")

if __name__ == "__main__":
    unittest.main()
