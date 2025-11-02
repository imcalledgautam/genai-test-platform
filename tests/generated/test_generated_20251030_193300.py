# filename: tests/generated/test_test_utils.py
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import the modules being tested
from code.test_utils import add_numbers, calculate_percentage, format_currency, SimpleCalculator

def test_add_numbers_valid_inputs():
    """Test with typical valid inputs."""
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0
    assert add_numbers(5.5, 4.5) == 10

def test_add_numbers_invalid_types():
    """Test conditions that raise TypeError."""
    with pytest.raises(TypeError):
        add_numbers(2, "3")

def test_calculate_percentage_valid_inputs():
    """Test with typical valid inputs."""
    assert calculate_percentage(20, 100) == 20.0
    assert calculate_percentage(50, 100) == 50.0
    assert calculate_percentage(1, 100) == 1.0

def test_calculate_percentage_zero_total():
    """Test conditions that raise ValueError."""
    with pytest.raises(ValueError):
        calculate_percentage(20, 0)

def test_format_currency_valid_inputs():
    """Test with typical valid inputs."""
    assert format_currency(1234.56) == "USD 1234.56"
    assert format_currency(789.0) == "USD 789.00"
    assert format_currency(0) == "USD 0.00"

def test_format_currency_invalid_types():
    """Test conditions that raise TypeError."""
    with pytest.raises(TypeError):
        format_currency("1234.56")

def test_SimpleCalculator_init():
    """Test with typical valid inputs."""
    calc = SimpleCalculator()
    assert calc.history == []

def test_SimpleCalculator_add_valid_inputs():
    """Test with typical valid inputs."""
    calc = SimpleCalculator()
    result = calc.add(2, 3)
    assert result == 5
    assert calc.history == ["2 + 3 = 5"]

def test_SimpleCalculator_get_history():
    """Test with typical valid inputs."""
    calc = SimpleCalculator()
    calc.add(2, 3)
    history = calc.get_history()
    assert history == ["2 + 3 = 5"]
    assert calc.history == ["2 + 3 = 5"]

def test_SimpleCalculator_clear_history():
    """Test with typical valid inputs."""
    calc = SimpleCalculator()
    calc.add(2, 3)
    calc.clear_history()
    assert calc.history == []