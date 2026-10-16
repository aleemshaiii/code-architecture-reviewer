import json
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import StreamingResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from app.services.ast_analyzer import ast_analyzer
from app.services.vector_store import vector_store
from app.services.multimodal_reviewer import multimodal_reviewer
from app.services.report_generator import report_generator
from app.services.refactorer import code_refactorer
from app.services.patch_generator import patch_generator

app = FastAPI(
    title="Real-Time Multimodal Code & Architecture Reviewer",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "code-architecture-reviewer-api",
        "vector_rules_indexed": vector_store.index.ntotal
    }

@app.post("/api/export-report")
async def export_audit_report(payload: dict = Body(...)):
    pdf_buffer = report_generator.generate_pdf(payload)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=architecture_audit_report.pdf"}
    )

@app.post("/api/export-patch")
async def export_git_patch(payload: dict = Body(...)):
    original_code = payload.get("original_code", "")
    modified_code = payload.get("modified_code", "")
    filename = payload.get("filename", "service.py")
    
    diff_text = patch_generator.create_unified_diff(original_code, modified_code, filename)
    return PlainTextResponse(
        diff_text,
        headers={"Content-Disposition": f"attachment; filename={filename}.patch"}
    )

@app.post("/api/auto-fix")
async def auto_fix_code(payload: dict = Body(...)):
    code_str = payload.get("code", "")
    warning_type = payload.get("warning_type", "")
    line_number = payload.get("line_number", 1)
    
    fixed_code = code_refactorer.fix_issue(code_str, warning_type, line_number)
    return {"fixed_code": fixed_code}

@app.websocket("/ws/review")
async def websocket_review_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({
        "type": "connection_established",
        "message": "Connected to Real-Time Review Pipeline"
    })

    try:
        while True:
            raw_text = await websocket.receive_text()
            data = json.loads(raw_text)
            
            code_str = data.get("code", "")
            diagram_base64 = data.get("diagram_base64", None)

            # 1. AST Analysis
            ast_results = ast_analyzer.analyze_source(code_str)

            # 2. FAISS Matching
            matched_rules = []
            for warning in ast_results.get("warnings", []):
                query = f"{warning.get('type', '')} {warning.get('message', '')}"
                similar = vector_store.search_similar(query, top_k=1)
                if similar:
                    matched_rules.extend(similar)

            unique_rules = {r["id"]: r for r in matched_rules}

            # 3. Diagram Processing
            image_bytes = None
            if diagram_base64:
                try:
                    if "," in diagram_base64:
                        diagram_base64 = diagram_base64.split(",")[1]
                    image_bytes = base64.b64decode(diagram_base64)
                except Exception as e:
                    print(f"Diagram decoding error: {e}")

            # 4. Multimodal Architecture Review
            arch_results = await multimodal_reviewer.review_architecture_and_code(
                image_bytes=image_bytes,
                code_str=code_str,
                ast_summary=ast_results
            )

            # 5. Push payload
            await websocket.send_json({
                "type": "review_result",
                "ast": ast_results,
                "architecture": arch_results,
                "relevant_rules": list(unique_rules.values())
            })

    except WebSocketDisconnect:
        print("Client disconnected from /ws/review")
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except:
            pass
