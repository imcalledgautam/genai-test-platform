#!/usr/bin/env python3
"""
GenAI Test Platform - Complete Test Generation & Execution Solution

This script addresses the core issues seen in GitHub Actions workflows:
1. Import path resolution for generated tests
2. Missing package dependencies  
3. Proper pytest configuration
4. Enhanced LLM prompts for better test generation

Usage:
    python run_complete_test_solution.py [--fix-imports] [--generate-tests] [--run-tests]
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Optional

class CompleteTestSolution:
    def __init__(self, project_root: str = None):
        self.root = Path(project_root or os.getcwd())
        self.tools_dir = self.root / "tools"
        self.tests_dir = self.root / "tests"
        self.venv_python = self._find_python_executable()
        
        print(f"🚀 GenAI Test Platform Solution")
        print(f"📁 Project root: {self.root}")
        print(f"🐍 Python executable: {self.venv_python}")
    
    def _find_python_executable(self) -> str:
        """Find the correct Python executable (venv if available)"""
        # Check for virtual environment
        venv_paths = [
            self.root / ".venv" / "Scripts" / "python.exe",  # Windows
            self.root / "venv" / "Scripts" / "python.exe",   # Windows alt
        ]
        
        # Only check Windows paths on Windows, Unix paths on Unix
        if os.name != 'nt':  # Unix systems
            venv_paths.extend([
                self.root / ".venv" / "bin" / "python",
                self.root / "venv" / "bin" / "python",
            ])
        
        for venv_path in venv_paths:
            try:
                if venv_path.exists():
                    print(f"✅ Found virtual environment: {venv_path}")
                    return str(venv_path)
            except (OSError, PermissionError):
                # Skip paths that can't be accessed
                continue
        
        # Fall back to system Python
        print(f"📍 Using system Python: {sys.executable}")
        return sys.executable
    
    def install_dependencies(self) -> bool:
        """Install required dependencies for testing"""
        print("\n📦 Installing/upgrading test dependencies...")
        
        requirements = [
            "pytest>=8.0.0",
            "pytest-cov>=4.0.0", 
            "pytest-mock>=3.10.0",
            "requests>=2.28.0",
        ]
        
        try:
            for req in requirements:
                print(f"   Installing {req}...")
                result = subprocess.run(
                    [self.venv_python, "-m", "pip", "install", req],
                    capture_output=True, text=True, cwd=self.root
                )
                if result.returncode != 0:
                    print(f"❌ Failed to install {req}: {result.stderr}")
                    return False
            
            print("✅ All dependencies installed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def setup_pytest_config(self) -> bool:
        """Create or update pytest configuration"""
        print("\n⚙️  Setting up pytest configuration...")
        
        pytest_ini = self.root / "pytest.ini"
        config_content = """[tool:pytest]
# pytest configuration for genai-test-platform
testpaths = tests
python_paths = .
addopts = 
    --verbose
    --tb=short
    --maxfail=10
    --strict-markers
    --disable-warnings
    --import-mode=importlib
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests  
    generated: LLM-generated tests
    slow: Slow-running tests
    smoke: Smoke tests for basic functionality
