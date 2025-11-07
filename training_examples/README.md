# Training Examples Metadata

This directory contains curated examples of good and bad test patterns for training LLM test generation.

## Structure

```
training_examples/
  metadata.json           # Central metadata registry
  python/
    good/
      calc_sum_test.py.ex1        # Good: Clear, deterministic unit test
      api_routes_test.py.ex2      # Good: Proper mocking and assertions
      edge_cases_test.py.ex3      # Good: Comprehensive edge case coverage
    bad/
      flaky_sleep_test.py.ex1     # Bad: Uses sleep, non-deterministic
      mocks_leaking_state.py.ex2  # Bad: Shared state between tests
      vague_assertions.py.ex3     # Bad: Generic assertions, unclear intent
  node/
    good/
      userService.spec.js.ex1     # Good: Jest best practices
      async_handler.test.js.ex2   # Good: Proper async testing
    bad/
      brittle_dom_selectors.spec.js.ex1  # Bad: Fragile DOM dependencies
  java/
    good/
      UserServiceTest.java.ex1    # Good: JUnit 5 best practices
    bad/
      SingletonSharedStateTest.java.ex1  # Bad: Singleton pollution
```

## Usage

1. **Few-shot prompting**: Include relevant good examples in LLM prompts
2. **Policy validation**: Use bad examples to train rejection filters  
3. **Fine-tuning**: Optional training data for domain-specific models
4. **Human review**: Reference examples for HITL validation

## Metadata Schema

Each example has associated metadata:

```json
{
  "file": "calc_sum_test.py.ex1",
  "category": "good|bad",
  "language": "python|node|java", 
  "test_type": "unit|integration|e2e",
  "principles": ["deterministic", "isolated", "AAA", "clear_asserts"],
  "violations": ["uses_sleep", "network_calls", "shared_state"],
  "tags": ["arithmetic", "edge_cases", "error_handling"],
  "complexity": "simple|medium|complex",
  "framework": "pytest|jest|junit"
}
```

## Quality Principles

### Good Test Characteristics
- **Deterministic**: Same input always produces same result
- **Isolated**: No dependencies on other tests or external state
- **Fast**: Executes quickly without unnecessary delays
- **Clear**: Intent and expectations are obvious
- **Maintainable**: Easy to understand and modify

### Anti-patterns to Avoid
- Sleep statements or time-based waits
- Network calls to real services
- File system operations outside temp directories
- Shared global state between tests
- Non-deterministic data generation without seeds
- Vague assertions (e.g., `assert True`)