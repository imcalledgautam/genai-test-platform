import sys
import pathlib

# Add tools directory to path for imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "tools"))

def test_stack_detection():
    """Test stack detection works"""
    from tools.unified_test_runner import detect_stack
    
    # Test basic stack detection (should detect python for our project)
    stack = detect_stack()
    assert stack in ["python", "node", "java"], f"Expected valid stack type, got: {stack}"
    
    print("✅ Stack detection tests passed")

def test_imports():
    """Test that all imports work"""
    from tools.unified_test_runner import (
        detect_stack,
        ensure_deps, 
        run_native_tests,
        collect_reports
    )
    print("✅ Import tests passed")

if __name__ == "__main__":
    test_imports()
    test_stack_detection()
    print("✅ All tests passed!")