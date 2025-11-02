# GenAI Test Platform - LLM Agent

This folder contains the LLM agent components for generating tests automatically.

## Components

### `prompt_template.txt`
The prompt template that guides the LLM to generate appropriate pytest test cases. The template ensures:
- Focus on functional unit tests and regression tests
- Target only changed code and direct dependencies
- Include both positive and negative test cases
- Follow pytest best practices

### `context_builder.py`
Builds a comprehensive context bundle containing:
- Git diffs of changed files
- Full text of changed Python files
- Directly imported helper modules (shallow dependencies)
- Repository context (README, requirements, sample data)

**Usage:**
```bash
python llm_agent/context_builder.py
```

Output: `ci_artifacts/context_bundle.json`

### `generate_tests.py`
Calls the local Ollama instance with the context bundle and generates test files.

**Environment Variables:**
- `OLLAMA_MODEL`: Model to use (default: `qwen2.5-coder:7b`)
- `OLLAMA_HOST`: Ollama server URL (default: `http://localhost:11434`)

**Usage:**
```bash
python llm_agent/generate_tests.py
```

Output: `tests/generated/test_generated_YYYYMMDD_HHMMSS.py`

## Prerequisites

1. **Ollama Installation:**
   ```bash
   # Install Ollama (visit https://ollama.ai for platform-specific instructions)
   ollama pull qwen2.5-coder:7b
   ollama serve
   ```

2. **Python Dependencies:**
   ```bash
   pip install requests
   ```

## Quick Start

1. **Build context bundle:**
   ```bash
   python llm_agent/context_builder.py
   ```

2. **Generate tests (requires Ollama):**
   ```bash
   python llm_agent/generate_tests.py
   ```

3. **Or use the helper script:**
   ```bash
   python run_local_agent.py
   ```

## CI Integration

The context builder is integrated into the GitHub Actions workflow and will produce a `context-bundle` artifact that can be downloaded and used locally with the generator.

## Output Structure

Generated test files follow this naming pattern:
- `tests/generated/test_generated_YYYYMMDD_HHMMSS.py`

Each file contains pytest test cases targeting the changed code with:
- Positive test cases
- Negative/edge case testing  
- Exception path testing
- Isolated, deterministic tests