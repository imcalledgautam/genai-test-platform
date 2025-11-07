# Legacy LLM Agent Components

This directory contains the original LLM agent implementation that has been superseded by the unified GenAI Test Platform.

## Superseded by:
- `tools/genai_test_runner.py` - Unified test runner with LLM integration
- `tools/context_builder.py` - Enhanced context building
- `tools/policy_checker.py` - Production policy validation

## Migration Notes:
The new unified approach provides:
- Stack-agnostic detection and execution
- Better error handling and logging  
- Stricter policy enforcement
- Comprehensive artifact collection
- GitHub Actions integration

Use the tools in `/tools/` directory instead of this legacy implementation.