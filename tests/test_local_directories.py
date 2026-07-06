import tempfile
import unittest
from pathlib import Path

from local_directories import LOCAL_DIRECTORIES, ensure_local_directories


class LocalDirectoriesTests(unittest.TestCase):
    def test_ensure_local_directories_creates_expected_paths_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            created = ensure_local_directories(root)
            expected = [root / relative_path for relative_path in LOCAL_DIRECTORIES]

            self.assertEqual(created, expected)
            for directory in expected:
                self.assertTrue(directory.exists())

            created_again = ensure_local_directories(root)
            self.assertEqual(created_again, expected)


if __name__ == "__main__":
    unittest.main()
