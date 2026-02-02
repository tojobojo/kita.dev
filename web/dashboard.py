"""
Kita.dev Web Dashboard
Bible II Section 10: Web Module - Minimal dashboard UI.
"""
import os
import json
import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Kita.dev Dashboard",
    description="Monitoring and configuration dashboard for Kita.dev",
    version="0.1.0"
)

# Data models
class TaskRecord(BaseModel):
    id: str
    task: str
    repo: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    final_state: Optional[str] = None
    token_usage: Optional[int] = None
    confidence_score: Optional[float] = None

class ConfigUpdate(BaseModel):
    key: str
    value: str

# In-memory task history (would be database in production)
task_history: List[TaskRecord] = []

# --- API Endpoints ---

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/tasks")
async def get_tasks(limit: int = 50) -> List[dict]:
    """Get recent task history."""
    return [t.dict() for t in task_history[-limit:]]

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    """Get a specific task by ID."""
    for task in task_history:
        if task.id == task_id:
            return task.dict()
    raise HTTPException(status_code=404, detail="Task not found")

@app.post("/api/tasks")
async def record_task(task: TaskRecord) -> dict:
    """Record a new task (called by agent controller)."""
    task_history.append(task)
    logger.info(f"Recorded task: {task.id} - {task.status}")
    return {"success": True, "id": task.id}

@app.get("/api/config")
async def get_config() -> dict:
    """Get current configuration."""
    config_path = Path(__file__).parent.parent / "config" / "default.yaml"
    
    if not config_path.exists():
        return {"error": "Config file not found"}
    
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

@app.put("/api/config")
async def update_config(update: ConfigUpdate) -> dict:
    """Update a configuration value."""
    # In production, this would validate and persist changes
    logger.info(f"Config update requested: {update.key} = {update.value}")
    return {"success": True, "message": "Config update noted (not persisted in V0)"}

@app.get("/api/metrics")
async def get_metrics() -> dict:
    """Get system metrics."""
    total_tasks = len(task_history)
    completed = sum(1 for t in task_history if t.final_state == "COMPLETED")
    stopped_safe = sum(1 for t in task_history if t.final_state == "STOPPED_SAFE")
    stopped_error = sum(1 for t in task_history if t.final_state == "STOPPED_ERROR")
    
    return {
        "total_tasks": total_tasks,
        "completed": completed,
        "stopped_safe": stopped_safe,
        "stopped_error": stopped_error,
        "success_rate": completed / total_tasks if total_tasks > 0 else 0,
        "stop_rate": (stopped_safe + stopped_error) / total_tasks if total_tasks > 0 else 0,
    }

# --- Static Files & HTML ---

