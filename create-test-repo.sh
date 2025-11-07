#!/bin/bash

# Quick Test Repository Creator
# This creates a new test repository and deploys GenAI to it

echo "🧪 Creating Test Repository for GenAI Platform"
echo "=============================================="

REPO_NAME="genai-test-$(date +%s)"
echo "📁 Repository name: $REPO_NAME"

# Create temporary directory
TEST_DIR="/tmp/$REPO_NAME"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Initialize repository
git init
git config user.name "GenAI Tester"
git config user.email "genai@test.com"

# Create sample Python code
echo "📝 Creating sample code..."
mkdir -p src

cat > src/calculator.py << 'EOF'
"""Simple calculator module for testing GenAI."""

def add(a, b):
    """Add two numbers."""
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

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def calculate(self, operation, a, b):
        """Perform calculation and store in history."""
        operations = {
            'add': add,
            'subtract': subtract,
            'multiply': multiply,
            'divide': divide
        }
        
        if operation not in operations:
            raise ValueError(f"Unknown operation: {operation}")
        
        result = operations[operation](a, b)
        self.history.append(f"{operation}({a}, {b}) = {result}")
        return result
    
    def get_history(self):
        """Get calculation history."""
        return self.history.copy()
    
    def clear_history(self):
        """Clear calculation history."""
        self.history.clear()
EOF

cat > src/string_utils.py << 'EOF'
"""String utility functions for testing."""

import re

def reverse_string(s):
    """Reverse a string."""
    return s[::-1]

def count_words(text):
    """Count words in text."""
    return len(text.split())

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def capitalize_words(text):
    """Capitalize each word in text."""
    return ' '.join(word.capitalize() for word in text.split())

def extract_numbers(text):
    """Extract all numbers from text."""
    return [int(match) for match in re.findall(r'\d+', text)]

def is_palindrome(text):
    """Check if text is a palindrome."""
    clean_text = re.sub(r'[^a-zA-Z0-9]', '', text.lower())
    return clean_text == clean_text[::-1]
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
pytest>=8.0.0
pytest-cov>=4.0.0
EOF

# Create README
cat > README.md << 'EOF'
# GenAI Test Repository

This is a test repository for the GenAI Test Platform.

## Code Structure
- `src/calculator.py` - Calculator functions and class
- `src/string_utils.py` - String utility functions

## Testing
This repository will use AI-generated tests via GitHub Actions.
EOF

# Initial commit
git add .
git commit -m "Initial commit: Sample code for GenAI testing"

echo ""
echo "✅ Test repository created: $TEST_DIR"
echo ""
echo "📋 Created files:"
ls -la src/
echo ""
echo "🚀 To test GenAI deployment:"
echo "   1. cd $TEST_DIR"
echo "   2. Create GitHub repository: gh repo create $REPO_NAME --public"
echo "   3. Push: git remote add origin https://github.com/YOUR_USERNAME/$REPO_NAME.git"
echo "   4. git push -u origin main"
echo "   5. Deploy GenAI: curl -sSL https://raw.githubusercontent.com/imcalledgautam/genai-test-platform/main/deploy-to-repo.sh | bash"
echo "   6. Commit and push GenAI files"
echo "   7. Watch GitHub Actions!"
echo ""
echo "🌐 Or test locally:"
echo "   cd $TEST_DIR"
echo "   /workspaces/genai-test-platform/deploy-to-repo.sh"
echo "   # Check generated files"