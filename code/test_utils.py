"""
Simple test utility for the GenAI Test Platform.
This file demonstrates test generation capabilities.
"""

def add_numbers(a, b):
    """Add two numbers together."""
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numbers")
    return a + b

def calculate_percentage(value, total):
    """Calculate percentage of value from total."""
    if total == 0:
        raise ValueError("Total cannot be zero")
    return (value / total) * 100

def format_currency(amount, currency="USD"):
    """Format amount as currency string."""
    if not isinstance(amount, (int, float)):
        raise TypeError("Amount must be a number")
    return f"{currency} {amount:.2f}"

class SimpleCalculator:
    """A simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers and store in history."""
        result = add_numbers(a, b)
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def get_history(self):
        """Get calculation history."""
        return self.history.copy()
    
    def clear_history(self):
        """Clear calculation history."""
        self.history.clear()