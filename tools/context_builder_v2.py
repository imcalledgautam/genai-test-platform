#!/usr/bin/env python3
"""
Context Builder for GenAI Test Platform
=======================================

Extracts repository facts to prevent LLM hallucinations.
Provides structured context about:
- File structure and languages
- Public API surface (functions, classes, methods)
- Test conventions and frameworks
- Dependencies and build configuration

This ensures LLM-generated tests are grounded in repository reality.
"""

import json
import pathlib
import re
import ast
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]

def summarize_repo() -> Dict[str, Any]:
    """Generate a comprehensive repository manifest."""
    try:
        files = []
        for p in ROOT.rglob("*"):
            if p.is_file():
                try:
                    # Skip large binary files and build artifacts
                    if p.suffix in ['.pyc', '.pyo', '.so', '.dylib', '.dll', '.exe']:
                        continue
                    if any(part.startswith('.') for part in p.parts):
                        continue
                    if 'node_modules' in p.parts or '__pycache__' in p.parts:
                        continue
                    if 'target' in p.parts or 'build' in p.parts:
                        continue
                    
                    files.append(str(p.relative_to(ROOT)))
                except (ValueError, OSError):
                    continue
        
        # Language detection
        has_py = any(p.endswith(".py") for p in files)
        has_js = any(p.endswith((".js", ".ts", ".jsx", ".tsx")) for p in files)
        has_java = any(p.endswith(".java") for p in files)
        
        manifest = {
            "total_files": len(files),
            "files_sample": files[:100],  # Cap to prevent huge contexts
            "config_files": {
                "requirements_txt": (ROOT / "requirements.txt").exists(),
                "package_json": (ROOT / "package.json").exists(),
                "pom_xml": (ROOT / "pom.xml").exists(),
                "build_gradle": (ROOT / "build.gradle").exists(),
                "pyproject_toml": (ROOT / "pyproject.toml").exists()
            },
            "languages": {
                "python": has_py,
                "javascript": has_js,
                "java": has_java
            },
            "test_directories": [
                p for p in ["tests", "__tests__", "test", "src/test/java", "spec"]
                if (ROOT / p).exists()
            ]
        }
        
        return manifest
        
    except Exception as e:
        return {
            "error": f"Failed to summarize repository: {str(e)}",
            "total_files": 0,
            "files_sample": [],
            "config_files": {},
            "languages": {},
            "test_directories": []
        }

def extract_python_surface() -> List[Dict[str, Any]]:
    """Extract public functions and classes from Python files."""
    surface = []
    
    try:
        files_processed = 0
        for py_file in ROOT.rglob("*.py"):
            # Skip test files, __pycache__, virtual environments, and hidden dirs
            if any(part.startswith(('test_', '__pycache__', '.')) for part in py_file.parts):
                continue
            if any(part in ('tests', 'venv', '.venv', 'env', '.env', 'node_modules', 'site-packages') for part in py_file.parts):
                continue
            
            files_processed += 1
            # Limit processing to avoid infinite loops with large repositories
            if files_processed > 50:
                print(f":: Limiting to 50 files for performance")
                break
                
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                tree = ast.parse(content, filename=str(py_file))
                
                rel_path = str(py_file.relative_to(ROOT))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Only public functions (not starting with _)
                        if not node.name.startswith('_'):
                            surface.append({
                                "file": rel_path,
                                "symbol": node.name,
                                "type": "function",
                                "line": node.lineno
                            })
                    
                    elif isinstance(node, ast.ClassDef):
                        # Only public classes
                        if not node.name.startswith('_'):
                            surface.append({
                                "file": rel_path,
                                "symbol": node.name,
                                "type": "class",
                                "line": node.lineno
                            })
                            
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue
                
    except Exception as e:
        print(f"Warning: Failed to extract Python surface: {e}")
        
    return surface

def extract_public_surface() -> Dict[str, List[Dict[str, Any]]]:
    """Extract public API surface for all detected languages."""
    surface = {
        "python": [],
        "javascript": [],
        "java": []
    }
    
    manifest = summarize_repo()
    
    if manifest["languages"].get("python", False):
        surface["python"] = extract_python_surface()
    
    return surface

def build_llm_context() -> Dict[str, Any]:
    """Build comprehensive context for LLM test generation."""
    print(":: Building LLM context from repository...")
    
    context = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "repository_root": str(ROOT),
        "manifest": summarize_repo(),
        "public_surface": extract_public_surface(),
        "conventions": {
            "python": {
                "tests_dir": "tests",
                "test_file_pattern": "test_*.py",
                "framework": "pytest"
            },
            "javascript": {
                "tests_dir": "__tests__",
                "test_file_pattern": "*.test.js",
                "framework": "jest"
            },
            "java": {
                "tests_dir": "src/test/java",
                "test_file_pattern": "*Test.java",
                "framework": "junit"
            }
        }
    }
    
    # Save context to artifacts
    output_path = ROOT / "genai_artifacts" / "context.json"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(context, indent=2))
    
    print(f":: Context saved to {output_path}")
    print(f":: Found {len(context['public_surface']['python'])} Python symbols")
    
    return context

if __name__ == "__main__":
    build_llm_context()
