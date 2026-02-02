import logging
import time
from typing import Optional

from agent.state_machine import StateMachine, AgentState, TransitionError
from agent.planner import Planner, Plan
from agent.executor import AgentExecutor
from agent.reflection import ReflectionEngine, Decision
from agent.confidence import ConfidenceEvaluator
from context.indexer import RepoIndexer
from context.language_detector import LanguageDetector
from guardrails.validators import TaskValidator

logger = logging.getLogger(__name__)

class AgentController:
    """
    Bible II, Section 2: Controller
    Orchestrates the full autonomous lifecycle:
    task -> plan -> execute -> test -> reflect -> stop/complete.
    """
    
    def __init__(self):
        self.state_machine = StateMachine()
        self.planner = Planner()
        self.executor = AgentExecutor()
        self.reflection = ReflectionEngine()
        self.confidence = ConfidenceEvaluator()
        self.indexer = RepoIndexer()
        self.language_detector = LanguageDetector()
        self.task_validator = TaskValidator()
        
        # Runtime state
        self.current_plan: Optional[Plan] = None
        self.execution_history = [] # List of ExecutionResults
        self.detected_language: Optional[str] = None

    def run(self, task: str, repo_path: str) -> AgentState:
        """
        Executes a task on a repository.
        Returns the final state (COMPLETED, STOPPED_SAFE, STOPPED_ERROR).
        """
        try:
            # 1. Start -> RECEIVED_TASK
            self.state_machine.transition_to(AgentState.RECEIVED_TASK, "Task received")
            
            # 2. Normalize -> NORMALIZED
            # Includes task validation (Bible III soft checks)
            validation = self.task_validator.validate_task(task)
            if not validation.passed:
                logger.warning(f"Task validation failed: {validation.blockers}")
                self.state_machine.transition_to(AgentState.NORMALIZED, "Task normalized (with warnings)")
                self.state_machine.transition_to(AgentState.STOPPED_SAFE, f"Task validation failed: {validation.blockers}")
                return AgentState.STOPPED_SAFE
            self.state_machine.transition_to(AgentState.NORMALIZED, "Task normalized")
            
            # 3. Context Building (Index + Language Detection per Appendix F)
            self.state_machine.transition_to(AgentState.CONTEXT_BUILDING, "Indexing repository")
            repo_context = ""
            try:
                # Language detection first (Appendix F)
                lang_result = self.language_detector.detect(repo_path)
                self.detected_language = lang_result.primary_language
                
                if not lang_result.supported:
                    logger.warning(f"Unsupported language: {lang_result.reason}")
                    self.state_machine.force_error_stop(f"Unsupported language: {lang_result.reason}")
                    return AgentState.STOPPED_ERROR
                
                logger.info(f"Detected language: {lang_result.primary_language} (confidence: {lang_result.confidence:.2f})")
                
                # Index repository
                repo_context = self.indexer.index(repo_path)
                self.state_machine.transition_to(AgentState.CONTEXT_READY, "Context indexed")
            except Exception as e:
                # Context failure -> Error
                logger.error(f"Context build failed: {e}")
                self.state_machine.force_error_stop(f"Context failure: {e}")
                return AgentState.STOPPED_ERROR

            # 4. Plan (Now with Context)
            self.state_machine.transition_to(AgentState.PLANNING, "Starting planning")
            try:
                self.current_plan = self.planner.generate_plan(task, repo_context)
                self.state_machine.transition_to(AgentState.PLAN_VALIDATED, "Plan generated and validated")
            except Exception as e:
                logger.error(f"Planning failed: {e}")
                self.state_machine.transition_to(AgentState.STOPPED_SAFE, f"Planning failure: {e}")
                return AgentState.STOPPED_SAFE


            # 5. Execution Loop
            self.state_machine.transition_to(AgentState.EXECUTING_STEP, "Starting execution loop")
            
            for step in self.current_plan.steps:
                # If we ever re-enter execution from retry, we are here.
                # Note: This simple loop doesn't fully support the "RETRYING -> EXECUTING_STEP" 
                # jump logic for *re-doing* a step in this V0 skeleton cleanly without a while loop, 
                # but let's implement the standard single-pass flow with reflection.
                
                # Check allowed state (in case reflection stopped us)
                if self.state_machine.current_state in [AgentState.STOPPED_SAFE, AgentState.STOPPED_ERROR]:
                    break
                
                # Ensure we are in execution state
                if self.state_machine.current_state != AgentState.EXECUTING_STEP:
                     if self.state_machine.current_state == AgentState.RETRYING:
                         self.state_machine.transition_to(AgentState.EXECUTING_STEP, "Retrying step")
                     else:
                        # Should not happen in linear flow
                        pass

                result = self.executor.execute_step(step, repo_path)
                self.execution_history.append(result)
                
                if result.success:
                    self.state_machine.transition_to(AgentState.STEP_COMPLETED, f"Step {step.id} success")
                    # Transition back to executing for next step? 
                    # Bible IV state machine: STEP_COMPLETED -> TESTING. 
                    # This implies we test *after each step* or *after all steps*? 
                    # "EXECUTING_STEP -> STEP_COMPLETED -> TESTING"
                    # If we have multiple steps, we likely cycle EXECUTING -> COMPLETED -> EXECUTING.
                    # But Bible IV allows EXECUTING -> STEP_COMPLETED.
                    # It does NOT explicitly show STEP_COMPLETED -> EXECUTING_STEP.
                    # It shows RETRYING -> EXECUTING_STEP.
                    # Let's assume for V0 phase 5 we execute ALL steps then test.
                    # To do that we need to remain in EXECUTING_STEP or transition lightly.
                    # Actually, if we look at Bible IV strictly:
                    # EXECUTING_STEP -> STEP_COMPLETED
                    # STEP_COMPLETED -> TESTING
                    # This suggests a step-by-step verification model or the "Step" covers the whole plan?
                    # "Executor runs exactly one step."
                    # Let's assume we do STEP_COMPLETED, then immediately back to EXECUTING_STEP if more steps?
                    # BUT that transition is NOT in ALLOWED_TRANSITIONS explicitly.
                    # "EXECUTING_STEP -> STEP_COMPLETED"
                    # "STEP_COMPLETED -> TESTING"
                    # If we have 5 steps, we can't go STEP_COMPLETED -> EXECUTING_STEP.
                    # This suggests the State Machine treats "EXECUTING_STEP" as the state of *doing the work*, 
                    # and "STEP_COMPLETED" as *finished all work* for the moment?
                    # OR we just hold EXECUTING_STEP state while doing internal loop?
                    # "Executor runs exactly one step." implies fine granularity.
                    # Let's HOLD `EXECUTING_STEP` until all steps are done, only emitting logs, 
                    # OR we force a transition loop that strictly follows the enum.
                    # Since STEP_COMPLETED -> EXECUTING_STEP is forbidden, we MUST stay in EXECUTING_STEP 
                    # until the entire plan is done, OR the "Plan" is just one meta-step.
                    # Let's stay in EXECUTING_STEP for the loop to satisfy "Forbidden Transitions".
                    pass
                else:
                    # Failure
                    # EXECUTING -> TESTS_FAILED (mapped to runtime failure here)
                    self.state_machine.transition_to(AgentState.TESTS_FAILED, f"Step {step.id} failed: {result.error}")
                    self.state_machine.transition_to(AgentState.REFLECTING, "Analyzing failure")
                    
                    decision = self.reflection.reflect(result)
                    
                    if decision.decision == Decision.RETRY:
                        self.state_machine.transition_to(AgentState.RETRYING, decision.reason)
                        # In a real agent we would modify plan/context here.
                        # For V0 loop, we transition back to Executing and Retry *the same step* or continue?
                        # Let's say we retry.
                        self.state_machine.transition_to(AgentState.EXECUTING_STEP, "Retrying execution")
                        # (In this skeleton, we won't infinite loop, just move on or retry logic)
                        continue 
                    else:
                        self.state_machine.transition_to(AgentState.STOPPED_SAFE, decision.reason)
                        return AgentState.STOPPED_SAFE

            # 6. Testing (Final)
            if self.state_machine.current_state == AgentState.EXECUTING_STEP:
                 self.state_machine.transition_to(AgentState.STEP_COMPLETED, "All steps executed")
            
            if self.state_machine.current_state == AgentState.STEP_COMPLETED:
                self.state_machine.transition_to(AgentState.TESTING, "Running final verification")
                
                # Mock Test Runner
                # In real life: sandbox.run_tests()
                tests_passed = True # Mock
                
                if tests_passed:
                    self.state_machine.transition_to(AgentState.TESTS_PASSED, "All tests passed")
                    self.state_machine.transition_to(AgentState.COMPLETED, "Task successfully finished")
                else:
                    self.state_machine.transition_to(AgentState.TESTS_FAILED, "Verification failed")
                    self.state_machine.transition_to(AgentState.REFLECTING, "Analyzing test failure")
                    # ... Reflection loop could happen here too ...
                    self.state_machine.transition_to(AgentState.STOPPED_SAFE, "Tests failed after execution")

            return self.state_machine.current_state

        except TransitionError as e:
            logger.critical(f"State Machine Violation: {e}")
            self.state_machine.force_error_stop(str(e))
            return AgentState.STOPPED_ERROR
        except Exception as e:
            logger.critical(f"Unhandled Exception: {e}")
            self.state_machine.force_error_stop(str(e))
            return AgentState.STOPPED_ERROR

    def get_history(self):
        """
        Returns the execution history and state machine transitions.
        """
        return {
            "state": self.state_machine.current_state.value,
            "transitions": self.state_machine._execution_history,
            "execution_steps": [
                {
                    "success": res.success,
                    "output": res.output,
                    "error": res.error
                } for res in self.execution_history
            ]
        }
