import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import asyncio

from agent.controller import AgentController, AgentState

# Import middleware
from api.middleware import (
    setup_logging,
    RequestLoggingMiddleware,
    MetricsMiddleware,
    get_metrics_response,
    APIKeyMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    get_cors_origins,
)

# Setup logging based on environment
setup_logging()
logger = logging.getLogger("api")

# Create FastAPI app
app = FastAPI(
    title="Kita.dev Agent API",
    description="Autonomous coding agent with safety-first design",
    version="0.1.0",
    docs_url="/docs" if os.getenv("KITA_ENV") != "production" else None,
    redoc_url="/redoc" if os.getenv("KITA_ENV") != "production" else None,
)

# Add middleware (order matters - first added = outermost)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, rpm=int(os.getenv("RATE_LIMIT_RPM", "60")))
app.add_middleware(APIKeyMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (built React UI) in production
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Job Manager State
class JobManager:
    def __init__(self):
        self.controllers: Dict[str, AgentController] = {}
        self.results: Dict[str, str] = {}  # Job ID -> Final State
        self.task_records: List[dict] = []  # For dashboard history
        self.executor = ThreadPoolExecutor(max_workers=5)

    def create_job(
        self, api_key: str = None, model: str = None, api_base: str = None
    ) -> str:
        """
        Create a new job with optional BYOK support.

        Args:
            api_key: Optional API key for this job
            model: Optional model override for this job
            api_base: Optional custom API endpoint
        """
        job_id = str(uuid.uuid4())
        self.controllers[job_id] = AgentController(
            api_key=api_key, model=model, api_base=api_base
        )
        return job_id

    def get_controller(self, job_id: str) -> Optional[AgentController]:
        return self.controllers.get(job_id)

    def record_task(
        self,
        job_id: str,
        task: str,
        repo: str,
        final_state: str = None,
        tokens: int = None,
        confidence: float = None,
    ):
        """Record task for dashboard history."""
        record = {
            "id": job_id,
            "task": task,
            "repo": repo,
            "status": "running" if final_state is None else "completed",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": (
                None if final_state is None else datetime.utcnow().isoformat()
            ),
            "final_state": final_state,
            "token_usage": tokens,
            "confidence_score": confidence,
        }
        # Update existing or append
        for i, r in enumerate(self.task_records):
            if r["id"] == job_id:
                self.task_records[i] = record
                return
        self.task_records.append(record)


manager = JobManager()


# Models
class RunRequest(BaseModel):
    task: str
    repo_path: str
    # BYOK: Bring Your Own Key (optional - uses server key if not provided)
    api_key: Optional[str] = None  # Works with any provider (OpenAI, Anthropic, etc.)
    model: Optional[str] = None  # e.g. "gpt-4-turbo", "claude-3-opus"
    api_base: Optional[str] = (
        None  # Custom API endpoint (e.g., Azure OpenAI, local LLM)
    )


class JobStatusResponse(BaseModel):
    job_id: str
    state: str
    history: List[Dict]
    execution_steps: List[Dict]


# Background Task Wrapper
def run_agent_in_thread(job_id: str, task: str, repo_path: str):
    """
    Runs the agent in a background thread.
    BYOK keys are already configured in the controller at job creation.
    """
    logger.info(f"Starting job {job_id} for task: {task}")
    controller = manager.get_controller(job_id)
    if controller:
        try:
            final_state = controller.run(task, repo_path)
            manager.results[job_id] = final_state.value
            manager.record_task(job_id, task, repo_path, final_state.value)
            logger.info(f"Job {job_id} finished with state: {final_state}")
        except Exception as e:
            logger.error(f"Job {job_id} crashed: {e}")
            manager.results[job_id] = "CRASHED"
            manager.record_task(job_id, task, repo_path, "CRASHED")


@app.get("/")
async def root():
    """Redirect to dashboard."""
    return RedirectResponse(url="/dashboard")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/agent/run")
async def run_agent(request: RunRequest):
    """
    Submits a task to the agent. Returns a Job ID.
    Job runs in the background.

    BYOK Support: Optionally pass `api_key`, `model`, and `api_base`
    to use your own LLM configuration.
    """
    # Create job with BYOK support
    job_id = manager.create_job(
        api_key=request.api_key, model=request.model, api_base=request.api_base
    )

    # Record task as started
    manager.record_task(job_id, request.task, request.repo_path)

    # Submit to thread pool
    manager.executor.submit(
        run_agent_in_thread, job_id, request.task, request.repo_path
    )

    return {"job_id": job_id, "status": "submitted"}


@app.get("/agent/status/{job_id}", response_model=JobStatusResponse)
async def get_status(job_id: str):
    controller = manager.get_controller(job_id)
    if not controller:
        raise HTTPException(status_code=404, detail="Job not found")

    history = controller.get_history()

    return JobStatusResponse(
        job_id=job_id,
        state=history["state"],
        history=history["transitions"],
        execution_steps=history["execution_steps"],
    )


# --- Dashboard API Endpoints ---


@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/tasks")
async def get_tasks(limit: int = 50):
    """Get recent task history for dashboard."""
    return manager.task_records[-limit:]


@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics for dashboard."""
    total = len(manager.task_records)
    completed = sum(
        1 for t in manager.task_records if t.get("final_state") == "COMPLETED"
    )
    stopped_safe = sum(
        1 for t in manager.task_records if t.get("final_state") == "STOPPED_SAFE"
    )
    stopped_error = sum(
        1 for t in manager.task_records if t.get("final_state") == "STOPPED_ERROR"
    )

    return {
        "total_tasks": total,
        "completed": completed,
        "stopped_safe": stopped_safe,
        "stopped_error": stopped_error,
        "success_rate": completed / total if total > 0 else 0,
        "stop_rate": (stopped_safe + stopped_error) / total if total > 0 else 0,
    }


@app.get("/api/config")
async def get_config():
    """Get current configuration."""
    from pathlib import Path

    config_path = Path(__file__).parent.parent / "config" / "default.yaml"

    if not config_path.exists():
        return {"error": "Config file not found"}

    import yaml

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# --- Dashboard HTML ---

from fastapi.responses import HTMLResponse


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard UI (redirects to React UI in production)."""
    # In production, static files serve the React UI
    # This is a fallback for API-only mode
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Kita.dev Dashboard</title>
    <style>
        body { font-family: system-ui; background: #1a1a2e; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { text-align: center; }
        h1 { color: #00d4ff; }
        a { color: #00d4ff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ Kita.dev</h1>
        <p>API is running. <a href="/docs">View API Docs</a></p>
        <p>For full dashboard, run the React UI: <code>cd ui && npm run dev</code></p>
    </div>
</body>
</html>
""")


# --- Metrics Endpoint ---


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return get_metrics_response()
