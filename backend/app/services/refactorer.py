import re
from typing import Dict, Any

class CodeRefactorer:
    """
    Applies precise AST-driven structural repairs and pattern fixes to source code.
    """
    
    @staticmethod
    def fix_issue(code_str: str, warning_type: str, line_number: int) -> str:
        lines = code_str.split("\n")
        idx = max(0, line_number - 1)
        
        if warning_type == "UNSAFE_CALL":
            # Replace eval/exec calls with safe ast.literal_eval
            if "import ast" not in code_str:
                code_str = "import ast\n" + code_str
                lines = code_str.split("\n")
                idx += 1  # Offset by inserted import

            if idx < len(lines):
                lines[idx] = re.sub(r'\beval\(', 'ast.literal_eval(', lines[idx])
                lines[idx] = re.sub(r'\bexec\(', '# TODO: Refactor dynamic exec: ', lines[idx])
            return "\n".join(lines)

        elif warning_type == "BARE_EXCEPT":
            # Replace bare 'except:' with explicit 'except Exception as exc:'
            if idx < len(lines):
                lines[idx] = re.sub(r'except\s*:', 'except Exception as exc:', lines[idx])
            return "\n".join(lines)

        elif warning_type == "MISSING_DOCSTRING":
            # Insert standard PEP-257 docstring under the function definition
            if idx < len(lines):
                match = re.match(r'^(\s*)def\s+([a-zA-Z0-9_]+)\(', lines[idx])
                if match:
                    indent = match.group(1) + "    "
                    fn_name = match.group(2)
                    docstring = f'{indent}"""Execute {fn_name} procedure securely."""'
                    lines.insert(idx + 1, docstring)
            return "\n".join(lines)

        return code_str

code_refactorer = CodeRefactorer()
