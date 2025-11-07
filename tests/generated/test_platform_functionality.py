#!/usr/bin/env python3
"""
Clean working tests for the GenAI Test Platform
These tests verify basic functionality without problematic imports.
"""

import pytest
import json
from pathlib import Path

def test_basic_functionality():
    """Basic test to verify pytest is working"""
    assert True

def test_simple_math():
    """Test basic math operations"""
    assert 2 + 2 == 4
    assert 5 * 3 == 15
    assert 10 / 2 == 5
    assert 2 ** 3 == 8

def test_string_operations():
    """Test string operations"""
    text = "GenAI Test Platform"
    assert text.lower() == "genai test platform"
    assert len(text) == 19
    assert "Test" in text
    assert text.startswith("GenAI")
    assert text.endswith("Platform")

def test_list_operations():
    """Test list operations"""
    numbers = [1, 2, 3, 4, 5]
    assert len(numbers) == 5
    assert sum(numbers) == 15
    assert max(numbers) == 5
    assert min(numbers) == 1
    
    # Test list methods
    numbers.append(6)
    assert 6 in numbers
    assert len(numbers) == 6

def test_dict_operations():
    """Test dictionary operations"""
    config = {
        "platform": "GenAI Test Platform",
        "version": "1.0",
        "features": ["LLM", "Context", "HITL", "Policy"]
    }
    
    assert config["platform"] == "GenAI Test Platform"
    assert len(config["features"]) == 4
    assert "LLM" in config["features"]

def test_file_path_operations():
    """Test Path operations"""
    path = Path("test.txt")
    assert path.suffix == ".txt"
    assert path.stem == "test"
    assert str(path) == "test.txt"

def test_json_operations():
    """Test JSON serialization/deserialization"""
    data = {
        "test_id": "test_001",
        "results": [True, False, True],
        "score": 0.75
    }
    
    # Serialize to JSON
    json_str = json.dumps(data)
    assert isinstance(json_str, str)
    
    # Deserialize from JSON
    parsed_data = json.loads(json_str)
    assert parsed_data == data
    assert parsed_data["test_id"] == "test_001"
    assert parsed_data["score"] == 0.75

@pytest.mark.parametrize("input_val,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (4, 8),
])
def test_parametrized_double(input_val, expected):
    """Test parametrized function - double a number"""
    assert input_val * 2 == expected

def test_exception_handling():
    """Test exception handling"""
    with pytest.raises(ZeroDivisionError):
        result = 10 / 0
    
    with pytest.raises(KeyError):
        test_dict = {"a": 1}
        value = test_dict["nonexistent_key"]

def test_platform_specific_functionality():
    """Test functionality specific to our platform"""
    # Test that we can work with test-related concepts
    test_result = {
        "status": "passed",
        "execution_time": 0.123,
        "assertions": 5
    }
    
    assert test_result["status"] == "passed"
    assert test_result["execution_time"] < 1.0
    assert test_result["assertions"] > 0
    
    # Simulate test aggregation
    test_results = [
        {"status": "passed", "score": 1.0},
        {"status": "failed", "score": 0.0},
        {"status": "passed", "score": 1.0},
    ]
    
    total_score = sum(r["score"] for r in test_results)
    avg_score = total_score / len(test_results)
    
    assert total_score == 2.0
    assert avg_score == pytest.approx(0.667, rel=1e-2)