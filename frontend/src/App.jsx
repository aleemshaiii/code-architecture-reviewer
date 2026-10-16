import React, { useState, useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { 
  ShieldAlert, 
  Layers, 
  BookOpen, 
  CheckCircle2, 
  UploadCloud, 
  Code2, 
  Radio,
  FileDown,
  Wand2,
  FolderTree,
  ChevronRight,
  ChevronDown,
  GitPullRequest
} from 'lucide-react';
import './App.css';

const INITIAL_CODE = `import redis
import os

def process_transaction(user_id, amount):
    # Missing docstring and using unsafe dynamic eval
    query = f"update_balance({user_id}, {amount})"
    try:
        eval(query)
    except:
        pass
    return True
`;

function ASTNodeView({ node, onSelectLine }) {
  const [isOpen, setIsOpen] = useState(true);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div style={{ marginLeft: '14px', fontFamily: 'monospace', fontSize: '0.78rem' }}>
      <div 
        style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '4px', 
          cursor: 'pointer',
          padding: '2px 4px',
          borderRadius: '3px'
        }}
        onClick={() => {
          if (node.line) onSelectLine(node.line);
        }}
      >
        {hasChildren ? (
          <span onClick={(e) => { e.stopPropagation(); setIsOpen(!isOpen); }}>
            {isOpen ? <ChevronDown size={12} color="#94a3b8" /> : <ChevronRight size={12} color="#94a3b8" />}
          </span>
        ) : (
          <span style={{ width: '12px' }} />
        )}
        <span style={{ color: '#38bdf8', fontWeight: 600 }}>{node.type}</span>
        {node.name && <span style={{ color: '#facc15' }}>"{node.name}"</span>}
        {node.line && <span style={{ color: '#64748b', fontSize: '0.7rem' }}>[L{node.line}]</span>}
      </div>
      {isOpen && hasChildren && (
        <div style={{ borderLeft: '1px dashed #334155', marginLeft: '6px' }}>
          {node.children.map((child, idx) => (
            <ASTNodeView key={idx} node={child} onSelectLine={onSelectLine} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [diagramBase64, setDiagramBase64] = useState(null);
  const [connected, setConnected] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [fixingLine, setFixingLine] = useState(null);
  const [activeTab, setActiveTab] = useState('editor');
  const [review, setReview] = useState({
    ast: { valid_syntax: true, metrics: {}, warnings: [], tree_nodes: [] },
    architecture: { diagram_components: [], architecture_drift: [], recommendations: [] },
    relevant_rules: []
  });

  const ws = useRef(null);
  const codeRef = useRef(INITIAL_CODE);
  const originalCodeRef = useRef(INITIAL_CODE);
  const monacoRef = useRef(null);
  const editorRef = useRef(null);

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8000/ws/review');
    ws.current = socket;

    socket.onopen = () => {
      setConnected(true);
      sendPayload(codeRef.current, diagramBase64);
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'review_result') {
          setReview(payload);
          applyEditorMarkers(payload.ast?.warnings || []);
        }
      } catch (err) {
        console.error('Error parsing WebSocket frame:', err);
      }
    };

    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);

    return () => socket.close();
  }, []);

  const sendPayload = (currentCode, currentDiagram) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        code: currentCode,
        diagram_base64: currentDiagram
      }));
    }
  };

  const handleEditorMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
  };

  const applyEditorMarkers = (warnings) => {
    if (!monacoRef.current || !editorRef.current) return;
    const model = editorRef.current.getModel();
    if (!model) return;

    const markers = warnings.map((w) => ({
      startLineNumber: w.line,
      startColumn: 1,
      endLineNumber: w.line,
      endColumn: model.getLineMaxColumn(w.line),
      message: `[${w.type}] ${w.message}`,
      severity: w.type === 'UNSAFE_CALL' 
        ? monacoRef.current.MarkerSeverity.Error 
        : monacoRef.current.MarkerSeverity.Warning
    }));

    monacoRef.current.editor.setModelMarkers(model, 'ast-analyzer', markers);
  };

  const jumpToLine = (lineNumber) => {
    if (editorRef.current) {
      editorRef.current.revealLineInCenter(lineNumber);
      editorRef.current.setPosition({ lineNumber, column: 1 });
      editorRef.current.focus();
    }
  };

  const handleEditorChange = (value) => {
    const updated = value || '';
    codeRef.current = updated;
    sendPayload(updated, diagramBase64);
  };

  const handleDiagramUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setDiagramBase64(reader.result);
        sendPayload(codeRef.current, reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleExportPDF = async () => {
    try {
      setIsExporting(true);
      const res = await fetch('http://localhost:8000/api/export-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(review)
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'architecture_audit_report.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error('PDF Export failed:', err);
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportPatch = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/export-patch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          original_code: originalCodeRef.current,
          modified_code: codeRef.current,
          filename: 'service.py'
        })
      });
      const patchText = await res.text();
      const blob = new Blob([patchText], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'changes.patch';
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error('Patch Export failed:', err);
    }
  };

  const handleAutoFix = async (warning) => {
    try {
      setFixingLine(warning.line);
      const res = await fetch('http://localhost:8000/api/auto-fix', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: codeRef.current,
          warning_type: warning.type,
          line_number: warning.line
        })
      });
      const data = await res.json();
      if (data.fixed_code) {
        codeRef.current = data.fixed_code;
        if (editorRef.current) {
          editorRef.current.setValue(data.fixed_code);
        }
        sendPayload(data.fixed_code, diagramBase64);
      }
    } catch (err) {
      console.error('Auto-fix failed:', err);
    } finally {
      setFixingLine(null);
    }
  };

  const { ast, architecture, relevant_rules } = review;

  return (
    <div className="app-container">
      <header className="top-navbar">
        <div className="brand-section">
          <Code2 size={24} color="#38bdf8" />
          <h1 className="brand-title">Code & Architecture Reviewer</h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button 
            onClick={handleExportPatch} 
            title="Download Git Unified Diff Patch"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              background: '#1e293b',
              color: '#38bdf8',
              border: '1px solid #0284c7',
              padding: '4px 9px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.78rem'
            }}
          >
            <GitPullRequest size={13} />
            <span>Export Git Patch</span>
          </button>

          <button 
            onClick={handleExportPDF} 
            disabled={isExporting}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              background: '#334155',
              color: '#f8fafc',
              border: '1px solid #475569',
              padding: '4px 9px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.78rem'
            }}
          >
            <FileDown size={13} />
            <span>{isExporting ? 'Generating...' : 'Export PDF'}</span>
          </button>

          <div className={`badge ${connected ? 'badge-connected' : 'badge-disconnected'}`}>
            <Radio size={14} />
            {connected ? 'Pipeline Active' : 'Disconnected'}
          </div>
        </div>
      </header>

      <main className="main-workspace">
        <section className="editor-column">
          <div className="editor-toolbar">
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setActiveTab('editor')}
                style={{
                  background: activeTab === 'editor' ? '#0284c7' : 'transparent',
                  color: '#fff',
                  border: 'none',
                  padding: '3px 8px',
                  borderRadius: '3px',
                  fontSize: '0.75rem',
                  cursor: 'pointer'
                }}
              >
                Python Editor
              </button>
              <button
                onClick={() => setActiveTab('ast')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  background: activeTab === 'ast' ? '#0284c7' : 'transparent',
                  color: '#fff',
                  border: 'none',
                  padding: '3px 8px',
                  borderRadius: '3px',
                  fontSize: '0.75rem',
                  cursor: 'pointer'
                }}
              >
                <FolderTree size={12} />
                <span>AST Explorer</span>
              </button>
            </div>
            <label className="diagram-upload-btn">
              <UploadCloud size={16} />
              <span>Attach Architecture Diagram</span>
              <input 
                type="file" 
                accept="image/png, image/jpeg, image/webp" 
                onChange={handleDiagramUpload} 
                style={{ display: 'none' }} 
              />
            </label>
          </div>

          <div className="editor-frame">
            {activeTab === 'editor' ? (
              <Editor
                height="100%"
                width="100%"
                defaultLanguage="python"
                theme="vs-dark"
                defaultValue={INITIAL_CODE}
                onMount={handleEditorMount}
                onChange={handleEditorChange}
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  automaticLayout: true
                }}
              />
            ) : (
              <div style={{ padding: '16px', height: '100%', overflowY: 'auto', background: '#0f172a' }}>
                <h3 style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '10px' }}>
                  Parsed Syntax Tree (Click nodes to locate line in editor)
                </h3>
                {ast.tree_nodes && ast.tree_nodes.length > 0 ? (
                  ast.tree_nodes.map((node, idx) => (
                    <ASTNodeView 
                      key={idx} 
                      node={node} 
                      onSelectLine={(line) => {
                        setActiveTab('editor');
                        setTimeout(() => jumpToLine(line), 50);
                      }} 
                    />
                  ))
                ) : (
                  <p style={{ color: '#64748b', fontSize: '0.8rem' }}>No syntax tree available.</p>
                )}
              </div>
            )}
          </div>
        </section>

        <section className="review-column">
          {diagramBase64 && (
            <div className="review-card">
              <div className="card-header">
                <Layers size={18} color="#38bdf8" />
                <span>Uploaded Architecture Reference</span>
              </div>
              <img src={diagramBase64} alt="Architecture" className="diagram-preview-box" />
            </div>
          )}

          <div className="review-card">
            <div className="card-header">
              <CheckCircle2 size={18} color="#4ade80" />
              <span>Structural AST Metrics</span>
            </div>
            <div className="metric-grid">
              <div className="metric-pill">
                <span className="metric-label">Lines</span>
                <span className="metric-value">{ast.metrics?.total_lines ?? 0}</span>
              </div>
              <div className="metric-pill">
                <span className="metric-label">Functions</span>
                <span className="metric-value">{ast.metrics?.function_count ?? 0}</span>
              </div>
              <div className="metric-pill">
                <span className="metric-label">Imports</span>
                <span className="metric-value">{ast.metrics?.import_count ?? 0}</span>
              </div>
              <div className="metric-pill">
                <span className="metric-label">Warnings</span>
                <span className="metric-value">{ast.metrics?.warning_count ?? 0}</span>
              </div>
            </div>
          </div>

          <div className="review-card">
            <div className="card-header">
              <ShieldAlert size={18} color="#f87171" />
              <span>Structural Flags & Warnings ({ast.warnings?.length || 0})</span>
            </div>
            {ast.warnings?.length > 0 ? (
              ast.warnings.map((w, idx) => (
                <div key={idx} className="warning-item" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong>Line {w.line}: {w.type}</strong>
                    <button
                      onClick={() => handleAutoFix(w)}
                      disabled={fixingLine === w.line}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        background: '#0284c7',
                        border: 'none',
                        color: '#fff',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.72rem',
                        cursor: 'pointer'
                      }}
                    >
                      <Wand2 size={11} />
                      <span>{fixingLine === w.line ? 'Fixing...' : 'Fix Issue'}</span>
                    </button>
                  </div>
                  <span>{w.message}</span>
                </div>
              ))
            ) : (
              <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>No AST code structure warnings detected.</p>
            )}
          </div>

          <div className="review-card">
            <div className="card-header">
              <Layers size={18} color="#c084fc" />
              <span>Architecture Drift & Components</span>
            </div>
            <div className="tag-list" style={{ marginBottom: '10px' }}>
              {architecture.diagram_components?.map((c, idx) => (
                <span key={idx} className="tag-badge">{c}</span>
              ))}
            </div>
            {architecture.architecture_drift?.map((drift, idx) => (
              <div key={idx} className="warning-item" style={{ borderColor: '#eab308' }}>
                <strong style={{ color: '#facc15' }}>{drift.type}</strong>
                <span>{drift.message}</span>
              </div>
            ))}
          </div>

          <div className="review-card">
            <div className="card-header">
              <BookOpen size={18} color="#38bdf8" />
              <span>FAISS Matched Best Practice Rules ({relevant_rules?.length || 0})</span>
            </div>
            {relevant_rules?.length > 0 ? (
              relevant_rules.map((rule) => (
                <div key={rule.id} className="rule-item">
                  <h4>{rule.id} - {rule.title}</h4>
                  <p>{rule.content}</p>
                </div>
              ))
            ) : (
              <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>No specific rules flagged for current code.</p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