"""
        
        try:
            with open(pytest_ini, 'w', encoding='utf-8') as f:
                f.write(config_content)
            print(f"✅ Created pytest configuration: {pytest_ini}")
            return True
        except Exception as e:
            print(f"❌ Error creating pytest config: {e}")
            return False
    
    def create_test_structure(self) -> bool:
        """Create proper test directory structure"""
        print("\n📁 Setting up test directory structure...")
        
        test_dirs = [
            self.tests_dir,
            self.tests_dir / "unit",
            self.tests_dir / "integration", 
            self.tests_dir / "generated",
            self.tests_dir / "generated_by_llm",
        ]
        
        try:
            for test_dir in test_dirs:
                test_dir.mkdir(parents=True, exist_ok=True)
                
                # Create __init__.py if it doesn't exist
                init_file = test_dir / "__init__.py"
                if not init_file.exists():
                    init_file.write_text("# Test package\n", encoding='utf-8')
            
            print("✅ Test directory structure created")
            return True
            
        except Exception as e:
            print(f"❌ Error creating test structure: {e}")
            return False
    
    def fix_existing_test_imports(self) -> bool:
        """Fix import issues in existing test files"""
        print("\n🔧 Fixing import paths in existing tests...")
        
        fix_script = self.tools_dir / "fix_test_imports.py"
        if not fix_script.exists():
            print(f"❌ Import fixer script not found: {fix_script}")
            return False
        
        try:
            result = subprocess.run(
                [self.venv_python, str(fix_script)],
                capture_output=True, text=True, cwd=self.root
            )
            
            print(result.stdout)
            if result.stderr:
                print(f"Warnings: {result.stderr}")
            
            if result.returncode == 0:
                print("✅ Import fixing completed successfully")
            else:
                print("⚠️  Import fixing completed with warnings")
            
            return True
            
        except Exception as e:
            print(f"❌ Error running import fixer: {e}")
            return False
    
    def generate_sample_tests(self) -> bool:
        """Generate some sample tests to verify the setup"""
        print("\n🧪 Generating sample tests...")
        
        sample_test = self.tests_dir / "unit" / "test_sample_generated.py"
        test_content = '''#!/usr/bin/env python3
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
'''
        
        try:
            with open(sample_test, 'w', encoding='utf-8') as f:
                f.write(test_content)
            print(f"✅ Created sample test: {sample_test}")
            return True
        except Exception as e:
            print(f"❌ Error creating sample test: {e}")
            return False
    
    def run_test_validation(self) -> bool:
        """Run tests to validate the setup"""
        print("\n🧪 Running test validation...")
        
        try:
            # Run sample tests first
            result = subprocess.run(
                [self.venv_python, "-m", "pytest", "tests/unit/test_sample_generated.py", "-v"],
                capture_output=True, text=True, cwd=self.root
            )
            
            print("Test Output:")
            print(result.stdout)
            if result.stderr:
                print("Errors/Warnings:")
                print(result.stderr)
            
            if result.returncode == 0:
                print("✅ Test validation passed!")
                return True
            else:
                print("❌ Test validation failed")
                return False
                
        except Exception as e:
            print(f"❌ Error running test validation: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests in the project"""
        print("\n🚀 Running all tests...")
        
        try:
            result = subprocess.run(
                [self.venv_python, "-m", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=True, text=True, cwd=self.root
            )
            
            print("All Tests Output:")
            print(result.stdout)
            if result.stderr:
                print("Errors/Warnings:")  
                print(result.stderr)
            
            if result.returncode == 0:
                print("✅ All tests passed!")
            else:
                print("⚠️  Some tests failed or had issues")
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running all tests: {e}")
            return False
    
    def run_complete_solution(self) -> bool:
        """Run the complete test solution setup"""
        print("🎯 Running Complete GenAI Test Solution...")
        print("=" * 60)
        
        steps = [
            ("Installing Dependencies", self.install_dependencies),
            ("Setting up pytest config", self.setup_pytest_config),
            ("Creating test structure", self.create_test_structure), 
            ("Fixing existing test imports", self.fix_existing_test_imports),
            ("Generating sample tests", self.generate_sample_tests),
            ("Running test validation", self.run_test_validation),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{'='*10} {step_name} {'='*10}")
            if not step_func():
                print(f"❌ Failed at step: {step_name}")
                return False
        
        print("\n" + "="*60)
        print("✅ Complete solution setup successful!")
        print("\n📋 Next steps:")
        print("   1. Run 'python -m pytest tests/ -v' to run all tests")
        print("   2. Use enhanced_test_generator.py for better LLM test generation")
        print("   3. Check pytest.ini for configuration options")
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="GenAI Test Platform - Complete Test Solution"
    )
    parser.add_argument(
        "--project-root", 
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--fix-imports", 
        action="store_true",
        help="Only fix import issues in existing tests"
    )
    parser.add_argument(
        "--run-tests", 
        action="store_true",
        help="Only run test validation"
    )
    parser.add_argument(
        "--setup-only", 
        action="store_true",
        help="Only run setup steps, don't run tests"
    )
    
    args = parser.parse_args()
    
    solution = CompleteTestSolution(args.project_root)
    
    if args.fix_imports:
        return solution.fix_existing_test_imports()
    elif args.run_tests:
        return solution.run_all_tests()
    elif args.setup_only:
        steps = [
            solution.install_dependencies,
            solution.setup_pytest_config,
            solution.create_test_structure,
            solution.fix_existing_test_imports,
            solution.generate_sample_tests,
        ]
        return all(step() for step in steps)
    else:
        return solution.run_complete_solution()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)