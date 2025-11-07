#!/usr/bin/env python3
"""
Sample generated test file to verify test execution setup
"""
import sys
import os
import pytest

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestSampleFunctionality:
    """Sample test class to verify pytest setup"""
    
    def test_basic_assertion(self):
        """Test basic assertions work"""
        assert True
        assert 1 + 1 == 2
        assert "hello".upper() == "HELLO"
    
    def test_list_operations(self):
        """Test list operations"""
        test_list = [1, 2, 3, 4, 5]
        assert len(test_list) == 5
        assert test_list[0] == 1
        assert test_list[-1] == 5
    
    def test_exception_handling(self):
        """Test exception handling with pytest.raises"""
        with pytest.raises(ZeroDivisionError):
            result = 1 / 0
        
        with pytest.raises(KeyError):
            test_dict = {"a": 1}
            value = test_dict["nonexistent_key"]
    
    @pytest.mark.parametrize("input_val,expected", [
        (0, 0),
        (1, 1), 
        (2, 4),
        (3, 9),
        (4, 16),
    ])
    def test_square_function(self, input_val, expected):
        """Test parametrized square function"""
        def square(x):
            return x * x
        
        assert square(input_val) == expected

@pytest.mark.generated
class TestImportResolution:
    """Test that imports work correctly"""
    
    def test_standard_library_imports(self):
        """Test standard library imports"""
        import json
        import os
        import sys
        
        assert hasattr(json, 'dumps')
        assert hasattr(os, 'path')
        assert hasattr(sys, 'path')
    
    def test_pytest_functionality(self):
        """Test pytest-specific functionality"""
        import pytest
        
        assert hasattr(pytest, 'raises')
        assert hasattr(pytest, 'mark')
        assert hasattr(pytest, 'param')
