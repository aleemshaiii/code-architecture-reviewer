import ast
from typing import Dict, Any, List

class ASTCodeAnalyzer:
    """
    Parses Python source code, extracts syntax trees, node hierarchies,
    and flags anti-patterns and vulnerabilities.
    """

    def analyze_source(self, code_str: str) -> Dict[str, Any]:
        try:
            tree = ast.parse(code_str)
        except SyntaxError as err:
            return {
                "valid_syntax": False,
                "error": {
                    "line": err.lineno,
                    "offset": err.offset,
                    "message": str(err.msg)
                },
                "metrics": {
                    "total_lines": len(code_str.splitlines()),
                    "function_count": 0,
                    "class_count": 0,
                    "import_count": 0,
                    "warning_count": 1
                },
                "warnings": [{
                    "line": err.lineno or 1,
                    "type": "SYNTAX_ERROR",
                    "message": f"SyntaxError: {err.msg}"
                }],
                "imports": [],
                "tree_nodes": []
            }

        warnings: List[Dict[str, Any]] = []
        imports: List[str] = []
        functions: List[str] = []
        classes: List[str] = []
        tree_nodes: List[Dict[str, Any]] = []

        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

            # Classes
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)

            # Functions & Docstrings
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
                docstring = ast.get_docstring(node)
                if not docstring:
                    warnings.append({
                        "line": node.lineno,
                        "type": "MISSING_DOCSTRING",
                        "message": f"Function '{node.name}' has no docstring definition."
                    })

            # Security: Dynamic Code Execution
            elif isinstance(node, ast.Call):
                func_id = None
                if isinstance(node.func, ast.Name):
                    func_id = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_id = node.func.attr

                if func_id in ("eval", "exec"):
                    warnings.append({
                        "line": node.lineno,
                        "type": "UNSAFE_CALL",
                        "message": f"Critical security issue: dynamic execution via '{func_id}()'."
                    })

            # Reliability: Bare Except Clauses
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    warnings.append({
                        "line": node.lineno,
                        "type": "BARE_EXCEPT",
                        "message": "Use of bare 'except:': catches SystemExit and KeyboardInterrupt; specify Exception type."
                    })

        # Build clean hierarchical tree for the visual explorer
        for item in tree.body:
            tree_nodes.append(self._format_ast_node(item))

        return {
            "valid_syntax": True,
            "metrics": {
                "total_lines": len(code_str.splitlines()),
                "function_count": len(functions),
                "class_count": len(classes),
                "import_count": len(imports),
                "warning_count": len(warnings)
            },
            "warnings": warnings,
            "imports": imports,
            "tree_nodes": tree_nodes
        }

    def _format_ast_node(self, node: ast.AST) -> Dict[str, Any]:
        node_type = type(node).__name__
        line = getattr(node, "lineno", 1)

        node_data = {
            "type": node_type,
            "line": line,
            "name": getattr(node, "name", None),
            "children": []
        }

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node_data["name"] = node.name
            node_data["args"] = [a.arg for a in node.args.args]
            node_data["children"] = [self._format_ast_node(child) for child in node.body if hasattr(child, "lineno")]

        elif isinstance(node, ast.ClassDef):
            node_data["name"] = node.name
            node_data["children"] = [self._format_ast_node(child) for child in node.body if hasattr(child, "lineno")]

        elif isinstance(node, ast.Import):
            node_data["name"] = ", ".join(a.name for a in node.names)

        elif isinstance(node, ast.ImportFrom):
            node_data["name"] = f"{node.module} ({', '.join(a.name for a in node.names)})"

        elif isinstance(node, ast.Try):
            node_data["children"] = [self._format_ast_node(child) for child in node.body if hasattr(child, "lineno")]

        return node_data

ast_analyzer = ASTCodeAnalyzer()
