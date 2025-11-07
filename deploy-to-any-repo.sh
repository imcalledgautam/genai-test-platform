#!/bin/bash

# GenAI Test Platform - Enhanced Repository Deployment Script
# This script adds GenAI testing capabilities to any repository with full workflow integration

set -e

REPO_URL="https://github.com/imcalledgautam/genai-test-platform"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-.}"

echo "🚀 GenAI Test Platform - Enhanced Deployment"
echo "============================================="

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "❌ Target directory '$TARGET_DIR' does not exist"
    exit 1
fi

cd "$TARGET_DIR"

# Check if it's a git repository
if [ ! -d ".git" ]; then
    echo "❌ Target directory is not a git repository"
    echo "   Please run this script from the root of a git repository"
    exit 1
fi

echo "📁 Target repository: $(pwd)"

# Create .github/workflows directory
echo "📂 Creating .github/workflows directory..."
mkdir -p .github/workflows

# Copy our workflow file directly since we have it locally
echo "📋 Installing GenAI workflow..."
cp "$SCRIPT_DIR/.github/workflows/genai-testing.yml" .github/workflows/genai-testing.yml

# Create genai config directory
echo "📂 Creating .genai/ configuration directory..."
mkdir -p .genai

# Create comprehensive configuration file
echo "⚙️  Creating configuration file..."
cat > .genai/config.yml << 'EOF'
# GenAI Test Platform Configuration

# LLM Model Configuration
model:
  name: "qwen2.5-coder:1.5b"  # Fast, efficient model for test generation
  timeout: 30  # Timeout for LLM generation in seconds
  host: "http://localhost:11434"  # Ollama host
  
# Test Generation Settings
generation:
  auto_approve: false  # Set to true to skip human review
  skip_existing: true  # Skip generating tests if they already exist
  max_files_per_run: 10  # Maximum files to process in one run
  target_coverage: 70  # Target coverage percentage for generated tests
  
# Test Execution Settings
testing:
  timeout: 900  # Test execution timeout in seconds (15 minutes)
  coverage_threshold: 0  # Minimum coverage % (0 = no minimum)
  fail_on_test_failure: false  # Whether to fail CI if generated tests fail
  parallel: true  # Run tests in parallel
  
# File Patterns (glob patterns)
include_patterns:
  python:
    - "src/**/*.py"
    - "lib/**/*.py" 
    - "app/**/*.py"
    - "**/*.py"
  javascript:
    - "src/**/*.js"
    - "lib/**/*.js"
    - "**/*.js"
  typescript:
    - "src/**/*.ts"
    - "lib/**/*.ts"
    - "**/*.ts"
  java:
    - "src/**/*.java"
    - "**/*.java"
    
exclude_patterns:
  - "**/test_*.py"
  - "**/*_test.py"
  - "**/*.test.js"
  - "**/*.test.ts"
  - "**/*.spec.js"
  - "**/*.spec.ts"
  - "**/tests/**"
  - "**/test/**"
  - "**/node_modules/**"
  - "**/venv/**"
  - "**/.venv/**"
  - "**/.git/**"
  - "**/build/**"
  - "**/dist/**"

# GitHub Actions Configuration
github_actions:
  run_on_push: true
  run_on_pr: true
  run_on_schedule: false  # Set cron expression if needed: "0 2 * * *"
  branches:
    - main
    - master
    - develop
  
# Notification Settings
notifications:
  pr_comments: true  # Comment on PRs with test results
  job_summary: true  # Generate GitHub Actions job summary
  slack_webhook: ""  # Optional Slack webhook URL
  teams_webhook: ""  # Optional Microsoft Teams webhook URL
  email: ""  # Optional email for notifications

# Quality Gates
quality_gates:
  min_test_coverage: 0  # Minimum test coverage to pass
  max_test_failures: -1  # Maximum test failures allowed (-1 = unlimited)
  require_human_approval: true  # Require human approval for generated tests

# Advanced Settings
advanced:
  context_window_size: 4000  # Context window for LLM
  max_tokens: 2000  # Maximum tokens for generated tests
  temperature: 0.3  # LLM creativity (0.0 = deterministic, 1.0 = creative)
  retry_attempts: 3  # Number of retry attempts for failed operations
