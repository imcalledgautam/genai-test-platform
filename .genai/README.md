# GenAI Test Platform

Automated test generation using AI.

## Usage

Manually trigger:
```bash
gh workflow run genai-testing.yml
```

With specific files:
```bash  
gh workflow run genai-testing.yml -f files="src/utils.py"
```

Auto-approve tests:
```bash
gh workflow run genai-testing.yml -f auto_approve=true
```

## Configuration

Edit `.genai/config.yml` to customize:
- Model selection
- File patterns 
- Quality thresholds

## Generated Tests

Tests are saved to `tests/generated_by_llm/`