# Serve static files from web/static directory
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard page."""
    html_path = Path(__file__).parent / "templates" / "dashboard.html"
    
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    
    # Fallback inline HTML if template doesn't exist
    return HTMLResponse(content=get_inline_dashboard_html())

def get_inline_dashboard_html() -> str:
    """Returns inline dashboard HTML for when templates aren't available."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kita.dev Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        header {
            display: flex; justify-content: space-between; align-items: center;
            padding: 1.5rem 2rem;
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            margin-bottom: 2rem;
        }
        .logo { font-size: 1.8rem; font-weight: 700; color: #00d4ff; }
        .status-badge {
            padding: 0.5rem 1rem;
            background: linear-gradient(135deg, #00c853 0%, #00e676 100%);
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 40px rgba(0,212,255,0.2);
        }
        .metric-value { font-size: 2.5rem; font-weight: 700; color: #00d4ff; }
        .metric-label { color: #888; margin-top: 0.5rem; }
        .section-title {
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #fff;
        }
        .task-table {
            width: 100%;
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .task-table th, .task-table td {
            padding: 1rem 1.5rem;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .task-table th {
            background: rgba(0,212,255,0.1);
            font-weight: 600;
            color: #00d4ff;
        }
        .task-table tr:hover { background: rgba(255,255,255,0.03); }
        .status-completed { color: #00e676; }
        .status-stopped-safe { color: #ffd600; }
        .status-stopped-error { color: #ff5252; }
        .status-running { color: #00d4ff; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
        .config-section {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 2rem;
            margin-top: 2rem;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .config-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .config-key { font-weight: 500; }
        .config-value { 
            color: #00d4ff;
            font-family: 'Monaco', monospace;
            font-size: 0.9rem;
        }
        .refresh-btn {
            background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            color: #fff;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .refresh-btn:hover { transform: scale(1.05); }
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">⚡ Kita.dev</div>
            <span class="status-badge" id="system-status">Loading...</span>
        </header>
        
        <div class="metrics-grid" id="metrics">
            <div class="metric-card">
                <div class="metric-value" id="total-tasks">-</div>
                <div class="metric-label">Total Tasks</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="completed">-</div>
                <div class="metric-label">Completed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="success-rate">-</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="stop-rate">-</div>
                <div class="metric-label">Stop Rate</div>
            </div>
        </div>
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h2 class="section-title">Task History</h2>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
        </div>
        
        <table class="task-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Task</th>
                    <th>Repository</th>
                    <th>Status</th>
                    <th>Tokens</th>
                    <th>Confidence</th>
                    <th>Started</th>
                </tr>
            </thead>
            <tbody id="task-list">
                <tr><td colspan="7" class="empty-state">Loading tasks...</td></tr>
            </tbody>
        </table>
        
        <div class="config-section">
            <h2 class="section-title">Configuration</h2>
            <div id="config-list">
                <div class="empty-state">Loading configuration...</div>
            </div>
        </div>
    </div>
    
    <script>
        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                const data = await res.json();
                document.getElementById('total-tasks').textContent = data.total_tasks;
                document.getElementById('completed').textContent = data.completed;
                document.getElementById('success-rate').textContent = 
                    (data.success_rate * 100).toFixed(1) + '%';
                document.getElementById('stop-rate').textContent = 
                    (data.stop_rate * 100).toFixed(1) + '%';
            } catch (e) {
                console.error('Failed to fetch metrics:', e);
            }
        }
        
        async function fetchTasks() {
            try {
                const res = await fetch('/api/tasks');
                const tasks = await res.json();
                const tbody = document.getElementById('task-list');
                
                if (tasks.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No tasks yet</td></tr>';
                    return;
                }
                
                tbody.innerHTML = tasks.map(t => `
                    <tr>
                        <td>${t.id.substring(0, 8)}</td>
                        <td>${t.task.substring(0, 50)}${t.task.length > 50 ? '...' : ''}</td>
                        <td>${t.repo}</td>
                        <td class="status-${(t.final_state || 'running').toLowerCase().replace('_', '-')}">${t.final_state || 'Running'}</td>
                        <td>${t.token_usage || '-'}</td>
                        <td>${t.confidence_score ? t.confidence_score.toFixed(2) : '-'}</td>
                        <td>${new Date(t.started_at).toLocaleString()}</td>
                    </tr>
                `).join('');
            } catch (e) {
                console.error('Failed to fetch tasks:', e);
            }
        }
        
        async function fetchConfig() {
            try {
                const res = await fetch('/api/config');
                const config = await res.json();
                const container = document.getElementById('config-list');
                
                const renderConfig = (obj, prefix = '') => {
                    return Object.entries(obj).map(([k, v]) => {
                        const key = prefix ? `${prefix}.${k}` : k;
                        if (typeof v === 'object' && v !== null && !Array.isArray(v)) {
                            return renderConfig(v, key);
                        }
                        return `
                            <div class="config-item">
                                <span class="config-key">${key}</span>
                                <span class="config-value">${JSON.stringify(v)}</span>
                            </div>
                        `;
                    }).flat().join('');
                };
                
                container.innerHTML = renderConfig(config);
            } catch (e) {
                console.error('Failed to fetch config:', e);
            }
        }
        
        async function checkHealth() {
            try {
                const res = await fetch('/api/health');
                const data = await res.json();
                document.getElementById('system-status').textContent = 
                    data.status === 'healthy' ? '● Healthy' : '● Unhealthy';
            } catch (e) {
                document.getElementById('system-status').textContent = '● Offline';
                document.getElementById('system-status').style.background = 
                    'linear-gradient(135deg, #ff5252 0%, #ff1744 100%)';
            }
        }
        
        function refreshData() {
            fetchMetrics();
            fetchTasks();
            fetchConfig();
            checkHealth();
        }
        
        // Initial load
        refreshData();
        
        // Auto-refresh every 10 seconds
        setInterval(refreshData, 10000);
    </script>
</body>
</html>
"""

# Entry point for running standalone
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
