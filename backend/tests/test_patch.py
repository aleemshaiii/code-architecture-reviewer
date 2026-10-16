import pytest
from app.services.patch_generator import patch_generator

def test_unified_diff_generation():
    orig = "def compute():\n    eval('2+2')\n"
    mod = "import ast\ndef compute():\n    ast.literal_eval('2+2')\n"

    diff = patch_generator.create_unified_diff(orig, mod, "test.py")
    assert "--- a/test.py" in diff
    assert "+++ b/test.py" in diff
    assert "-    eval('2+2')" in diff
    assert "+    ast.literal_eval('2+2')" in diff
