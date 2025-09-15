import sys
import types
import tempfile
import unittest
from unittest import mock

from pathlib import Path

import qt_stubs  # noqa: F401

# Provide a minimal vtk stub before importing settings
vtk_stub = types.ModuleType("vtk")


class DummyNamedColors:
    def GetColor3d(self, key):
        return (0.0, 0.0, 0.0)


vtk_stub.vtkNamedColors = DummyNamedColors
sys.modules["vtk"] = vtk_stub

from src.settings import compare_files  # noqa: E402


class CompareFilesTest(unittest.TestCase):
    def test_missing_first_file_returns_false(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"data")
            existing_path = Path(temp_file.name)
        missing_path = existing_path.with_name(existing_path.name + "_missing")
        self.assertFalse(compare_files(missing_path, existing_path))
        existing_path.unlink()

    def test_missing_second_file_returns_false(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"data")
            existing_path = Path(temp_file.name)
        missing_path = existing_path.with_name(existing_path.name + "_missing")
        self.assertFalse(compare_files(existing_path, missing_path))
        existing_path.unlink()

    def test_both_files_missing_returns_false(self):
        import uuid

        missing1 = Path(tempfile.gettempdir()) / uuid.uuid4().hex
        missing2 = Path(tempfile.gettempdir()) / uuid.uuid4().hex
        self.assertFalse(compare_files(missing1, missing2))

    def test_file_not_found_during_read_returns_false(self):
        with tempfile.NamedTemporaryFile(delete=False) as f1:
            path1 = Path(f1.name)
        with tempfile.NamedTemporaryFile(delete=False) as f2:
            path2 = Path(f2.name)
        with mock.patch("pathlib.Path.open", side_effect=FileNotFoundError()):
            self.assertFalse(compare_files(path1, path2))
        path1.unlink()
        path2.unlink()


if __name__ == "__main__":
    unittest.main()
