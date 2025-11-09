import os, re, json, subprocess, textwrap, pathlib, ast, inspect
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "ci_artifacts"
OUT_DIR.mkdir(exist_ok=True, parents=True)

def run(cmd, cwd=None):
    return subprocess.check_output(cmd, cwd=cwd or ROOT, text=True, shell=True)

def list_changed_files():
    # if first commit on CI you already handled; locally we fallback safely
    try:
        diff_list = run("git diff --name-only HEAD~1 HEAD").strip().splitlines()
        if not diff_list:
            # possibly no previous commit or nothing changed; include key .py files for demo
            py_files = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*.py") if p.is_file()]
            # Filter out our own llm_agent files to avoid recursion and focus on application code
            return [f for f in py_files if not f.startswith("llm_agent") and not f.startswith("tests")]
        return diff_list
    except subprocess.CalledProcessError:
        py_files = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*.py") if p.is_file()]
        # Filter out our own llm_agent files to avoid recursion and focus on application code
        return [f for f in py_files if not f.startswith("llm_agent") and not f.startswith("tests")]

def read_file(path):
    p = ROOT / path
    if p.exists() and p.is_file():
        try:
            return p.read_text(encoding="utf-8")[:200000]  # safety cap
        except UnicodeDecodeError:
            return ""
    return ""

IMPORT_RE = re.compile(r"^(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))", re.M)

def direct_imports(py_text):
    mods = set()
    for m in IMPORT_RE.finditer(py_text):
        pkg = m.group(1) or m.group(2)
        if not pkg:
            continue
        # keep first segment only (project-local modules assumed in repo)
        top = pkg.split(".")[0]
        mods.add(top)
    return mods

