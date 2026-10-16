# Real-Time Multimodal Code & Architecture Reviewer

[![CI Review Pipeline](https://github.com/aleemshaiii/code-architecture-reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/aleemshaiii/code-architecture-reviewer/actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![FAISS](https://img.shields.io/badge/Vector_DB-FAISS-0A85EA)](https://github.com/facebookresearch/faiss)
[![Gemini Vision](https://img.shields.io/badge/Vision_AI-Gemini_2.5_Flash-8E75B2?logo=google&logoColor=white)](https://ai.google.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, real-time code and system architecture audit engine. The application monitors code typed in a browser-based Monaco editor via WebSockets, parses syntax trees with Python AST, checks anti-patterns against a FAISS vector database of architectural best practices, and evaluates visual architecture diagrams using Google Gemini multimodal vision to detect architectural drift.

---

## Key Features

- **Live Python AST Analysis:** Instant AST validation, cyclomatic/structural metrics, and vulnerability detection (e.g., dynamic `eval()`, bare `except:`, missing docstrings).
- **In-Line Editor Squiggly Markers:** Uses Monaco's `setModelMarkers` to highlight problematic lines with severity tooltips in real time.
- **Multimodal Architecture Drift Detection:** Upload PNG/JPEG architecture diagrams; Gemini Vision identifies visual services, queues, and databases, flagging components missing from the actual implementation.
- **FAISS Vector Knowledge Base:** Semantic retrieval of architectural rules (OWASP, async reliability, caching strategies, and connection pooling).
- **Interactive Visual AST Explorer:** Expandable syntax hierarchy allowing developers to inspect nodes and jump directly to specific lines in the editor.
- **One-Click Auto-Fix ("Refactor with AI"):** In-place AST-driven code repairs for common antipatterns.
- **Git Patch & Audit PDF Generation:** Export standard unified diff `.patch` files or professional PDF audit reports built with ReportLab.

---

## Architecture Overview

```text
       Browser (React + Monaco Editor)
                     │
       Persistent WebSocket /ws/review
                     │
                     ▼
          FastAPI Gateway Server
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
Python AST    FAISS Vector Store  Multimodal Vision
 Analyzer     (Rules Catalog)    (Gemini 2.5 Flash)
       │             │             │
       └─────────────┼─────────────┘
                     ▼
       Real-Time Review Payload Stream
Tech Stack
Frontend: React, Vite, @monaco-editor/react, lucide-react

Backend: FastAPI, Python ast, WebSockets, Uvicorn

Vector Search: Facebook AI Similarity Search (FAISS), NumPy

Multimodal AI: Google Gemini Vision (gemini-2.5-flash)

Reporting & Diffing: ReportLab, Python difflib

Containerization & CI: Docker, Docker Compose, GitHub Actions

Getting Started
Prerequisites
Python 3.10+

Node.js 18+

Git

1. Backend Setup
Bash


cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
(Optional) To enable deep visual diagram analysis, create backend/.env:

Code snippet


GEMINI_API_KEY="your-api-key-here"
2. Frontend Setup
Bash


cd frontend
npm install
npm run dev
Visit http://localhost:5173 to launch the reviewer dashboard.

Running Automated Tests
Bash


cd backend
python -m pytest -v tests/
Running with Docker Compose
Bash


docker-compose up --build
Frontend: http://localhost:3000

Backend API: http://localhost:8000

License
This project is licensed under the MIT License.
