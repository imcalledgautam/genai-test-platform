# GenAI Test Platform - Production Workflow Guide
## Complete End-to-End Test Generation & Validation Pipeline

🚀 **One Action Step for Every Repository**: `python tools/unified_test_runner.py`

## Architecture Overview

This production-ready system provides:
1. **Stack-agnostic test detection & execution**
2. **LLM-powered test generation with guardrails**
3. **Human-in-the-loop quality control**
4. **Pre-merge validation pipeline**
5. **Comprehensive reporting & artifacts**

## Core Components

### 1. Unified Test Runner (`tools/unified_test_runner.py`)
**The orchestrator that ties everything together**

```bash
# Single command for any repository
python tools/unified_test_runner.py

# With environment variables
GENAI_TEST_GEN=true python tools/unified_test_runner.py
```

**What it does:**
- ✅ Auto-detects stack (Python/Node/Java)
- ✅ Installs dependencies
- ✅ Builds LLM context
- ✅ Runs native test frameworks
- ✅ Collects coverage & artifacts
- ✅ Generates unified JSON report

### 2. Context Builder (`tools/context_builder_v2.py`)
**Prevents LLM hallucinations with ground truth**

```bash
# Standalone context building
python tools/context_builder_v2.py --verbose

# Output: genai_artifacts/context.json
```

**Extracts:**
- File structure & languages
- Public API surface (functions, classes, methods)
- Test conventions & frameworks
- Dependencies & build configuration

### 3. Policy Checker (`tools/policy_checker_v2.py`) 
**Enforces test quality guardrails**

```bash
# Check all tests
python tools/policy_checker_v2.py tests/

# Check specific file
python tools/policy_checker_v2.py tests/test_example.py

# Generate JSON report
python tools/policy_checker_v2.py tests/ --format json --output policy_report.json
```

**Validates:**
- ❌ No flaky patterns (sleep, random, network)
- ✅ Deterministic behavior
- ✅ Proper isolation & mocking
- ✅ Clear assertions
- ✅ Valid imports & syntax

### 4. HITL Validator (`tools/hitl_validator_v2.py`)
**Human-in-the-loop review workflow**

```bash
# List pending reviews
python tools/hitl_validator_v2.py list

# Approve review
python tools/hitl_validator_v2.py approve review_123 --reviewer "Alice"

# Reject review
python tools/hitl_validator_v2.py reject review_123 --reviewer "Alice" --reason "Missing edge cases"

# Check status
python tools/hitl_validator_v2.py status review_123
```

**Creates:**
- Structured review artifacts (JSON + Markdown)
- Human-readable checklists
- Approval/rejection tracking
- Reviewer accountability

### 5. Evaluation Harness (`tools/evaluation_harness_v2.py`)
**Pre-merge validation pipeline**

```bash
# Evaluate test files
python tools/evaluation_harness_v2.py tests/test_*.py

# Strict mode (all checks must pass)
python tools/evaluation_harness_v2.py tests/test_*.py --strict

# Custom output
python tools/evaluation_harness_v2.py tests/test_*.py --output evaluation.json
```

**Validates:**
- Syntax & compilation
- Policy compliance
- Import availability
- Execution in sandbox
- Performance characteristics
- HITL approval status

## Complete Workflow

### For CI/CD Integration

```yaml
# .github/workflows/genai-tests.yml
name: GenAI Test Pipeline

on: [pull_request]

jobs:
  genai-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run Unified GenAI Test Runner
        run: python tools/unified_test_runner.py
        env:
          GENAI_TEST_GEN: "true"
      
      - name: Upload GenAI artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: genai-artifacts
          path: genai_artifacts/**
          if-no-files-found: warn
```

### For Local Development

```bash
# 1. Initial setup
git clone <your-repo>
cd <your-repo>
pip install -r requirements.txt

# 2. Generate tests (with LLM)
GENAI_TEST_GEN=true python tools/unified_test_runner.py

# 3. Review generated tests
python tools/hitl_validator_v2.py list
# Edit the generated .md review file
python tools/hitl_validator_v2.py approve review_123 --reviewer "Your Name"

# 4. Validate before commit
python tools/evaluation_harness_v2.py tests/generated/*.py --strict

# 5. Run final validation
python tools/policy_checker_v2.py tests/ --format json > policy_report.json
```

## Training & Few-Shot Examples

