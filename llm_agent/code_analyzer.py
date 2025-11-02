"""
Code analysis helper for better LLM test generation.
This module analyzes Python code to extract testable behaviors and edge cases.
"""

import ast
import inspect
from typing import Dict, List, Any
from pathlib import Path

def analyze_function_for_testing(func_source: str, func_name: str) -> Dict[str, Any]:
    """
    Analyze a function's source code to identify testable behaviors.
    Returns structured information about what should be tested.
    """
    analysis = {
        "function_name": func_name,
        "parameters": [],
        "return_type": None,
        "raises_exceptions": [],
        "validation_checks": [],
        "edge_cases": [],
        "test_recommendations": []
    }
    
    try:
        # Parse the function
        tree = ast.parse(func_source)
        
        # Find the function definition
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                # Extract parameters
                for arg in node.args.args:
                    analysis["parameters"].append(arg.arg)
                
                # Analyze function body for testing patterns
                for stmt in ast.walk(node):
                    # Look for isinstance checks
                    if isinstance(stmt, ast.Call) and isinstance(stmt.func, ast.Name):
                        if stmt.func.id == "isinstance":
                            analysis["validation_checks"].append("isinstance check found")
                    
                    # Look for raise statements
                    if isinstance(stmt, ast.Raise):
                        if isinstance(stmt.exc, ast.Call) and isinstance(stmt.exc.func, ast.Name):
                            exc_type = stmt.exc.func.id
                            analysis["raises_exceptions"].append(exc_type)
                    
                    # Look for value comparisons (edge cases)
                    if isinstance(stmt, ast.Compare):
                        for comparator in stmt.comparators:
                            if isinstance(comparator, ast.Constant):
                                if comparator.value == 0:
                                    analysis["edge_cases"].append("zero_check")
                                elif comparator.value == "":
                                    analysis["edge_cases"].append("empty_string_check")
    
    except SyntaxError:
        analysis["error"] = "Could not parse function"
    
    # Generate test recommendations based on analysis
    _generate_test_recommendations(analysis)
    
    return analysis

def _generate_test_recommendations(analysis: Dict[str, Any]) -> None:
    """Generate specific test recommendations based on code analysis."""
    recommendations = []
    
    # Basic positive tests
    recommendations.append("Test with typical valid inputs")
    
    # Exception-based tests
    for exc_type in analysis["raises_exceptions"]:
        recommendations.append(f"Test conditions that raise {exc_type}")
    
    # Validation-based tests  
    if analysis["validation_checks"]:
        recommendations.append("Test invalid input types based on isinstance checks")
    
    # Edge case tests
    if "zero_check" in analysis["edge_cases"]:
        recommendations.append("Test with zero values (division by zero scenarios)")
    
    if "empty_string_check" in analysis["edge_cases"]:
        recommendations.append("Test with empty strings")
    
    analysis["test_recommendations"] = recommendations

def analyze_python_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze an entire Python file and extract testable functions and classes.
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}
    
    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except Exception as e:
        return {"error": f"Could not parse file: {e}"}
    
    analysis = {
        "file_path": file_path,
        "functions": [],
        "classes": [],
        "imports": []
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Extract function source
            func_start = node.lineno - 1
            func_end = node.end_lineno if hasattr(node, 'end_lineno') else func_start + 10
            lines = content.split('\n')
            func_source = '\n'.join(lines[func_start:func_end])
            
            func_analysis = analyze_function_for_testing(func_source, node.name)
            analysis["functions"].append(func_analysis)
        
        elif isinstance(node, ast.ClassDef):
            class_info = {
                "name": node.name,
                "methods": []
            }
            
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    # Analyze class methods
                    method_start = item.lineno - 1
                    method_end = item.end_lineno if hasattr(item, 'end_lineno') else method_start + 10
                    lines = content.split('\n')
                    method_source = '\n'.join(lines[method_start:method_end])
                    
                    method_analysis = analyze_function_for_testing(method_source, item.name)
                    class_info["methods"].append(method_analysis)
            
            analysis["classes"].append(class_info)
        
        elif isinstance(node, ast.Import):
            for alias in node.names:
                analysis["imports"].append(alias.name)
        
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for alias in node.names:
                    analysis["imports"].append(f"{node.module}.{alias.name}")
    
    return analysis

def generate_test_guidance(file_analysis: Dict[str, Any]) -> str:
    """
    Generate specific guidance for LLM test generation based on code analysis.
    """
    guidance = []
    guidance.append("=== AUTOMATED CODE ANALYSIS RESULTS ===\n")
    
    if "error" in file_analysis:
        guidance.append(f"⚠️ Analysis Error: {file_analysis['error']}\n")
        return "\n".join(guidance)
    
    # Function analysis
    if file_analysis.get("functions"):
        guidance.append("FUNCTIONS TO TEST:")
        for func in file_analysis["functions"]:
            guidance.append(f"\n📋 Function: {func['function_name']}")
            guidance.append(f"   Parameters: {func['parameters']}")
            
            if func["raises_exceptions"]:
                guidance.append(f"   ⚠️ Raises: {', '.join(func['raises_exceptions'])}")
            
            if func["test_recommendations"]:
                guidance.append("   💡 Test Recommendations:")
                for rec in func["test_recommendations"]:
                    guidance.append(f"      - {rec}")
    
    # Class analysis
    if file_analysis.get("classes"):
        guidance.append("\nCLASSES TO TEST:")
        for cls in file_analysis["classes"]:
            guidance.append(f"\n📋 Class: {cls['name']}")
            for method in cls["methods"]:
                guidance.append(f"   Method: {method['function_name']}")
                if method["raises_exceptions"]:
                    guidance.append(f"      ⚠️ Raises: {', '.join(method['raises_exceptions'])}")
    
    guidance.append("\n" + "="*50)
    guidance.append("USE THIS ANALYSIS TO GENERATE ACCURATE TESTS!")
    guidance.append("Only test the exception conditions that are actually implemented.")
    guidance.append("="*50)
    
    return "\n".join(guidance)

if __name__ == "__main__":
    # Test the analyzer on our test file
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        analysis = analyze_python_file(file_path)
        guidance = generate_test_guidance(analysis)
        print(guidance)