EOF

# Detect project type and create stack-specific config
echo "🔍 Detecting project stack..."

STACK="unknown"
TEST_DIR="tests"
TEST_PATTERN="test_*.py"

if [ -f "package.json" ]; then
    STACK="node"
    TEST_PATTERN="*.test.js"
    echo "   Detected: Node.js project"
    
    # Add test script to package.json if not present
    if ! grep -q '"test"' package.json; then
        echo "📝 Adding test script to package.json..."
        if command -v jq > /dev/null; then
            jq '.scripts.test = "jest --coverage" | .scripts."test:watch" = "jest --watch"' package.json > package.json.tmp && mv package.json.tmp package.json
        else
            echo "   ⚠️  Please manually add test scripts to package.json:"
            echo "   \"test\": \"jest --coverage\","
            echo "   \"test:watch\": \"jest --watch\""
        fi
    fi
    
    # Create jest.config.js if not present
    if [ ! -f "jest.config.js" ] && [ ! -f "jest.config.json" ]; then
        echo "📝 Creating jest.config.js..."
        cat > jest.config.js << 'EOF'
module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/tests/**/*.test.js', '**/*.test.js'],
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
};
EOF
    fi
    
elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    STACK="python"
    echo "   Detected: Python project"
    
    # Create pytest.ini if not present and no pyproject.toml pytest config
    if [ ! -f "pytest.ini" ] && ! grep -q "\[tool.pytest" pyproject.toml 2>/dev/null; then
        echo "📝 Creating pytest.ini..."
        cat > pytest.ini << 'EOF'
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers --cov=. --cov-report=xml --cov-report=term
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    generated: marks tests as LLM-generated
EOF
    fi
    
elif [ -f "pom.xml" ]; then
    STACK="java-maven"
    TEST_PATTERN="*Test.java"
    TEST_DIR="src/test/java"
    echo "   Detected: Java (Maven) project"
    
elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
    STACK="java-gradle"
    TEST_PATTERN="*Test.java"
    TEST_DIR="src/test/java"
    echo "   Detected: Java (Gradle) project"
    
elif [ -f "go.mod" ]; then
    STACK="go"
    TEST_PATTERN="*_test.go"
    echo "   Detected: Go project"
    
elif [ -f "Cargo.toml" ]; then
    STACK="rust"
    TEST_PATTERN="*.rs"
    TEST_DIR="tests"
    echo "   Detected: Rust project"
    
else
    echo "   ⚠️  Could not detect project stack automatically"
    echo "   Please manually configure stack in .genai/config.yml"
fi

# Append stack-specific configuration
echo "⚙️  Adding stack-specific configuration..."
cat >> .genai/config.yml << EOF

# Detected Stack Configuration
detected_stack: "$STACK"

# Stack-specific settings
stack_config:
  $STACK:
    test_directory: "$TEST_DIR"
    test_file_pattern: "$TEST_PATTERN"
    dependencies: []
    build_command: ""
    test_command: ""
EOF

# Create .gitignore entries
echo "📝 Updating .gitignore..."
if [ -f ".gitignore" ]; then
    if ! grep -q "genai_artifacts" .gitignore; then
        echo "" >> .gitignore
        echo "# GenAI Test Platform artifacts" >> .gitignore
        echo "genai_artifacts/" >> .gitignore
        echo ".genai-tools/" >> .gitignore
        echo "test-results.xml" >> .gitignore
        echo "coverage.xml" >> .gitignore
    fi
else
    cat > .gitignore << 'EOF'
# GenAI Test Platform artifacts
genai_artifacts/
.genai-tools/
test-results.xml
coverage.xml
EOF
fi

# Create comprehensive README
echo "📖 Creating comprehensive documentation..."
cat > .genai/README.md << 'EOF'
# GenAI Test Platform Integration

This repository is integrated with the GenAI Test Platform for automated test generation using LLM-powered code analysis.

## 🚀 How it Works

1. **Code Analysis**: LLM analyzes your code structure, functions, and patterns
2. **Test Generation**: High-quality tests are generated based on code analysis
3. **Human Review**: Generated tests can be reviewed before execution (configurable)
4. **Test Execution**: Tests run automatically with coverage reporting
5. **Quality Gates**: Configurable quality thresholds for coverage and test results

## ⚙️ Configuration

Configuration is stored in `.genai/config.yml`. Key settings:

### Model Settings
- `model.name`: LLM model to use (default: qwen2.5-coder:1.5b)
- `model.timeout`: Generation timeout in seconds
- `model.host`: Ollama server host

### Generation Settings  
- `generation.auto_approve`: Skip human review (default: false)
- `generation.skip_existing`: Skip if tests exist (default: true)
- `generation.max_files_per_run`: Max files per generation run

### Quality Gates
- `quality_gates.min_test_coverage`: Minimum coverage percentage
- `quality_gates.max_test_failures`: Maximum allowed test failures
- `quality_gates.require_human_approval`: Require human review

## 🔧 Usage

### Automatic Execution
Tests are generated automatically on:
- Push to main/master/develop branches
- Pull requests to main branches
- Manual workflow triggers

### Manual Test Generation

```bash
# Generate tests for specific files
gh workflow run genai-testing.yml \
  -f target_files="src/utils.py,src/helpers.py"

# Generate tests for specific functions  
gh workflow run genai-testing.yml \
  -f target_functions="calculate_sum,validate_email"

# Auto-approve generated tests (skip human review)
gh workflow run genai-testing.yml \
  -f auto_approve_tests=true

# Use different model
gh workflow run genai-testing.yml \
  -f model="qwen2.5-coder:7b"
```

### Using as Reusable Action

```yaml
# .github/workflows/my-genai-tests.yml
name: My GenAI Tests

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate and Run Tests
        uses: imcalledgautam/genai-test-platform@main
        with:
          target_files: 'src/core.py,src/utils.py'
          auto_approve: false
          coverage_threshold: 80
          model: 'qwen2.5-coder:1.5b'
```

## 📁 Generated Files

Generated tests are saved to:
- `tests/generated_by_llm/` - LLM-generated test files
- `genai_artifacts/` - Test reports, metadata, and context files

## 📊 Outputs and Artifacts

Each workflow run produces:
- **Test Results**: JUnit XML format (`test-results.xml`)
- **Coverage Reports**: XML and HTML format (`coverage.xml`)
- **GenAI Metadata**: Platform logs and generation context
- **Test Files**: All generated test files
- **Job Summary**: GitHub Actions summary with key metrics

## 🎯 Quality Control

### Human-in-the-Loop
When `auto_approve: false` (default):
1. Tests are generated and saved
2. Human reviewer approves/rejects each test file  
3. Only approved tests are executed
4. Feedback improves future generations

### Quality Gates
- **Coverage Threshold**: Fail if coverage below threshold
- **Test Failure Limits**: Control how many test failures are acceptable  
- **Review Requirements**: Enforce human approval for critical code

## 🔍 Troubleshooting

### Common Issues

1. **No tests generated**
   - Check `include_patterns` in config match your file structure
   - Verify files aren't excluded by `exclude_patterns`
   - Check LLM model is pulling correctly

2. **LLM timeout errors**
   - Increase `model.timeout` in config
   - Try smaller model (e.g., qwen2.5-coder:1.5b vs 7b)
   - Check system resources and Ollama setup

3. **Test execution failures**
   - Review generated tests - some manual refinement may be needed
   - Check dependencies are properly installed
   - Verify test framework configuration (pytest.ini, jest.config.js, etc.)

4. **Coverage issues**
   - Adjust `quality_gates.min_test_coverage` 
   - Review which files are included in coverage
   - Check test quality and completeness

### Debug Mode

Enable verbose logging by setting environment variables:
```bash
export GENAI_DEBUG=true
export GENAI_VERBOSE=true
```

### Manual Execution

Run the platform locally:
```bash
# Clone the platform
git clone https://github.com/imcalledgautam/genai-test-platform
cd genai-test-platform

# Install dependencies
pip install -r requirements.txt

# Run test generation
python tools/unified_test_runner.py --files "your_file.py"
```

## 📚 Advanced Configuration

### Custom File Patterns
```yaml
include_patterns:
  python:
    - "custom/src/**/*.py"
    - "modules/**/*.py"