def find_local_module_file(mod_name):
    # simple heuristics: <mod>.py under repo root or under code/app folders
    candidates = [
        ROOT / f"{mod_name}.py",
        ROOT / "code" / f"{mod_name}.py",
        ROOT / "app" / f"{mod_name}.py",
        ROOT / "src" / f"{mod_name}.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

def get_unified_diff(path):
    try:
        return run(f"git diff --unified=3 HEAD~1 HEAD -- {path}")
    except subprocess.CalledProcessError:
        return ""

def small_read(path_like):
    p = ROOT / path_like
    if p.exists():
        try:
            txt = p.read_text(encoding="utf-8")
            return txt[:4000]  # keep it short
        except Exception:
            return ""
    return ""

# ==================== ENHANCED UNIVERSAL CONTEXT ANALYSIS ====================

class UniversalContextAnalyzer:
    """Universal context analyzer that works across any Python repository"""
    
    def __init__(self, root_path: Path):
        self.root = Path(root_path).resolve()
        self.python_files = self._safe_find_python_files()
    
    def _safe_find_python_files(self) -> List[Path]:
        """Safely find Python files, handling permission errors"""
        python_files = []
        
        # Skip these directories to avoid permission issues
        skip_dirs = {'.git', '.venv', 'venv', 'env', '__pycache__', 'node_modules', 
                    '.pytest_cache', '.tox', 'build', 'dist', '.egg-info'}
        
        try:
            for item in self.root.rglob("*.py"):
                # Check if any part of the path should be skipped
                if not any(part.startswith('.') or part in skip_dirs for part in item.parts):
                    try:
                        # Test if we can access the file
                        if item.exists() and item.is_file():
                            python_files.append(item)
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            # Fallback: manually walk directories
            python_files = self._manual_walk_for_python_files()
        
        return python_files
    
    def _manual_walk_for_python_files(self) -> List[Path]:
        """Manual directory walking as fallback"""
        python_files = []
        skip_dirs = {'.git', '.venv', 'venv', 'env', '__pycache__', 'node_modules'}
        
        try:
            for root, dirs, files in os.walk(self.root):
                # Remove skip directories from dirs to avoid walking them
                dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
                
                for file in files:
                    if file.endswith('.py'):
                        try:
                            file_path = Path(root) / file
                            if file_path.exists():
                                python_files.append(file_path)
                        except (OSError, PermissionError):
                            continue
        except (OSError, PermissionError):
            pass
        
        return python_files
    
    def scan_all_imports(self) -> Dict[str, Set[str]]:
        """Scan all Python files and extract available imports"""
        all_imports = {
            'stdlib': set(),
            'local': set(), 
            'external': set()
        }
        
        # Standard library modules (common ones)
        stdlib_modules = {
            'os', 'sys', 'json', 'ast', 'inspect', 're', 'pathlib', 'typing',
            'unittest', 'pytest', 'mock', 'datetime', 'collections', 'itertools',
            'functools', 'math', 'random', 'string', 'io', 'csv', 'sqlite3'
        }
        all_imports['stdlib'] = stdlib_modules
        
        # Scan for local and external imports
        for py_file in self.python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                imports = self.extract_imports_from_code(content)
                
                for imp in imports:
                    if imp in stdlib_modules:
                        all_imports['stdlib'].add(imp)
                    elif self.is_local_module(imp):
                        all_imports['local'].add(imp)
                    else:
                        all_imports['external'].add(imp)
                        
            except Exception:
                continue
                
        return all_imports
    
    def extract_imports_from_code(self, code: str) -> Set[str]:
        """Extract all imports from Python code using AST"""
        imports = set()
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
        except Exception:
            pass
        return imports
    
    def is_local_module(self, module_name: str) -> bool:
        """Check if a module is local to the repository"""
        # Check if there's a corresponding .py file
        candidates = [
            self.root / f"{module_name}.py",
            self.root / module_name / "__init__.py",
            self.root / "src" / f"{module_name}.py", 
            self.root / "src" / module_name / "__init__.py",
            self.root / "app" / f"{module_name}.py",
            self.root / "code" / f"{module_name}.py"
        ]
        return any(c.exists() for c in candidates)
    
    def extract_function_signatures(self) -> Dict[str, List[Dict]]:
        """Extract function signatures from all Python files"""
        signatures = {}
        
        for py_file in self.python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                rel_path = str(py_file.relative_to(self.root))
                signatures[rel_path] = self.parse_functions_from_code(content)
            except Exception:
                continue
                
        return signatures
    
    def parse_functions_from_code(self, code: str) -> List[Dict]:
        """Parse function signatures from code using AST"""
        functions = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip private functions for testing
                    if not node.name.startswith('_'):
                        func_info = {
                            'name': node.name,
                            'args': [arg.arg for arg in node.args.args],
                            'returns': self.get_return_annotation(node),
                            'docstring': ast.get_docstring(node),
                            'is_async': isinstance(node, ast.AsyncFunctionDef)
                        }
                        functions.append(func_info)
        except Exception:
            pass
        return functions
    
    def get_return_annotation(self, node: ast.FunctionDef) -> Optional[str]:
        """Extract return type annotation if available"""
        if node.returns:
            try:
                return ast.unparse(node.returns)
            except:
                return None
        return None
    
    def analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze the project structure and identify patterns"""
        structure = {
            'has_src_dir': (self.root / 'src').exists(),
            'has_app_dir': (self.root / 'app').exists(), 
            'has_code_dir': (self.root / 'code').exists(),
            'has_tests_dir': (self.root / 'tests').exists(),
            'framework': self.detect_framework(),
            'package_files': self.find_package_files(),
            'main_modules': self.identify_main_modules()
        }
        return structure
    
    def detect_framework(self) -> List[str]:
        """Detect which frameworks/libraries are being used"""
        frameworks = []
        
        # Check for common framework indicators
        framework_indicators = {
            'flask': ['from flask import', 'import flask'],
            'django': ['from django', 'import django', 'manage.py'],
            'fastapi': ['from fastapi import', 'import fastapi'],
            'pytest': ['import pytest', 'from pytest'],
            'pandas': ['import pandas', 'from pandas'],
            'numpy': ['import numpy', 'from numpy'],
            'sklearn': ['from sklearn', 'import sklearn'],
            'tensorflow': ['import tensorflow', 'from tensorflow'],
            'torch': ['import torch', 'from torch'],
            'gradio': ['import gradio', 'from gradio'],
            'streamlit': ['import streamlit', 'from streamlit']
        }
        
        all_content = ""
        for py_file in self.python_files:
            try:
                all_content += py_file.read_text(encoding='utf-8') + "\n"
            except:
                continue
        
        for framework, indicators in framework_indicators.items():
            if any(indicator in all_content for indicator in indicators):
                frameworks.append(framework)
                
        return frameworks
    
    def find_package_files(self) -> List[str]:
        """Find package/dependency files"""
        package_files = []
        candidates = [
            'requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile',
            'environment.yml', 'conda.yml', 'poetry.lock'
        ]
        
        for candidate in candidates:
            if (self.root / candidate).exists():
                package_files.append(candidate)
                
        return package_files
    
    def identify_main_modules(self) -> List[str]:
        """Identify the main application modules"""
        main_modules = []
        
        # Look for common main module patterns in python_files we already found safely
        main_patterns = ['main.py', 'app.py', 'run.py', '__main__.py']
        
        for py_file in self.python_files:
            filename = py_file.name
            if filename in main_patterns:
                try:
                    main_modules.append(str(py_file.relative_to(self.root)))
                except ValueError:
                    # Handle case where file is not relative to root
                    main_modules.append(str(py_file))
            
        return main_modules
    
    def generate_universal_test_examples(self) -> List[str]:
        """Generate universal test examples that work across frameworks"""
        return [
            """
# Example 1: Basic function test
def test_function_basic():
    result = my_function("input")
    assert result is not None
    assert isinstance(result, expected_type)
""",
            """
# Example 2: Exception handling test
def test_function_handles_invalid_input():
    with pytest.raises(ValueError):
        my_function(None)
    
    with pytest.raises(TypeError):
        my_function(123)  # when string expected
""",
            """
# Example 3: Mock external dependencies
@patch('module.external_api_call')
def test_function_with_mock(mock_api):
    mock_api.return_value = {"status": "success"}
    result = my_function_that_calls_api()
    assert result["status"] == "success"
    mock_api.assert_called_once()
""",
            """
# Example 4: Edge cases
def test_function_edge_cases():
    # Test empty input
    assert my_function("") == expected_empty_result
    
    # Test large input
    large_input = "x" * 1000
    result = my_function(large_input)
    assert len(result) > 0
    
    # Test special characters
    special_input = "test@#$%"
    result = my_function(special_input)
    assert result is not None
""",
            """
# Example 5: Configuration/settings test
def test_config_values():
    from src.config import SETTING_NAME
    assert isinstance(SETTING_NAME, int)
    assert SETTING_NAME > 0
"""
        ]

def gather_context():
    """Enhanced universal context gathering with deep analysis"""
    print("🔍 Starting enhanced universal context analysis...")
    
    # Initialize universal analyzer
    analyzer = UniversalContextAnalyzer(ROOT)
    
    changed = list_changed_files()
    changed = [f for f in changed if f.endswith(".py")]
    files_payload = []

    deps_seen = set()

    for f in changed:
        src = read_file(f)
        diff = get_unified_diff(f)
        files_payload.append({
            "path": f,
            "full_text": src,
            "unified_diff": diff
        })
        # shallow dependency harvest
        for mod in direct_imports(src):
            mod_file = find_local_module_file(mod)
            if mod_file and mod_file.exists():
                key = str(mod_file.relative_to(ROOT))
                if key not in deps_seen and key not in [x["path"] for x in files_payload]:
                    deps_seen.add(key)
                    files_payload.append({
                        "path": key,
                        "full_text": read_file(key),
                        "unified_diff": ""  # not changed, but context
                    })

    # Enhanced universal context
    print("📊 Analyzing project structure...")
    project_structure = analyzer.analyze_project_structure()
    
    print("📦 Scanning all imports...")
    all_imports = analyzer.scan_all_imports()
    
    print("🔧 Extracting function signatures...")
    function_signatures = analyzer.extract_function_signatures()
    
    print("📋 Generating universal test examples...")
    test_examples = analyzer.generate_universal_test_examples()

    context = {
        "readme": small_read("README.md"),
        "requirements": small_read("requirements.txt") or small_read("requirements/requirements.txt"),
        "sample_data": {},
        # Enhanced universal context
        "project_structure": project_structure,
        "available_imports": {
            "stdlib": sorted(list(all_imports['stdlib'])),
            "local": sorted(list(all_imports['local'])), 
            "external": sorted(list(all_imports['external']))
        },
        "function_signatures": function_signatures,
        "universal_test_examples": test_examples,
        "testing_guidelines": {
            "import_rules": [
                "Only import modules that exist in available_imports",
                "Use 'from unittest.mock import patch, Mock' for mocking",
                "Import local modules using relative paths (e.g., 'from src.module import function')",
                "Always define test data before using it"
            ],
            "test_patterns": [
                "Test basic functionality with valid inputs",
                "Test edge cases (empty, None, invalid inputs)",
                "Test exception handling with pytest.raises",
                "Use mocks for external dependencies",
                "Assert both return values and types"
            ],
            "common_mistakes": [
                "Don't use undefined variables",
                "Don't import non-existent modules", 
                "Don't hardcode expected values without context",
                "Don't assume specific data formats without checking"
            ]
        }
    }

    # include tiny sample rows from common data files if present
    for candidate in ["data/transactions.csv", "data/sample.json"]:
        p = ROOT / candidate
        if p.exists():
            context["sample_data"][candidate] = small_read(candidate)

    # Enhanced target harvesting with function signatures
    def harvest_enhanced_targets(files_payload, function_signatures):
        targets = {}
        
        for f in files_payload:
            if f["path"].endswith(".py") and f.get("full_text"):
                file_functions = []
                file_path = f["path"]
                
                # Get function signatures for this file
                if file_path in function_signatures:
                    file_functions = function_signatures[file_path]
                
                # Find dependents (files that import this module)
                dependents = []
                module_name = Path(file_path).stem
                
                for other_file in files_payload:
                    if other_file["path"] != file_path:
                        content = other_file.get("full_text", "")
                        if f"from {module_name}" in content or f"import {module_name}" in content:
                            dependents.append(other_file["path"])
                
                targets[file_path] = {
                    "functions": file_functions,
                    "dependents": dependents,
                    "testable_functions": [f for f in file_functions if not f.get('name', '').startswith('_')]
                }
        
        return targets

    targets = harvest_enhanced_targets(files_payload, function_signatures)

    bundle = {
        "files": files_payload, 
        "context": context, 
        "targets": targets,
        "analysis_metadata": {
            "total_python_files": len(analyzer.python_files),
            "files_analyzed": len(files_payload),
            "frameworks_detected": project_structure.get("framework", []),
            "has_tests_directory": project_structure.get("has_tests_dir", False)
        }
    }
    
    (OUT_DIR / "context_bundle.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"✅ Enhanced context written to {OUT_DIR/'context_bundle.json'}")
    print(f"📊 Analyzed {len(files_payload)} files with {len(targets)} targets")
    print(f"🔧 Detected frameworks: {', '.join(project_structure.get('framework', ['None']))}")
    print(f"📦 Available imports: {len(all_imports['local'])} local, {len(all_imports['external'])} external")

if __name__ == "__main__":
    gather_context()