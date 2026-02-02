import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TokenUsage:
    """Tracks token usage for a single request."""
    input_tokens: int
    output_tokens: int
    total_tokens: int

class BudgetTracker:
    """
    Tracks token budget across agent execution.
    Appendix D: Cost, Token & Compute Budget Law
    """
    
    # Appendix D Section 3: Default Budgets
    DEFAULT_TOKEN_BUDGET = 120000
    # Appendix D Section 4: Hard Ceilings
    HARD_CEILING = 250000
    
    def __init__(self, budget: int = DEFAULT_TOKEN_BUDGET):
        self.initial_budget = min(budget, self.HARD_CEILING)
        self.remaining_budget = self.initial_budget
        self.total_used = 0
        self.request_count = 0
        
    def consume(self, tokens: int) -> bool:
        """
        Consumes tokens from budget.
        Returns True if budget remains, False if exhausted.
        """
        self.total_used += tokens
        self.remaining_budget -= tokens
        self.request_count += 1
        
        if self.remaining_budget < 0:
            logger.warning(f"Budget exhausted! Used {self.total_used}/{self.initial_budget}")
            return False
        return True
    
    def can_afford(self, estimated_tokens: int) -> bool:
        """Checks if budget can afford estimated token usage."""
        return self.remaining_budget >= estimated_tokens
    
    def get_usage_summary(self) -> dict:
        """Returns usage summary for logging/PR."""
        return {
            "total_tokens_used": self.total_used,
            "initial_budget": self.initial_budget,
            "remaining_budget": max(0, self.remaining_budget),
            "request_count": self.request_count,
            "budget_utilization": self.total_used / self.initial_budget if self.initial_budget > 0 else 0
        }

class LLMClient(ABC):
    """
    Abstract Base Class for LLM Providers.
    """
    
    def __init__(self):
        self.last_usage: Optional[TokenUsage] = None
        self.budget_tracker: Optional[BudgetTracker] = None
    
    def set_budget_tracker(self, tracker: BudgetTracker):
        """Attaches a budget tracker to this client."""
        self.budget_tracker = tracker
    
    @abstractmethod
    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.0) -> str:
        """
        Send a completion request to the LLM.
        """
        pass
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimate: 4 characters per token."""
        return len(text) // 4

class LiteLLMClient(LLMClient):
    """
    Client using the litellm library for broad model support (OpenAI, Anthropic, Vertex, etc.).
    Requires appropriate API keys in environment variables (e.g. OPENAI_API_KEY, ANTHROPIC_API_KEY).
    """
    
    def __init__(self, model: str = "gpt-4-turbo"):
        super().__init__()
        self.model = model
        try:
            import litellm
            self.litellm = litellm
            # Optional: Configure litellm to drop params not supported by provider
            self.litellm.drop_params = True 
        except ImportError:
            logger.error("litellm package not installed. Please run `pip install litellm`.")
            self.litellm = None

    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.0) -> str:
        if not self.litellm:
             raise RuntimeError("litellm library not found.")

        try:
            response = self.litellm.completion(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            
            # Track token usage
            usage = response.usage
            if usage:
                self.last_usage = TokenUsage(
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens
                )
                
                # Consume from budget if tracker attached
                if self.budget_tracker:
                    if not self.budget_tracker.consume(usage.total_tokens):
                        logger.warning("Token budget exhausted during LLM call")
                        
                logger.info(f"LLM tokens used: {usage.total_tokens} (in: {usage.prompt_tokens}, out: {usage.completion_tokens})")
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LiteLLM Error: {e}")
            raise

class MockLLMClient(LLMClient):
    """
    For testing without costs.
    """
    def __init__(self):
        super().__init__()
        
    def complete(self, messages: List[Dict[str, str]], temperature: float = 0.0) -> str:
        # Mock token usage
        mock_response = """
        {
            "steps": [
                {
                    "id": 1,
                    "description": "Echo hello world to verify execution",
                    "action_type": "COMMAND",
                    "target": "echo hello world",
                    "details": ""
                }
            ],
            "strategy": "Run tests"
        }
        """
        
        # Track mock token usage
        input_tokens = sum(self.estimate_tokens(m.get('content', '')) for m in messages)
        output_tokens = self.estimate_tokens(mock_response)
        self.last_usage = TokenUsage(input_tokens, output_tokens, input_tokens + output_tokens)
        
        if self.budget_tracker:
            self.budget_tracker.consume(input_tokens + output_tokens)
            
        return mock_response