exclude_patterns:
  - "**/legacy/**"
  - "**/deprecated/**"
```

### Notification Setup
```yaml
notifications:
  pr_comments: true
  slack_webhook: "https://hooks.slack.com/your-webhook"
  teams_webhook: "https://your-org.webhook.office.com/..."
```

### Multi-Stack Projects
```yaml
stack_config:
  python:
    test_directory: "tests/python"
  javascript:
    test_directory: "tests/js"
```

## 🆘 Support

- **Documentation**: [GenAI Test Platform](https://github.com/imcalledgautam/genai-test-platform)
- **Issues**: [Report Issues](https://github.com/imcalledgautam/genai-test-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/imcalledgautam/genai-test-platform/discussions)

## 📄 License

This integration uses the GenAI Test Platform under its license terms.
EOF

# Create example workflows directory
echo "📄 Creating example workflows..."
mkdir -p .github/workflows/examples

# Example: Manual trigger workflow
cat > .github/workflows/examples/genai-manual-trigger.yml << 'EOF'
name: Manual GenAI Test Generation

on:
  workflow_dispatch:
    inputs:
      files:
        description: 'Files to generate tests for (comma-separated)'
        required: true
        type: string
        default: 'src/'
      functions:
        description: 'Specific functions to test (comma-separated)'
        required: false
        type: string
      auto_approve:
        description: 'Auto-approve generated tests'
        required: false
        type: boolean
        default: false
      model:
        description: 'LLM model to use'
        required: false
        type: choice
        options:
          - 'qwen2.5-coder:1.5b'
          - 'qwen2.5-coder:7b'
          - 'codellama:7b'
        default: 'qwen2.5-coder:1.5b'
      coverage_threshold:
        description: 'Minimum coverage percentage'
        required: false
        type: number
        default: 0

jobs:
  generate-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate Tests
        uses: imcalledgautam/genai-test-platform@main
        with:
          target_files: ${{ github.event.inputs.files }}
          target_functions: ${{ github.event.inputs.functions }}
          auto_approve: ${{ github.event.inputs.auto_approve }}
          model: ${{ github.event.inputs.model }}
          coverage_threshold: ${{ github.event.inputs.coverage_threshold }}
          
      - name: Upload Generated Tests
        uses: actions/upload-artifact@v4
        with:
          name: generated-tests
          path: |
            tests/generated_by_llm/
            genai_artifacts/
          retention-days: 30
EOF

# Example: Scheduled workflow  
cat > .github/workflows/examples/genai-scheduled.yml << 'EOF'
name: Scheduled GenAI Test Review

on:
  schedule:
    # Run every Sunday at 2 AM UTC
    - cron: '0 2 * * 0'
  workflow_dispatch:

jobs:
  comprehensive-test-review:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        coverage_target: [50, 70, 85]
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate Tests (Coverage Target ${{ matrix.coverage_target }}%)
        uses: imcalledgautam/genai-test-platform@main
        with:
          skip_existing: false
          coverage_threshold: ${{ matrix.coverage_target }}
          auto_approve: true
          model: 'qwen2.5-coder:7b'  # Use larger model for scheduled runs
          
      - name: Create Coverage Report
        run: |
          echo "## Coverage Report - Target: ${{ matrix.coverage_target }}%" >> $GITHUB_STEP_SUMMARY
          if [ -f "coverage.xml" ]; then
            echo "Coverage file generated successfully" >> $GITHUB_STEP_SUMMARY
          fi
EOF

# Example: PR-focused workflow
cat > .github/workflows/examples/genai-pr-focus.yml << 'EOF'
name: GenAI PR-Focused Testing

on:
  pull_request:
    branches: [ main, master ]
    paths:
      - 'src/**'
      - 'lib/**'

jobs:
  test-changed-files:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Needed for changed files detection
          
      - name: Get Changed Files
        id: changed-files
        run: |
          # Get changed files in the PR
          changed_files=$(git diff --name-only ${{ github.event.pull_request.base.sha }}..${{ github.sha }} | grep -E '\.(py|js|ts|java)$' | tr '\n' ',' | sed 's/,$//')
          echo "files=$changed_files" >> $GITHUB_OUTPUT
          echo "Changed files: $changed_files"
          
      - name: Generate Tests for Changed Files
        if: steps.changed-files.outputs.files != ''
        uses: imcalledgautam/genai-test-platform@main
        with:
          target_files: ${{ steps.changed-files.outputs.files }}
          auto_approve: false  # Always require review for PR tests
          coverage_threshold: 75
          
      - name: Comment PR
        if: steps.changed-files.outputs.files != ''
        uses: actions/github-script@v7
        with:
          script: |
            const comment = `## 🧪 GenAI Test Generation for PR
            
            Generated tests for changed files:
            \`\`\`
            ${{ steps.changed-files.outputs.files }}
            \`\`\`
            
            Please review the generated tests in \`tests/generated_by_llm/\` before approving this PR.`;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
