#!/bin/bash

# Demo: How to use Method 1 on any repository

set -e

echo "🎯 GenAI Test Platform - Method 1 Demo"
echo "======================================"

# Create a sample repository to demonstrate on
DEMO_REPO="/tmp/sample-python-project"
echo "📁 Creating sample repository at: $DEMO_REPO"

# Clean up if exists
rm -rf "$DEMO_REPO"
mkdir -p "$DEMO_REPO"
cd "$DEMO_REPO"

# Initialize git repository
git init
git config user.name "Demo User"
git config user.email "demo@example.com"

# Create sample Python project structure
mkdir -p src tests

# Create some sample Python code
cat > src/calculator.py << 'EOF'
"""A simple calculator module"""

def add(a, b):
    """Add two numbers"""
    return a + b

def multiply(a, b):
    """Multiply two numbers"""
    return a * b

def divide(a, b):
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

class Calculator:
    """Calculator class with memory"""
    
    def __init__(self):
        self.memory = 0
    
    def add_to_memory(self, value):
        """Add value to memory"""
        self.memory += value
        return self.memory
    
    def clear_memory(self):
        """Clear memory"""
        self.memory = 0
EOF

cat > src/utils.py << 'EOF'
"""Utility functions"""

def validate_email(email):
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def format_currency(amount, currency="USD"):
    """Format amount as currency"""
    if currency == "USD":
        return f"${amount:.2f}"
    elif currency == "EUR":
        return f"€{amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
pytest>=7.0.0
coverage>=6.0
requests>=2.28.0
EOF

# Create README.md
cat > README.md << 'EOF'
# Sample Python Project

This is a demo project to show GenAI Test Platform deployment.

## Features
- Calculator functions
- Email validation
- Currency formatting

## Usage
```python
from src.calculator import add, Calculator
from src.utils import validate_email

result = add(2, 3)  # Returns 5
calc = Calculator()
calc.add_to_memory(10)

is_valid = validate_email("user@example.com")  # Returns True
```
EOF

# Initial commit
git add .
git commit -m "Initial commit: Sample Python project"

echo "✅ Sample repository created!"
echo "📁 Repository location: $DEMO_REPO"
echo ""
echo "📋 Repository contents:"
find . -type f -name "*.py" -o -name "*.txt" -o -name "*.md" | head -10

echo ""
echo "🚀 Now deploying GenAI Test Platform using Method 1..."
echo "=================================================="

# Now demonstrate the actual deployment
echo "Running: curl -sSL https://raw.githubusercontent.com/imcalledgautam/genai-test-platform/main/deploy-to-repo.sh | bash"

# Actually run the deployment script
curl -sSL https://raw.githubusercontent.com/imcalledgautam/genai-test-platform/main/deploy-to-repo.sh | bash

echo ""
echo "🎉 Deployment Complete!"
echo "======================"

echo ""
echo "📋 Files created by deployment:"
find .github .genai -type f 2>/dev/null || echo "Check GitHub Actions and config files"

echo ""
echo "📁 Full repository structure after deployment:"
tree . 2>/dev/null || find . -type f | head -15

echo ""
echo "✅ Your repository is now ready for AI-powered test generation!"
echo ""
echo "🔧 Next steps:"
echo "   1. git add ."
echo "   2. git commit -m 'Add GenAI testing infrastructure'"  
echo "   3. git push (if you have a remote)"
echo "   4. Go to GitHub Actions and run the 'GenAI Test Generation' workflow"