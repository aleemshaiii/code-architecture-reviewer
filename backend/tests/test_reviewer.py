import pytest
from app.services.ast_analyzer import ast_analyzer
from app.services.vector_store import vector_store

def test_ast_analyzer_valid_code():
    code = """
import math

def calculate_area(radius):
    \"\"\"Calculates circle area.\"\"\"
    return math.pi * (radius ** 2)
"""
    result = ast_analyzer.analyze_source(code)
    assert result["valid_syntax"] is True
    assert result["metrics"]["function_count"] == 1
    assert result["metrics"]["import_count"] == 1
    assert len(result["warnings"]) == 0

def test_ast_analyzer_detects_security_and_reliability_issues():
    unsafe_code = """
def run_command(cmd):
    try:
        eval(cmd)
    except:
        pass
"""
    result = ast_analyzer.analyze_source(unsafe_code)
    assert result["valid_syntax"] is True
    warning_types = [w["type"] for w in result["warnings"]]
    
    assert "UNSAFE_CALL" in warning_types
    assert "BARE_EXCEPT" in warning_types
    assert "MISSING_DOCSTRING" in warning_types

def test_ast_analyzer_syntax_error_handling():
    broken_code = "def invalid_syntax(:"
    result = ast_analyzer.analyze_source(broken_code)
    assert result["valid_syntax"] is False
    assert "error" in result
    assert result["error"]["line"] == 1

def test_vector_store_initialization_and_search():
    assert vector_store.index.ntotal >= 5
    
    # Query related to eval/dynamic execution
    matches = vector_store.search_similar("eval dynamic injection execution", top_k=1)
    assert len(matches) > 0
    assert matches[0]["id"] == "SEC-001"

def test_vector_store_timeout_search():
    matches = vector_store.search_similar("timeout circuit breaker downstream failure", top_k=1)
    assert len(matches) > 0
    assert matches[0]["id"] == "REL-001"