EOF

# Create validation script
echo "🔧 Creating validation script..."
cat > .genai/validate.sh << 'EOF'
#!/bin/bash

# GenAI Test Platform - Configuration Validation Script

echo "🔍 GenAI Test Platform - Configuration Validation"
echo "================================================"

CONFIG_FILE=".genai/config.yml"
WORKFLOW_FILE=".github/workflows/genai-testing.yml"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Check if workflow file exists
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ Workflow file not found: $WORKFLOW_FILE"
    exit 1
fi

echo "✅ Configuration files found"

# Validate YAML syntax (if yq is available)
if command -v yq > /dev/null; then
    echo "🔍 Validating YAML syntax..."
    if yq eval . "$CONFIG_FILE" > /dev/null; then
        echo "✅ Configuration YAML is valid"
    else
        echo "❌ Configuration YAML is invalid"
        exit 1
    fi
fi

# Check for required configuration sections
echo "🔍 Checking configuration sections..."
required_sections=("model" "generation" "testing" "include_patterns")
for section in "${required_sections[@]}"; do
    if grep -q "^$section:" "$CONFIG_FILE"; then
        echo "✅ Found section: $section"
    else
        echo "⚠️  Missing section: $section"
    fi
done

# Validate model configuration
if grep -q "name.*qwen" "$CONFIG_FILE"; then
    echo "✅ Model configuration looks good"
