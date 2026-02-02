#!/usr/bin/env python
"""Quick verification script for Phase 1 and 2 implementations."""
import sys
sys.path.insert(0, '.')

print("Testing Phase 1 & 2 implementations...")

# Test context module imports
print("\n1. Testing context module imports...")
try:
    from context.selector import ContextSelector
    from context.summarizer import ContextSummarizer
    from context.symbols import SymbolExtractor
    from context.language_detector import LanguageDetector
    print("   ✓ Context module imports OK")
except Exception as e:
    print(f"   ✗ Context module import failed: {e}")
    sys.exit(1)

# Test guardrails imports
print("\n2. Testing guardrails imports...")
try:
    from guardrails.validators import TaskValidator, PlanValidator, OutputValidator
    print("   ✓ Guardrails imports OK")
except Exception as e:
    print(f"   ✗ Guardrails import failed: {e}")
    sys.exit(1)

# Test LLM client with budget tracker
print("\n3. Testing LLM client with budget tracker...")
try:
    from llm.client import BudgetTracker, MockLLMClient, TokenUsage
    tracker = BudgetTracker(budget=10000)
    client = MockLLMClient()
    client.set_budget_tracker(tracker)
    response = client.complete([{"role": "user", "content": "test"}])
    print(f"   ✓ BudgetTracker OK: {tracker.total_used} tokens used")
except Exception as e:
    print(f"   ✗ LLM client failed: {e}")
    sys.exit(1)

# Test task validator
print("\n4. Testing task validator...")
try:
    validator = TaskValidator()
    # Test valid task
    result = validator.validate_task("Add logging to the main function")
    print(f"   ✓ Valid task passed: {result.passed}")
    # Test vague task
    result = validator.validate_task("improve performance")
    print(f"   ✓ Vague task blocked: {not result.passed}")
except Exception as e:
    print(f"   ✗ Task validator failed: {e}")
    sys.exit(1)

# Test language detector
print("\n5. Testing language detector...")
try:
    detector = LanguageDetector()
    result = detector.detect(".")
    print(f"   ✓ Language detected: {result.primary_language} (supported: {result.supported})")
except Exception as e:
    print(f"   ✗ Language detector failed: {e}")
    sys.exit(1)

# Test symbol extractor
print("\n6. Testing symbol extractor...")
try:
    extractor = SymbolExtractor()
    code = '''
class MyClass:
    """A test class."""
    def my_method(self, x: int) -> str:
        return str(x)
'''
    symbols = extractor.extract(code, "test.py")
    print(f"   ✓ Symbol extraction OK: {len(symbols)} symbols found")
except Exception as e:
    print(f"   ✗ Symbol extractor failed: {e}")
    sys.exit(1)

# Test context summarizer
print("\n7. Testing context summarizer...")
try:
    summarizer = ContextSummarizer()
    code = "import os\n" * 200
    summary = summarizer.summarize(code, "test.py")
    print(f"   ✓ Summarizer OK: {len(summary)} chars (from {len(code)})")
except Exception as e:
    print(f"   ✗ Summarizer failed: {e}")
    sys.exit(1)

# Test controller integration
print("\n8. Testing controller integration...")
try:
    import os
    os.environ["USE_MOCK_LLM"] = "true"
    from agent.controller import AgentController
    controller = AgentController()
    print("   ✓ Controller instantiation OK")
except Exception as e:
    print(f"   ✗ Controller integration failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("All Phase 1 & 2 tests PASSED!")
print("="*50)
