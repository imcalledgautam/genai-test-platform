# GenAI Test Platform - Tests

This directory contains tests for the GenAI Test Platform itself.

## Structure

- `unit/` - Unit tests for individual components
- `integration/` - Integration tests for full workflows
- `generated/` - Directory where AI-generated tests will be placed (auto-created)

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tools --cov=llm_agent

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

## Test Categories

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test complete workflows and component interactions
- **Generated Tests**: AI-generated tests for demonstration and validation