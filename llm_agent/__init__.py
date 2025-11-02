"""
GenAI Test Platform - LLM Agent Package

This package contains the core components for automatically generating
test cases using Large Language Models (specifically Ollama/Qwen).

Components:
- context_builder: Gathers git diffs, file contents, and repo context
- generate_tests: Calls LLM to generate pytest test cases
- prompt_template.txt: Standardized prompt for consistent test generation
"""

__version__ = "0.1.0"
__author__ = "GenAI Test Platform"