else
    echo "⚠️  Model configuration may need review"
fi

# Check file patterns
if grep -q "include_patterns" "$CONFIG_FILE" && grep -q "exclude_patterns" "$CONFIG_FILE"; then
    echo "✅ File pattern configuration found"
else
    echo "⚠️  File pattern configuration may be incomplete"
fi

echo ""
echo "🎉 Validation complete!"
echo ""
echo "💡 Tips:"
echo "   • Test the workflow: gh workflow run genai-testing.yml"
echo "   • Monitor runs: gh run list --workflow=genai-testing.yml"
echo "   • View logs: gh run view <run-id>"
EOF

chmod +x .genai/validate.sh

echo ""
echo "✅ GenAI Test Platform successfully deployed!"
echo ""
echo "📋 What was added:"
echo "   • .github/workflows/genai-testing.yml - Main workflow"  
echo "   • .genai/config.yml - Comprehensive configuration"
echo "   • .genai/README.md - Complete documentation"
echo "   • .genai/validate.sh - Configuration validator"
echo "   • Example workflows in .github/workflows/examples/"
echo "   • Updated .gitignore with GenAI artifacts"
echo ""
echo "🔧 Next steps:"
echo "   1. Review and customize .genai/config.yml for your project"
echo "   2. Run validation: .genai/validate.sh"
echo "   3. Commit and push the changes:"
echo "      git add .genai .github/workflows .gitignore"
echo "      git commit -m 'Add GenAI Test Platform integration'"
echo "      git push"
echo "   4. The workflow will run automatically on next push/PR"
echo ""
echo "📖 Manual execution:"
echo "   gh workflow run genai-testing.yml"
echo "   gh workflow run genai-testing.yml -f auto_approve_tests=true"
echo ""
echo "📊 Monitor progress:"
echo "   gh run list --workflow=genai-testing.yml"
echo "   gh run view --log"
echo ""
echo "🎉 Happy testing with GenAI!"
echo "   Stack detected: $STACK"
echo "   Test directory: $TEST_DIR"
echo "   Test pattern: $TEST_PATTERN"