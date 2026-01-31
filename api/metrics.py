from dataclasses import dataclass
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

@dataclass
class MetricsSummary:
    total_tasks: int
    completed_tasks: int
    stops: int
    retries: int
    stop_rate: float
    completion_rate: float
    retry_rate: float
    total_cost_tokens: int

class MetricsCollector:
    """
    Appendix C: Metrics & PMF Signals
    Collects core system metrics to enforce quality and safety.
    """
    
    def __init__(self):
        self._tasks_started = 0
        self._tasks_completed = 0
        self._stops = 0
        self._retries = 0
        self._tokens_used = 0
        
    def record_start(self):
        self._tasks_started += 1
        
    def record_success(self):
        self._tasks_completed += 1
        
    def record_stop(self, reason: str):
        self._stops += 1
        logger.warning(f"METRIC: STOPPED - {reason}")
        
    def record_retry(self):
        self._retries += 1
        
    def record_cost(self, tokens: int):
        self._tokens_used += tokens
        
    def get_summary(self) -> MetricsSummary:
        if self._tasks_started == 0:
            return MetricsSummary(0, 0, 0, 0, 0.0, 0.0, 0.0, 0)
            
        return MetricsSummary(
            total_tasks=self._tasks_started,
            completed_tasks=self._tasks_completed,
            stops=self._stops,
            retries=self._retries,
            stop_rate=self._stops / self._tasks_started,
            completion_rate=self._tasks_completed / self._tasks_started,
            retry_rate=self._retries / self._tasks_started,
            total_cost_tokens=self._tokens_used
        )
