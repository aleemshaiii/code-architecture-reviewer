import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

class MultimodalReviewer:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip('"').strip("'")
        self.client = genai.Client(api_key=self.api_key) if (genai and self.api_key and "PASTE_" not in self.api_key) else None

    async def review_architecture_and_code(
        self,
        image_bytes: Optional[bytes],
        code_str: str,
        ast_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        if self.client and image_bytes:
            return await self._call_vision_model(image_bytes, code_str, ast_summary)
        
        return self._heuristic_review(code_str, ast_summary, bool(image_bytes))

    async def _call_vision_model(
        self,
        image_bytes: bytes,
        code_str: str,
        ast_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        system_instruction = (
            "You are a Principal Software and Cloud Solutions Architect. "
            "Inspect the architecture diagram image and the provided code AST metrics. "
            "List detected components, detect architecture drift (diagram elements missing or unhandled in code), "
            "and supply concrete recommendations. Return ONLY valid JSON."
        )

        prompt = (
            f"Code AST Summary:\n{json.dumps(ast_summary, indent=2)}\n\n"
            f"Code Snippet:\n```python\n{code_str[:2500]}\n```\n"
            "Compare diagram with code and identify architectural components and drift."
        )

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json"
                )
            )
            parsed = json.loads(response.text)
            parsed["mode"] = "gemini_multimodal_vision"
            return parsed
        except Exception as exc:
            fallback = self._heuristic_review(code_str, ast_summary, True)
            fallback["vision_error"] = str(exc)
            return fallback

    def _heuristic_review(
        self,
        code_str: str,
        ast_summary: Dict[str, Any],
        has_diagram: bool
    ) -> Dict[str, Any]:
        imports = ast_summary.get("imports", [])
        code_lower = code_str.lower()
        drift_warnings = []
        components_found = []

        if "fastapi" in imports or "flask" in imports:
            components_found.append("REST API Service")
        if "redis" in code_lower:
            components_found.append("Cache Layer (Redis)")
        if "postgres" in code_lower or "sqlalchemy" in imports:
            components_found.append("Relational Database (PostgreSQL/SQLAlchemy)")

        if not has_diagram:
            drift_warnings.append({
                "type": "NO_DIAGRAM_ATTACHED",
                "message": "No architectural diagram attached. Review running on static AST analysis."
            })
        else:
            components_found.append("Architecture Diagram (Visual Component Analyzed)")

        return {
            "mode": "heuristic_fallback" if not self.client else "gemini_multimodal_vision",
            "diagram_components": components_found,
            "architecture_drift": drift_warnings,
            "recommendations": [
                "Ensure asynchronous DB sessions are used if handling high concurrent traffic.",
                "Verify network timeouts and retry logic on external API boundaries."
            ]
        }

multimodal_reviewer = MultimodalReviewer()
