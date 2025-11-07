# GenAI Test Platform - GitHub Actions Integration

Deploy AI-powered test generation to any repository with GitHub Actions workflows.

## 🚀 Quick Setup

### Option 1: Single Repository Deployment

```bash
# Deploy to current repository
curl -sSL https://raw.githubusercontent.com/imcalledgautam/genai-test-platform/main/deploy-to-repo.sh | bash

# Or download and run
wget https://raw.githubusercontent.com/imcalledgautam/genai-test-platform/main/deploy-to-repo.sh
chmod +x deploy-to-repo.sh
./deploy-to-repo.sh
```

### Option 2: Organization-wide Deployment

```bash
# Deploy to all repositories in an organization
export GITHUB_TOKEN="your_token"
curl -sSL https://raw.githubusercontent.com/imcalledgautam/genai-test-platform/main/deploy-organization-wide.sh | bash -s your-org

# Deploy to specific repositories
./deploy-organization-wide.sh your-org "repo1,repo2,repo3"
```

### Option 3: Use as GitHub Action

Add to `.github/workflows/genai-tests.yml`:

```yaml
name: GenAI Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: imcalledgautam/genai-test-platform@main
        with:
          files: 'src/'
          auto_approve: false
```

## 📋 What Gets Deployed

Each deployment adds:

### 1. GitHub Actions Workflow (`.github/workflows/genai-testing.yml`)
- Automatic test generation on push/PR
- LLM-powered code analysis
- Test execution with coverage reporting
- Artifact collection and reporting

### 2. Configuration (`.genai/config.yml`)
```yaml
model: "qwen2.5-coder:1.5b"
auto_approve: false
timeout: 900
coverage_threshold: 0

include_patterns:
  - "**/*.py"
  - "**/*.js" 
  - "**/*.ts"
  - "**/*.java"

exclude_patterns:
  - "**/test_*"
  - "**/tests/**"
  - "**/node_modules/**"
```

### 3. Documentation (`.genai/README.md`)
- Usage instructions
- Configuration options
- Troubleshooting guide

### 4. Git Configuration
- Updated `.gitignore` for GenAI artifacts
- Proper artifact exclusions

## 🎯 Usage Examples

### Manual Triggers

```bash
# Basic run
gh workflow run genai-testing.yml

# Test specific files
gh workflow run genai-testing.yml -f files="src/utils.py,src/helpers.py"

# Auto-approve tests (skip human review)
gh workflow run genai-testing.yml -f auto_approve=true

# Custom model
gh workflow run genai-testing.yml -f model="qwen2.5-coder:7b"
```

### Workflow Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `files` | Files to generate tests for | `""` (all) |
| `auto_approve` | Skip human review | `false` |
| `model` | LLM model to use | `qwen2.5-coder:1.5b` |

## 🔧 Configuration Options

### Model Selection
```yaml
# Fast, efficient (default)
model: "qwen2.5-coder:1.5b"  

# Larger, more capable
model: "qwen2.5-coder:7b"

# Alternative models
model: "codellama:7b"
```

### Quality Gates
```yaml
coverage_threshold: 70  # Minimum coverage %
auto_approve: false     # Require human review
timeout: 900           # Test timeout (seconds)
```

### File Patterns
```yaml
include_patterns:
  - "src/**/*.py"      # Python in src/
  - "lib/**/*.js"      # JavaScript in lib/
  - "**/*.ts"          # All TypeScript

exclude_patterns:
  - "**/test_*"        # Test files
  - "**/node_modules/**"  # Dependencies
  - "**/.git/**"       # Git files
```

## 📊 Workflow Outputs

Each run produces:

### Artifacts
- `test-results/` - JUnit XML test results
- `coverage.xml` - Coverage reports
- `genai_artifacts/` - Platform metadata
- `tests/generated_by_llm/` - Generated test files

### Job Summary
- Tests generated count
- Test pass/fail status
- Coverage percentage
- Links to generated files

### PR Comments (if enabled)
- Automated test generation summary
- Link to generated test files
- Coverage and quality metrics

## 🔍 Monitoring & Debugging

### Check Workflow Status
```bash
# List recent runs
gh run list --workflow=genai-testing.yml

# View specific run
gh run view <run-id>

# Download artifacts
gh run download <run-id>
```

### Debug Failed Runs
```bash
# View logs
gh run view <run-id> --log

# Check specific job
gh run view <run-id> --job=genai-tests
```

### Common Issues

1. **Ollama Model Pull Fails**
   - Check internet connectivity
   - Try smaller model: `qwen2.5-coder:1.5b`

2. **No Tests Generated**
   - Verify file patterns in config
   - Check if files are excluded
   - Review LLM timeout settings

3. **Test Execution Fails**
   - Check project dependencies
   - Review generated test quality
   - Increase timeout if needed

## 🎛️ Advanced Configuration

### Custom Workflow Schedule
```yaml
# Add to .github/workflows/genai-testing.yml
on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday 2 AM
```

### Multi-Environment Testing
```yaml
strategy:
  matrix:
    python-version: [3.8, 3.9, 3.11]
    model: ['qwen2.5-coder:1.5b', 'qwen2.5-coder:7b']
```

### Notification Integration
```yaml
# Add to workflow
- name: Notify Slack
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## 🔒 Security Considerations

### Repository Secrets
- `GITHUB_TOKEN` - For organization deployment
- `SLACK_WEBHOOK` - For notifications (optional)

### Permissions
The workflow requires:
- `contents: read` - Read repository code
- `pull-requests: write` - Comment on PRs
- `actions: read` - Access workflow artifacts

### Model Security
- Models run locally in GitHub Actions runners
- No code sent to external services
- All processing happens within your infrastructure

## 🆘 Troubleshooting

### Deployment Issues

**Problem**: "Not a git repository"
```bash
# Ensure you're in a git repository
git init
git remote add origin <your-repo-url>
```

**Problem**: "Permission denied"
```bash
# Make scripts executable
chmod +x deploy-to-repo.sh
```

### Workflow Issues

**Problem**: Workflow doesn't trigger
- Check branch names in workflow file
- Verify push/PR targets correct branches
- Check workflow permissions

**Problem**: Model download fails  
- Check GitHub Actions runner has internet access
- Try smaller model in config
- Increase timeout if on slower runners

**Problem**: Tests fail to execute
- Check project dependencies are installed
- Verify test framework configuration
- Review generated test files for issues

### Getting Help

1. **Check Logs**: Use `gh run view --log` for detailed error messages
2. **Test Locally**: Run `./test-deployment.sh` to validate setup
3. **File Issues**: [Report bugs](https://github.com/imcalledgautam/genai-test-platform/issues)
4. **Discussions**: [Community help](https://github.com/imcalledgautam/genai-test-platform/discussions)

## 📚 Resources

- [Main Repository](https://github.com/imcalledgautam/genai-test-platform)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Ollama Models](https://ollama.com/library)
- [pytest Documentation](https://docs.pytest.org/)

---

**Ready to generate AI-powered tests for your repositories? Start with a single repository deployment and expand from there!**