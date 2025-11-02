import pytest
from code.test_utils import add_numbers, calculate_percentage, format_currency, SimpleCalculator

# Tests for add_numbers function
def test_add_numbers_valid_inputs():
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0

def test_add_numbers_invalid_types():
    with pytest.raises(TypeError):
        add_numbers('a', 2)
    with pytest.raises(TypeError):
        add_numbers(2, 'b')

# Tests for calculate_percentage function
def test_calculate_percentage_valid_inputs():
    assert calculate_percentage(50, 100) == 50.0
    assert calculate_percentage(33.33, 100) == 33.33
    assert calculate_percentage(2.5, 10) == 25.0

def test_calculate_percentage_zero_total():
    with pytest.raises(ValueError):
        calculate_percentage(50, 0)

# Tests for format_currency function
def test_format_currency_valid_inputs():
    assert format_currency(1234.56) == "USD 1234.56"
    assert format_currency(99.99, "EUR") == "EUR 99.99"

def test_format_currency_invalid_types():
    with pytest.raises(TypeError):
        format_currency('a')

# Tests for SimpleCalculator class
def test_simple_calculator_init():
    calc = SimpleCalculator()
    assert calc.history == []

def test_simple_calculator_add_valid_inputs():
    calc = SimpleCalculator()
    assert calc.add(2, 3) == 5
    assert calc.history == ['2 + 3 = 5']

def test_simple_calculator_get_history():
    calc = SimpleCalculator()
    calc.add(2, 3)
    assert calc.get_history() == ['2 + 3 = 5']

def test_simple_calculator_clear_history():
    calc = SimpleCalculator()
    calc.add(2, 3)
    calc.clear_history()
    assert calc.history == []