### Directory Structure
```
training_examples/
├── python/
│   ├── good/
│   │   └── calc_sum_test.py.ex1      # ✅ Best practices
│   └── bad/
│       └── flaky_sleep_test.py.ex1   # ❌ Anti-patterns
├── node/
│   ├── good/
│   │   └── userService.spec.js.ex1
│   └── bad/
│       └── brittle_dom_selectors.spec.js.ex1
└── java/
    ├── good/
    └── bad/
```

### Example Usage in Prompts
The training examples automatically inform LLM generation with:
- **Good patterns**: Deterministic, isolated, clear assertions
- **Bad patterns**: Flaky, network-dependent, unclear tests
- **Stack conventions**: pytest/jest/junit patterns

## Configuration

### Environment Variables
```bash
# Enable/disable LLM generation
GENAI_TEST_GEN=true|false

# Model selection
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_HOST=http://localhost:11434

# Validation thresholds
EVAL_PASS_THRESHOLD=0.8
POLICY_STRICT_MODE=true
```

### Custom Configuration Files
```json
{
  "stack": "python",
  "test_framework": "pytest",
  "forbidden_patterns": [
    "time.sleep(",
    "requests.get(",
    "random()"
  ],
  "required_coverage": 0.8,
  "max_test_duration": 5.0
}
```

## Artifacts Generated

All artifacts are saved to `genai_artifacts/`:

```
genai_artifacts/
├── test_report.json              # Unified test runner output
├── context.json                  # Repository context for LLM
├── genai_test_plan.json         # LLM generation plan
├── hitl_review_*.json           # Human review artifacts  
├── hitl_review_*.md             # Human-readable reviews
├── evaluation_report_*.json     # Pre-merge validation
├── collected_files_manifest.txt # Test artifacts collected
└── policy_check_*.json          # Policy validation results
```

## Quality Gates

### Automatic Rejection Criteria
- ❌ Syntax errors or compilation failures
- ❌ Uses `sleep()`, `random()` without seed, or network calls
- ❌ Missing assertions or `assert True`
- ❌ Import errors or missing dependencies
- ❌ Execution timeouts or crashes

### Human Review Required
- ⚠️ Complex business logic tests
- ⚠️ Integration or E2E scenarios  
- ⚠️ Performance-critical code paths
- ⚠️ Security-sensitive functionality

### Performance Thresholds
- ⚡ Unit tests: < 1 second execution
- ⚡ Integration tests: < 10 seconds
- ⚡ Total test suite: < 5 minutes
- ⚡ File size: < 10KB per test file

## Success Metrics

### Quality Indicators
```json
{
  "overall_score": 0.95,
  "policy_compliance": 100,
  "execution_success": 98,
  "human_approval_rate": 92,
  "test_effectiveness": 87
}
```

### Reporting Dashboard
- 📊 Daily test generation stats
- 📈 Quality trend analysis  
- 👥 Reviewer workload distribution
- 🎯 Stack-specific success rates
- ⚡ Performance benchmarks

## Troubleshooting

### Common Issues

**LLM Generation Timeouts**
```bash
# Check Ollama service
curl http://localhost:11434/api/tags

# Reduce context size
export GENAI_CONTEXT_LIMIT=5000
```

**Policy Violations**
```bash
# Review specific violations
python tools/policy_checker_v2.py tests/problematic_test.py

# Update policy config
vim policy_config.json
```

**Import Failures**
```bash
# Check Python environment
python tools/context_builder_v2.py --verbose

# Install missing dependencies
pip install -r requirements.txt
```

## Best Practices

### For Repository Maintainers
1. **Review generated tests** before approving PRs
2. **Update training examples** with project-specific patterns
3. **Configure policy rules** for your stack/framework
4. **Monitor quality metrics** over time
5. **Provide reviewer feedback** to improve future generations

### For Developers  
1. **Run local validation** before pushing
2. **Address policy violations** immediately
3. **Write descriptive commit messages** for test changes
4. **Collaborate on complex reviews** with team members
5. **Update documentation** when adding new test patterns

---

**🎯 Result**: A production-ready, stack-agnostic test generation platform with human oversight, quality guardrails, and comprehensive validation - ready for enterprise deployment!

**Next Steps**: 
1. Deploy to your CI/CD pipeline
2. Train team on review process
3. Monitor and tune quality thresholds
4. Expand training examples for your domain
5. Scale to additional repositories