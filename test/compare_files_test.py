import os
import sys
import types
import tempfile
import unittest
from unittest import mock

import qt_stubs  # noqa: F401

# Provide a minimal vtk stub before importing settings
vtk_stub = types.ModuleType("vtk")


class DummyNamedColors:
    def GetColor3d(self, key):
        return (0.0, 0.0, 0.0)


vtk_stub.vtkNamedColors = DummyNamedColors
sys.modules["vtk"] = vtk_stub

from src.settings import compare_files


class CompareFilesTest(unittest.TestCase):
    def test_missing_first_file_returns_false(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"data")
            existing_path = temp_file.name
        missing_path = existing_path + "_missing"
        self.assertFalse(compare_files(missing_path, existing_path))
        os.remove(existing_path)

    def test_missing_second_file_returns_false(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"data")
            existing_path = temp_file.name
        missing_path = existing_path + "_missing"
        self.assertFalse(compare_files(existing_path, missing_path))
        os.remove(existing_path)

    def test_both_files_missing_returns_false(self):
        import uuid

        missing1 = os.path.join(tempfile.gettempdir(), uuid.uuid4().hex)
        missing2 = os.path.join(tempfile.gettempdir(), uuid.uuid4().hex)
        self.assertFalse(compare_files(missing1, missing2))

    def test_file_not_found_during_read_returns_false(self):
        with tempfile.NamedTemporaryFile(delete=False) as f1:
            path1 = f1.name
        with tempfile.NamedTemporaryFile(delete=False) as f2:
            path2 = f2.name
        with mock.patch("builtins.open", side_effect=FileNotFoundError()):
            self.assertFalse(compare_files(path1, path2))
        os.remove(path1)
        os.remove(path2)


if __name__ == "__main__":
    unittest.main()
