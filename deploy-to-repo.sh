#!/bin/bash

# GenAI Test Platform - Repository Deployment Script
# Version: 2.0
# This script deploys GenAI testing capabilities to any repository

set -e

REPO_URL="https://github.com/imcalledgautam/genai-test-platform"
TARGET_DIR="${1:-.}"

echo "🚀 GenAI Test Platform - Repository Deployment v2.0"
echo "===================================================="

# Validate target directory
if [ ! -d "$TARGET_DIR" ]; then
    echo "❌ Directory '$TARGET_DIR' does not exist"
    exit 1
fi

cd "$TARGET_DIR"

if [ ! -d ".git" ]; then
    echo "❌ Not a git repository. Please run from a git repository root."
    exit 1
fi

echo "📁 Target: $(pwd)"

# Create directories
echo "📂 Creating directories..."
mkdir -p .github/workflows .genai

# Create the main workflow file
echo "📝 Creating GitHub Actions workflow..."
cat > .github/workflows/genai-testing.yml << 'EOF'
name: 🌐 GenAI Test Platform - Universal Test Generation

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master, develop ]
  workflow_dispatch:
    inputs:
      files:
        description: "Files to test (comma-separated)"
        required: false
        type: string
      auto_approve:
        description: "Auto-approve LLM-generated tests"
        required: false
        type: boolean
        default: false

jobs:
  genai-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 45

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install Ollama + Dependencies
        run: |
          echo "🔧 Installing base dependencies..."
          sudo apt-get update -y
          sudo apt-get install -y curl jq git

          echo "🤖 Installing Ollama..."
          curl -fsSL https://ollama.com/install.sh | sh
          ollama serve &
          sleep 15

          echo "📦 Pulling model..."
          ollama pull qwen2.5-coder:1.5b

          echo "✅ Ollama installed successfully"

      - name: Clone GenAI Test Backend
        run: |
          echo "📥 Cloning GenAI backend tools..."
          git clone https://github.com/imcalledgautam/genai-test-platform.git /tmp/genai-platform
          cp -r /tmp/genai-platform/tools .
          cp -r /tmp/genai-platform/llm_agent .
          pip install pytest coverage requests pathlib2 || true
          echo "✅ GenAI tools ready"

      - name: Detect Project Language
        id: lang
        run: |
          echo "🔍 Detecting primary language..."
          if ls *.py >/dev/null 2>&1; then
            echo "language=python" >> $GITHUB_OUTPUT
          elif ls package.json >/dev/null 2>&1; then
            echo "language=javascript" >> $GITHUB_OUTPUT
          elif ls *.java >/dev/null 2>&1; then
            echo "language=java" >> $GITHUB_OUTPUT
          else
            echo "language=generic" >> $GITHUB_OUTPUT
          fi

      - name: Generate AI Test Cases
        run: |
          echo "🧠 Generating tests using LLM..."
          mkdir -p tests/generated
          export PYTHONPATH=".:$PYTHONPATH"
          python tools/unified_test_runner.py --auto-approve || echo "⚠️ Generation completed"

      - name: Run Tests and Collect Coverage
        if: always()
        run: |
          mkdir -p genai_artifacts reports
          pip install pytest pytest-cov coverage
          echo "🔍 Checking for generated tests..."
          find tests/ -name "*.py" -type f | head -5 || echo "No test files found"
          pytest tests/ --disable-warnings -v --tb=short \
            --cov=. --cov-report=xml:reports/coverage.xml --cov-report=term-missing \
            2>&1 | tee reports/test-results.log || echo "⚠️ Tests completed"

      - name: Upload Test Artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: genai-test-results
          path: |
            tests/
            genai_artifacts/
            reports/
            *.xml
            *.json
          retention-days: 30
EOF

# Create simple configuration
echo "📝 Creating configuration..."
cat > .genai/config.yml << 'EOF'
# GenAI Test Platform Configuration

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
  - "**/.git/**"
EOF

# Create README
echo "📖 Creating documentation..."
cat > .genai/README.md << 'EOF'
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
EOF

# Update .gitignore
echo "📝 Updating .gitignore..."
if [ -f ".gitignore" ]; then
    if ! grep -q "genai_artifacts" .gitignore; then
        echo -e "\n# GenAI artifacts\ngenai_artifacts/\ngenai-tools/" >> .gitignore
    fi
else
    echo -e "genai_artifacts/\ngenai-tools/" > .gitignore
fi

echo ""
echo "✅ GenAI Test Platform deployed successfully!"
echo ""
echo "📋 Added:"
echo "   • .github/workflows/genai-testing.yml"
echo "   • .genai/config.yml"
echo "   • .genai/README.md"
echo ""
echo "🔧 Next steps:"
echo "   1. Commit changes: git add . && git commit -m 'Add GenAI testing'"
echo "   2. Push: git push"
echo "   3. Run: gh workflow run genai-testing.yml"
echo ""
echo "🎉 Ready to generate AI-powered tests!"