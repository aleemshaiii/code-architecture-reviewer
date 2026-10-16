import pytest
from app.services.refactorer import code_refactorer

def test_fix_unsafe_eval():
    code = "def run():\n    eval('1+1')"
    fixed = code_refactorer.fix_issue(code, "UNSAFE_CALL", 2)
    assert "ast.literal_eval" in fixed
    assert "import ast" in fixed

def test_fix_bare_except():
    code = "try:\n    x = 1\nexcept:\n    pass"
    fixed = code_refactorer.fix_issue(code, "BARE_EXCEPT", 3)
    assert "except Exception as exc:" in fixed

def test_fix_missing_docstring():
    code = "def calculate_tax(amount):\n    return amount * 0.1"
    fixed = code_refactorer.fix_issue(code, "MISSING_DOCSTRING", 1)
    assert '"""Execute calculate_tax procedure securely."""' in fixed
