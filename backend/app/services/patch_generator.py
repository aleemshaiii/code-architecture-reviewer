import difflib

class PatchGenerator:
    """
    Computes unified git diffs between original and modified code buffers.
    """

    @staticmethod
    def create_unified_diff(original_code: str, modified_code: str, filename: str = "app/main.py") -> str:
        orig_lines = original_code.splitlines(keepends=True)
        mod_lines = modified_code.splitlines(keepends=True)

        diff = difflib.unified_diff(
            orig_lines,
            mod_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=""
        )
        return "".join(diff)

patch_generator = PatchGenerator()
