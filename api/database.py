"""
Database Module - PostgreSQL Integration for Task Persistence

Provides persistent storage for:
- Task history
- Job status
- Agent execution logs
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Optional PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logger.info("psycopg2 not installed. Using in-memory storage.")


@dataclass
class TaskRecord:
    """Represents a task in the database."""

    id: str
    task: str
    repo_path: str
    status: str
    created_at: datetime
    updated_at: datetime
    final_state: Optional[str] = None
    tokens_used: Optional[int] = None
    confidence_score: Optional[float] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None


class DatabaseManager:
    """
    Manages persistent storage.
    Falls back to in-memory if PostgreSQL is unavailable.
    """

    def __init__(self):
        self.connection_string = os.getenv("DATABASE_URL")
        self._memory_store: Dict[str, TaskRecord] = {}
        self._initialized = False

        if self.connection_string and POSTGRES_AVAILABLE:
            self._init_postgres()
        else:
            logger.info("Using in-memory task storage (no DATABASE_URL or psycopg2)")

    def _init_postgres(self):
        """Initialize PostgreSQL tables."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS tasks (
                            id VARCHAR(36) PRIMARY KEY,
                            task TEXT NOT NULL,
                            repo_path TEXT NOT NULL,
                            status VARCHAR(50) NOT NULL,
                            final_state VARCHAR(50),
                            tokens_used INTEGER,
                            confidence_score FLOAT,
                            execution_time_ms INTEGER,
                            error_message TEXT,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                        CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at DESC);
                    """)
                    conn.commit()
            self._initialized = True
            logger.info("PostgreSQL database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            logger.info("Falling back to in-memory storage")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = psycopg2.connect(self.connection_string)
        try:
            yield conn
        finally:
            conn.close()

    @property
    def is_persistent(self) -> bool:
        """Returns True if using PostgreSQL."""
        return self._initialized and POSTGRES_AVAILABLE and self.connection_string

    def create_task(self, task_id: str, task: str, repo_path: str) -> TaskRecord:
        """Create a new task record."""
        now = datetime.now(timezone.utc)
        record = TaskRecord(
            id=task_id,
            task=task,
            repo_path=repo_path,
            status="PENDING",
            created_at=now,
            updated_at=now,
        )

        if self.is_persistent:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO tasks (id, task, repo_path, status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                        (
                            record.id,
                            record.task,
                            record.repo_path,
                            record.status,
                            record.created_at,
                            record.updated_at,
                        ),
                    )
                    conn.commit()
        else:
            self._memory_store[task_id] = record

        return record

    def update_task(self, task_id: str, **updates) -> Optional[TaskRecord]:
        """Update task fields."""
        updates["updated_at"] = datetime.now(timezone.utc)

        if self.is_persistent:
            set_clause = ", ".join(f"{k} = %s" for k in updates.keys())
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE tasks SET {set_clause} WHERE id = %s
                    """,
                        (*updates.values(), task_id),
                    )
                    conn.commit()
            return self.get_task(task_id)
        else:
            if task_id in self._memory_store:
                record = self._memory_store[task_id]
                for k, v in updates.items():
                    if hasattr(record, k):
                        setattr(record, k, v)
                return record
        return None

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        """Retrieve a task by ID."""
        if self.is_persistent:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
                    row = cur.fetchone()
                    if row:
                        return TaskRecord(**row)
        else:
            return self._memory_store.get(task_id)
        return None

    def get_recent_tasks(self, limit: int = 50) -> List[TaskRecord]:
        """Get recent tasks ordered by creation time."""
        if self.is_persistent:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT * FROM tasks ORDER BY created_at DESC LIMIT %s
                    """,
                        (limit,),
                    )
                    return [TaskRecord(**row) for row in cur.fetchall()]
        else:
            tasks = list(self._memory_store.values())
            tasks.sort(key=lambda t: t.created_at, reverse=True)
            return tasks[:limit]

    def get_task_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics."""
        if self.is_persistent:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(CASE WHEN final_state = 'COMPLETED' THEN 1 END) as completed,
                            COUNT(CASE WHEN final_state = 'STOPPED_SAFE' THEN 1 END) as stopped_safe,
                            COUNT(CASE WHEN final_state = 'STOPPED_ERROR' THEN 1 END) as stopped_error,
                            AVG(tokens_used) as avg_tokens,
                            AVG(confidence_score) as avg_confidence
                        FROM tasks
                    """)
                    return dict(cur.fetchone())
        else:
            tasks = list(self._memory_store.values())
            return {
                "total": len(tasks),
                "completed": sum(1 for t in tasks if t.final_state == "COMPLETED"),
                "stopped_safe": sum(
                    1 for t in tasks if t.final_state == "STOPPED_SAFE"
                ),
                "stopped_error": sum(
                    1 for t in tasks if t.final_state == "STOPPED_ERROR"
                ),
                "avg_tokens": None,
                "avg_confidence": None,
            }


# Global database instance
db = DatabaseManager()
