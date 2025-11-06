#!/usr/bin/env python3
"""
Lightweight Context Builder for Fast LLM Generation
==================================================

This is a performance-optimized version that generates minimal, focused
context for LLM test generation instead of comprehensive analysis.
"""

import json
import ast
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

def extract_function_signatures(file_path: Path) -> List[Dict[str, Any]]:
    """Extract just function signatures and docstrings for LLM context."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(content, filename=str(file_path))
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                # Extract just the signature and docstring
                signature = f"def {node.name}("
                args = []
                for arg in node.args.args:
                    args.append(arg.arg)
                signature += ", ".join(args) + "):"
                
                docstring = ast.get_docstring(node) or ""
                
                functions.append({
                    "name": node.name,
                    "signature": signature,
                    "docstring": docstring[:200],  # Limit docstring length
                    "line": node.lineno
                })
        
        return functions
        
    except Exception:
        return []

def extract_class_info(file_path: Path) -> List[Dict[str, Any]]:
    """Extract just class names and public methods."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(content, filename=str(file_path))
        
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                        methods.append(item.name)
                
                classes.append({
                    "name": node.name,
                    "methods": methods[:5],  # Limit to 5 methods
                    "line": node.lineno
                })
        
        return classes
        
    except Exception:
        return []

def build_lightweight_context() -> Dict[str, Any]:
    """Build minimal context optimized for fast LLM generation."""
    
    # Only scan specific directories to avoid virtual environments
    scan_dirs = ["tools", "llm_agent", "src"]
    target_files = []
    
    for dir_name in scan_dirs:
        dir_path = ROOT / dir_name
        if dir_path.exists():
            for py_file in dir_path.rglob("*.py"):
                # Skip test files and internal files
                if not any(part.startswith(('test_', '__pycache__', '.')) for part in py_file.parts):
                    target_files.append(py_file)
    
    # Limit to 5 files for fast processing
    target_files = target_files[:5]
    
    file_contexts = []
    for file_path in target_files:
        rel_path = str(file_path.relative_to(ROOT))
        
        # Extract minimal info
        functions = extract_function_signatures(file_path)
        classes = extract_class_info(file_path)
        
        if functions or classes:  # Only include files with testable content
            file_contexts.append({
                "file": rel_path,
                "module": rel_path.replace('/', '.').replace('.py', ''),
                "functions": functions[:3],  # Limit to 3 functions per file
                "classes": classes[:2],      # Limit to 2 classes per file
                "size": "small" if len(functions) + len(classes) <= 3 else "medium"
            })
    
    context = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "mode": "lightweight_generation",
        "file_count": len(file_contexts),
        "files": file_contexts,
        "test_framework": "pytest",
        "import_style": "from {module} import {symbols}"
    }
    
    # Save lightweight context
    output_path = ROOT / "genai_artifacts" / "lightweight_context.json"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(context, indent=2))
    
    print(f":: Lightweight context built: {len(file_contexts)} files")
    return context

if __name__ == "__main__":
    build_lightweight_context()