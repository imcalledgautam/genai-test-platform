#!/bin/bash

# GenAI Test Platform - Deployment Validator
# Version: 2.0
# This script tests the GenAI deployment in a repository

set -e

TEST_DIR="${1:-/tmp/genai-test-$(date +%s)}"

echo "🧪 GenAI Test Platform - Deployment Validator"
echo "============================================="

# Create test repository
echo "📁 Creating test repository..."
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Initialize git repo
git init
git config user.name "GenAI Test"
git config user.email "test@genai.platform"

# Create sample Python code
echo "📝 Creating sample code..."
mkdir -p src
cat > src/calculator.py << 'EOF'
def add(a, b):
    """Add two numbers."""
    return a + b

def multiply(a, b):  
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

class Calculator:
    def __init__(self):
        self.history = []
    
    def calculate(self, operation, a, b):
        if operation == "add":
            result = add(a, b)
        elif operation == "multiply":
            result = multiply(a, b)
        elif operation == "divide":
            result = divide(a, b)
        else:
            raise ValueError("Unknown operation")
        
        self.history.append(f"{operation}({a}, {b}) = {result}")
        return result
EOF

cat > src/utils.py << 'EOF'
import re

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def format_name(first, last):
    """Format a person's name."""
    return f"{first.strip().title()} {last.strip().title()}"

def calculate_age(birth_year, current_year=2025):
    """Calculate age from birth year."""
    if birth_year > current_year:
        raise ValueError("Birth year cannot be in the future")
    return current_year - birth_year
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
pytest>=8.0.0
pytest-cov>=4.0.0
requests>=2.31.0
EOF

# Create setup.py
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="genai-test-sample",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.8",
)
EOF

# Initial commit
git add .
git commit -m "Initial commit with sample code"

echo "✅ Test repository created: $TEST_DIR"

# Run deployment script
echo "🚀 Running GenAI deployment..."
if [ -f "/workspaces/genai-test-platform/deploy-to-repo.sh" ]; then
    bash /workspaces/genai-test-platform/deploy-to-repo.sh
else
    curl -sSL https://raw.githubusercontent.com/imcalledgautam/genai-test-platform/main/deploy-to-repo.sh | bash
fi

# Validate deployment
echo "🔍 Validating deployment..."

ERRORS=0

# Check workflow file
if [ -f ".github/workflows/genai-testing.yml" ]; then
    echo "✅ Workflow file created"
else
    echo "❌ Workflow file missing"
    ERRORS=$((ERRORS + 1))
fi

# Check config file  
if [ -f ".genai/config.yml" ]; then
    echo "✅ Configuration file created"
else
    echo "❌ Configuration file missing"
    ERRORS=$((ERRORS + 1))
fi

# Check README
if [ -f ".genai/README.md" ]; then
    echo "✅ Documentation created"
else
    echo "❌ Documentation missing"  
    ERRORS=$((ERRORS + 1))
fi

# Check .gitignore
if grep -q "genai_artifacts" .gitignore; then
    echo "✅ .gitignore updated"
else
    echo "❌ .gitignore not updated"
    ERRORS=$((ERRORS + 1))
fi

# Validate YAML syntax (if yq available)
if command -v yq > /dev/null; then
    if yq eval . .genai/config.yml > /dev/null 2>&1; then
        echo "✅ Configuration YAML is valid"
    else
        echo "❌ Configuration YAML is invalid"
        ERRORS=$((ERRORS + 1))
    fi
fi

# Test workflow syntax (if actionlint available)
if command -v actionlint > /dev/null; then
    if actionlint .github/workflows/genai-testing.yml; then
        echo "✅ Workflow YAML is valid"
    else
        echo "❌ Workflow YAML has issues"
        ERRORS=$((ERRORS + 1))
    fi
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "🎉 Deployment validation PASSED!"
    echo "   All files created successfully"
    echo "   Repository ready for GenAI testing"
else
    echo "❌ Deployment validation FAILED!"
    echo "   $ERRORS error(s) found"
    exit 1
fi

echo ""
echo "📁 Test repository: $TEST_DIR"
echo "📋 Files created:"
find .genai .github -type f 2>/dev/null | sort

echo ""
echo "🔧 To test manually:"
echo "   cd $TEST_DIR"
echo "   # Set up Ollama and run the workflow locally"

echo ""
echo "🗑️  To clean up:"
echo "   rm -rf $TEST_DIR"