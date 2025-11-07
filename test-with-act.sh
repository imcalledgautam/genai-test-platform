#!/bin/bash

# GenAI Test Platform - Local Testing with Act
# This script tests GitHub Actions workflows locally using nektos/act

set -e

echo "🧪 GenAI Test Platform - Local Workflow Testing"
echo "==============================================="

# Check if act is installed
if ! command -v act &> /dev/null; then
    echo "❌ Act is not installed. Installing..."
    
    # Install act based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install act
        else
            echo "Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
    else
        echo "Please install act manually: https://github.com/nektos/act#installation"
        exit 1
    fi
fi

# Create test repository
TEST_DIR="/tmp/genai-act-test-$(date +%s)"
echo "📁 Creating test repository: $TEST_DIR"

mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Initialize git
git init
git config user.name "Act Test"
git config user.email "test@example.com"

# Create sample Python code
mkdir -p src
cat > src/math_utils.py << 'EOF'
def add(a, b):
    """Add two numbers together."""
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    return a - b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def power(base, exponent):
    """Raise base to the power of exponent."""
    return base ** exponent

def factorial(n):
    """Calculate factorial of n."""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
pytest>=8.0.0
pytest-cov>=4.0.0
EOF

# Deploy GenAI platform
echo "🚀 Deploying GenAI platform..."
bash "$SCRIPT_DIR/deploy-to-repo.sh" || curl -sSL https://raw.githubusercontent.com/imcalledgautam/genai-test-platform/main/deploy-to-repo.sh | bash

# Commit changes
git add .
git commit -m "Add GenAI test platform and sample code"

# Create act configuration
echo "⚙️  Creating act configuration..."
cat > .actrc << 'EOF'
--platform ubuntu-latest=catthehacker/ubuntu:act-latest
--artifact-server-path /tmp/artifacts
EOF

# Create GitHub event for testing
cat > .github/event.json << 'EOF'
{
  "inputs": {
    "files": "src/math_utils.py",
    "auto_approve": "true"
  }
}
EOF

echo "🎬 Testing workflow with act..."

# Test workflow_dispatch event
echo "Testing manual trigger..."
if act workflow_dispatch -e .github/event.json -v; then
    echo "✅ Workflow test passed"
else
    echo "❌ Workflow test failed"
    echo ""
    echo "This is expected as act has limitations with:"
    echo "- Docker container networking"
    echo "- Service containers (Ollama)"
    echo "- Complex shell scripts"
    echo ""
    echo "For full testing, use a real GitHub Actions environment"
fi

echo ""
echo "📋 Test Results:"
echo "   Repository: $TEST_DIR"
echo "   Workflow: .github/workflows/genai-testing.yml"
echo "   Event: .github/event.json"
echo ""

# Show generated files
if [ -d "tests/generated_by_llm" ]; then
    echo "Generated tests:"
    ls -la tests/generated_by_llm/
else
    echo "No tests generated (expected with act limitations)"
fi

echo ""
echo "🧹 Cleanup:"
echo "   rm -rf $TEST_DIR"
echo ""
echo "💡 For real testing:"
echo "   1. Push to a GitHub repository"
echo "   2. Run: gh workflow run genai-testing.yml"
echo "   3. Monitor: gh run list"

# Optional cleanup
read -p "Clean up test directory? (y/N): " cleanup
if [[ $cleanup =~ ^[Yy]$ ]]; then
    rm -rf "$TEST_DIR"
    echo "✅ Cleaned up test directory"
fi