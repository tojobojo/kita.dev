from typing import List
from agent.executor import ExecutionResult

class ConfidenceEvaluator:
    """
    Bible III, Section 8: Confidence Evaluation
    Quantify trustworthiness.
    Confidence in [0, 1].
    Low confidence -> STOP.
    """
    
    def evaluate(self, run_history: List[ExecutionResult]) -> float:
        """
        Calculates confidence score based on execution history.
        """
        if not run_history:
            return 1.0 # Optimistic start
            
        total_steps = len(run_history)
        failed_steps = len([r for r in run_history if not r.success])
        
        # Simple heuristic: Success rate
        success_rate = (total_steps - failed_steps) / total_steps
        
        # Penalize slightly for any failure even if retried successfully (mock logic)
        score = success_rate * 0.9 if failed_steps > 0 else 1.0
        
        return max(0.0, min(1.0, score))
