# filename: tests/generated/test_test_utils.py
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from code.test_utils import add_numbers, calculate_percentage, format_currency, SimpleCalculator

def test_add_numbers_positive():
    assert add_numbers(10, 5) == 15
    assert add_numbers(-3, 7) == 4

def test_add_numbers_negative():
    with pytest.raises(TypeError):
        add_numbers("a", 5)
    with pytest.raises(TypeError):
        add_numbers(10, "b")

def test_calculate_percentage_positive():
    assert calculate_percentage(250, 1000) == 25.0
    assert calculate_percentage(100, 100) == 100.0

def test_calculate_percentage_negative():
    with pytest.raises(ValueError):
        calculate_percentage(50, 0)
    with pytest.raises(ValueError):
        calculate_percentage(0, 50)

def test_format_currency_positive():
    assert format_currency(250) == "USD 250.00"
    assert format_currency(100, "EUR") == "EUR 100.00"

def test_format_currency_negative():
    with pytest.raises(TypeError):
        format_currency("a")
    with pytest.raises(TypeError):
        format_currency(100, 1)

def test_simple_calculator_add_positive():
    calc = SimpleCalculator()
    assert calc.add(10, 5) == 15
    assert calc.history == ["10 + 5 = 15"]

def test_simple_calculator_add_negative():
    calc = SimpleCalculator()
    with pytest.raises(TypeError):
        calc.add("a", 5)
    with pytest.raises(TypeError):
        calc.add(10, "b")

def test_simple_calculator_get_history_positive():
    calc = SimpleCalculator()
    calc.add(10, 5)
    assert calc.get_history() == ["10 + 5 = 15"]

def test_simple_calculator_clear_history_positive():
    calc = SimpleCalculator()
    calc.add(10, 5)
    calc.clear_history()
    assert calc.get_history() == []