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
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "genai_artifacts"
ARTIFACTS.mkdir(exist_ok=True)

class PublicSurfaceExtractor:
    """Extract public API surface from different language codebases"""
    
    @staticmethod
    def extract_python_surface(file_path: pathlib.Path) -> List[Dict[str, Any]]:
        """Extract Python functions, classes, and methods"""
        surface = []
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip private functions (starting with _)
                    if not node.name.startswith('_'):
                        surface.append({
                            "type": "function",
                            "name": node.name,
                            "line": node.lineno,
                            "args": [arg.arg for arg in node.args.args],
                            "docstring": ast.get_docstring(node),
                            "is_async": isinstance(node, ast.AsyncFunctionDef)
                        })
                
                elif isinstance(node, ast.ClassDef):
                    # Skip private classes
                    if not node.name.startswith('_'):
                        methods = []
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                                methods.append({
                                    "name": item.name,
                                    "line": item.lineno,
                                    "args": [arg.arg for arg in item.args.args],
                                    "is_property": any(
                                        isinstance(d, ast.Name) and d.id == 'property'
                                        for d in item.decorator_list
                                    )
                                })
                        
                        surface.append({
                            "type": "class",
                            "name": node.name,
                            "line": node.lineno,
                            "methods": methods,
                            "docstring": ast.get_docstring(node),
                            "bases": [base.id if isinstance(base, ast.Name) else str(base) 
                                     for base in node.bases]
                        })
        
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning(f"Could not parse Python file {file_path}: {e}")
        
        return surface
    
    @staticmethod
    def extract_javascript_surface(file_path: pathlib.Path) -> List[Dict[str, Any]]:
        """Extract JavaScript/TypeScript functions and classes (regex-based)"""
        surface = []
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Function declarations: function name() {} or const name = () => {}
            func_patterns = [
                r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(',
                r'const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*\([^)]*\)\s*=>',
                r'export\s+function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(',
            ]
            
            for pattern in func_patterns:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    name = match.group(1)
                    if not name.startswith('_'):  # Skip private functions
                        line_num = content[:match.start()].count('\n') + 1
                        surface.append({
                            "type": "function",
                            "name": name,
                            "line": line_num,
                            "exported": "export" in match.group(0)
                        })
            
            # Class declarations
            class_pattern = r'class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)'
            for match in re.finditer(class_pattern, content, re.MULTILINE):
                name = match.group(1)
                if not name.startswith('_'):
                    line_num = content[:match.start()].count('\n') + 1
                    surface.append({
                        "type": "class",
                        "name": name,
                        "line": line_num
                    })
        
        except UnicodeDecodeError as e:
            logger.warning(f"Could not read JavaScript file {file_path}: {e}")
        
        return surface
    
    @staticmethod
    def extract_java_surface(file_path: pathlib.Path) -> List[Dict[str, Any]]:
        """Extract Java public methods and classes (regex-based)"""
        surface = []
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Public class declarations
            class_pattern = r'public\s+class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)'
            for match in re.finditer(class_pattern, content, re.MULTILINE):
                name = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                surface.append({
                    "type": "class",
                    "name": name,
                    "line": line_num,
                    "visibility": "public"
                })
            
            # Public method declarations
            method_pattern = r'public\s+(?:static\s+)?[\w<>\[\]]+\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\('
            for match in re.finditer(method_pattern, content, re.MULTILINE):
                name = match.group(1)
                if name not in ['class']:  # Skip constructor-like patterns
                    line_num = content[:match.start()].count('\n') + 1
                    surface.append({
                        "type": "method",
                        "name": name,
                        "line": line_num,
                        "visibility": "public"
                    })
        
        except UnicodeDecodeError as e:
            logger.warning(f"Could not read Java file {file_path}: {e}")
        
        return surface

def detect_framework_and_conventions(stack: str) -> Dict[str, Any]:
    """Detect testing frameworks and conventions"""
    conventions = {
        "stack": stack,
        "test_framework": "unknown",
        "test_directories": [],
        "test_file_patterns": [],
        "mock_libraries": [],
        "coverage_tools": []
    }
    
    if stack == "python":
        # Check for pytest
        if (ROOT / "pytest.ini").exists() or (ROOT / "pyproject.toml").exists():
            with open(ROOT / "pyproject.toml" if (ROOT / "pyproject.toml").exists() 
                     else ROOT / "pytest.ini", 'r') as f:
                content = f.read()
                if 'pytest' in content:
                    conventions["test_framework"] = "pytest"
        
        # Look for test directories
        test_dirs = ["tests", "test", "testing"]
        for d in test_dirs:
            if (ROOT / d).is_dir():
                conventions["test_directories"].append(d)
        
        conventions["test_file_patterns"] = ["test_*.py", "*_test.py"]
        conventions["mock_libraries"] = ["unittest.mock", "pytest-mock", "responses"]
        conventions["coverage_tools"] = ["coverage.py", "pytest-cov"]
    
    elif stack == "node":
        # Check package.json for test framework
        package_json = ROOT / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    
                    if "jest" in deps:
                        conventions["test_framework"] = "jest"
                    elif "mocha" in deps:
                        conventions["test_framework"] = "mocha"
                    elif "vitest" in deps:
                        conventions["test_framework"] = "vitest"
            except json.JSONDecodeError:
                pass
        
        # Test directories
        test_dirs = ["__tests__", "tests", "test", "spec"]
        for d in test_dirs:
            if (ROOT / d).is_dir():
                conventions["test_directories"].append(d)
        
        conventions["test_file_patterns"] = ["*.test.js", "*.spec.js", "*.test.ts", "*.spec.ts"]
        conventions["mock_libraries"] = ["jest", "sinon", "nock"]
        conventions["coverage_tools"] = ["jest", "nyc", "c8"]
    
    elif stack == "java":
        # Check for Maven/Gradle test setup
        if (ROOT / "pom.xml").exists():
            try:
                with open(ROOT / "pom.xml") as f:
                    content = f.read()
                    if "junit" in content.lower():
                        conventions["test_framework"] = "junit"
                    elif "testng" in content.lower():
                        conventions["test_framework"] = "testng"
            except:
                pass
        
        # Standard Maven/Gradle test directory
        test_dir = ROOT / "src" / "test" / "java"
        if test_dir.is_dir():
            conventions["test_directories"].append("src/test/java")
        
        conventions["test_file_patterns"] = ["*Test.java", "Test*.java"]
        conventions["mock_libraries"] = ["mockito", "easymock", "powermock"]
        conventions["coverage_tools"] = ["jacoco", "cobertura"]
    
    return conventions

def analyze_dependencies(stack: str) -> Dict[str, Any]:
    """Analyze project dependencies and versions"""
    deps = {"stack": stack, "dependencies": [], "build_tools": []}
    
    try:
        if stack == "python":
            # Parse requirements.txt
            req_file = ROOT / "requirements.txt"
            if req_file.exists():
                content = req_file.read_text()
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        deps["dependencies"].append(line)
            
            # Parse pyproject.toml
            pyproject = ROOT / "pyproject.toml"
            if pyproject.exists():
                deps["build_tools"].append("pyproject.toml")
        
        elif stack == "node":
            package_json = ROOT / "package.json"
            if package_json.exists():
                with open(package_json) as f:
                    pkg = json.load(f)
                    
                    for dep_type in ["dependencies", "devDependencies"]:
                        if dep_type in pkg:
                            for name, version in pkg[dep_type].items():
                                deps["dependencies"].append(f"{name}@{version}")
                    
                    deps["build_tools"] = ["npm" if (ROOT / "package-lock.json").exists() else "yarn"]
        
        elif stack == "java":
            # Parse pom.xml (basic)
            pom_file = ROOT / "pom.xml"
            if pom_file.exists():
                deps["build_tools"].append("maven")
                # Basic dependency extraction (would need proper XML parsing for production)
                content = pom_file.read_text()
                artifact_pattern = r'<artifactId>([^<]+)</artifactId>'
                for match in re.finditer(artifact_pattern, content):
                    deps["dependencies"].append(match.group(1))
            
            # Check for Gradle
            if (ROOT / "build.gradle").exists() or (ROOT / "build.gradle.kts").exists():
                deps["build_tools"].append("gradle")
    
    except Exception as e:
        logger.warning(f"Error analyzing dependencies: {e}")
    
    return deps

def scan_existing_tests(stack: str, conventions: Dict[str, Any]) -> Dict[str, Any]:
    """Scan existing test files to understand current test patterns"""
    test_info = {
        "existing_test_files": [],
        "test_coverage_gaps": [],
        "test_patterns": []
    }
    
    # Find existing test files
    for test_dir in conventions["test_directories"]:
        test_path = ROOT / test_dir
        if test_path.is_dir():
            for pattern in conventions["test_file_patterns"]:
                # Convert glob pattern for pathlib
                if pattern.startswith('*'):
                    glob_pattern = pattern
                else:
                    glob_pattern = f"**/{pattern}"
                
                for test_file in test_path.rglob(glob_pattern.replace('*', '*')):
                    if test_file.is_file():
                        test_info["existing_test_files"].append(str(test_file.relative_to(ROOT)))
    
    logger.info(f"Found {len(test_info['existing_test_files'])} existing test files")
    return test_info

def get_security_constraints() -> Dict[str, Any]:
    """Define security constraints for LLM-generated code"""
    return {
        "allowed_imports": {
            "python": [
                "unittest", "pytest", "mock", "unittest.mock", "requests", "json", 
                "os", "sys", "pathlib", "tempfile", "datetime", "time", "re", 
                "collections", "itertools", "functools"
            ],
            "node": [
                "jest", "@testing-library", "supertest", "nock", "sinon", 
                "fs", "path", "util", "crypto", "assert"
            ],
            "java": [
                "org.junit", "org.mockito", "org.hamcrest", "java.util", 
                "java.time", "java.nio", "org.assertj"
            ]
        },
        "forbidden_patterns": [
            r"subprocess\.", r"eval\(", r"exec\(", r"__import__",  # Python
            r"child_process", r"eval\(", r"Function\(",  # Node.js
            r"Runtime\.getRuntime", r"ProcessBuilder",  # Java
            r"sleep\(", r"Thread\.sleep", r"setTimeout",  # All: avoid sleeps
            r"http://", r"https://",  # Network calls
            r"random\(\)" # Non-deterministic without seed
        ],
        "required_patterns": [
            r"assert", r"expect", r"should",  # Must have assertions
        ]
    }

def build_llm_context() -> Dict[str, Any]:
    """
    Build comprehensive context for LLM test generation
    Returns structured data to prevent hallucination
    """
    logger.info("Building LLM context for repository...")
    
    # Detect stack
    stack = detect_stack()
    logger.info(f"Detected stack: {stack}")
    
    # Build context
    context = {
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "repository_root": str(ROOT),
            "repository_name": ROOT.name,
            "stack": stack,
            "version": "2.0.0"
        },
        "repository_manifest": build_repository_manifest(),
        "public_surface": extract_public_surface(stack),
        "framework_conventions": detect_framework_and_conventions(stack),
        "dependencies": analyze_dependencies(stack),
        "existing_tests": None,  # Will be filled below
        "security_constraints": get_security_constraints(),
        "generation_guidelines": get_generation_guidelines(stack)
    }
    
    # Add existing test analysis
    context["existing_tests"] = scan_existing_tests(stack, context["framework_conventions"])
    
    # Save to artifacts
    context_file = ARTIFACTS / "context.json"
    context_file.write_text(json.dumps(context, indent=2))
    
    logger.info(f"Context saved to {context_file}")
    logger.info(f"Public surface: {len(context['public_surface'])} items")
    logger.info(f"Existing tests: {len(context['existing_tests']['existing_test_files'])}")
    
    return context

def detect_stack() -> str:
    """Detect project technology stack"""
    files = {f.name.lower() for f in ROOT.iterdir() if f.is_file()}
    
    if "pom.xml" in files or "build.gradle" in files:
        return "java"
    elif "package.json" in files:
        return "node"
    elif "requirements.txt" in files or "pyproject.toml" in files or "setup.py" in files:
        return "python"
    else:
        # Heuristic fallback
        py_files = list(ROOT.rglob("*.py"))
        js_files = list(ROOT.rglob("*.js")) + list(ROOT.rglob("*.ts"))
        java_files = list(ROOT.rglob("*.java"))
        
        if py_files and len(py_files) >= len(js_files) and len(py_files) >= len(java_files):
            return "python"
        elif js_files and len(js_files) >= len(java_files):
            return "node"
        elif java_files:
            return "java"
        else:
            return "unknown"

def build_repository_manifest() -> Dict[str, Any]:
    """Build repository file manifest and metadata"""
    all_files = []
    
    # Collect files with size limits for security
    for file_path in ROOT.rglob("*"):
        if file_path.is_file():
            try:
                size = file_path.stat().st_size
                if size < 1_000_000:  # Skip files > 1MB for security
                    rel_path = str(file_path.relative_to(ROOT))
                    all_files.append({
                        "path": rel_path,
                        "size": size,
                        "extension": file_path.suffix
                    })
            except (OSError, ValueError):
                continue
    
    # Limit total files for performance
    if len(all_files) > 1000:
        all_files = all_files[:1000]
    
    # File type analysis
    extensions = {}
    for file_info in all_files:
        ext = file_info["extension"].lower()
        extensions[ext] = extensions.get(ext, 0) + 1
    
    return {
        "total_files": len(all_files),
        "files": all_files,
        "file_types": extensions,
        "config_files": [
            f["path"] for f in all_files 
            if f["path"].split("/")[-1] in [
                "requirements.txt", "package.json", "pom.xml", "build.gradle",
                "pytest.ini", "jest.config.js", ".gitignore", "README.md"
            ]
        ]
    }

def extract_public_surface(stack: str) -> List[Dict[str, Any]]:
    """Extract public API surface for the detected stack"""
    extractor = PublicSurfaceExtractor()
    surface = []
    
    if stack == "python":
        for py_file in ROOT.rglob("*.py"):
            if not any(part.startswith('.') for part in py_file.parts):  # Skip hidden dirs
                file_surface = extractor.extract_python_surface(py_file)
                for item in file_surface:
                    item["file"] = str(py_file.relative_to(ROOT))
                surface.extend(file_surface)
    
    elif stack == "node":
        for js_file in ROOT.rglob("*.js"):
            file_surface = extractor.extract_javascript_surface(js_file)
            for item in file_surface:
                item["file"] = str(js_file.relative_to(ROOT))
            surface.extend(file_surface)
        
        for ts_file in ROOT.rglob("*.ts"):
            file_surface = extractor.extract_javascript_surface(ts_file)
            for item in file_surface:
                item["file"] = str(ts_file.relative_to(ROOT))
            surface.extend(file_surface)
    
    elif stack == "java":
        for java_file in ROOT.rglob("*.java"):
            file_surface = extractor.extract_java_surface(java_file)
            for item in file_surface:
                item["file"] = str(java_file.relative_to(ROOT))
            surface.extend(file_surface)
    
    # Limit results for performance and security
    return surface[:500]

def get_generation_guidelines(stack: str) -> Dict[str, Any]:
    """Get stack-specific test generation guidelines"""
    guidelines = {
        "python": {
            "test_structure": "AAA (Arrange, Act, Assert)",
            "naming_convention": "test_<function_name>_<scenario>",
            "assertion_style": "assert statement or pytest assertions",
            "fixture_usage": "Use @pytest.fixture for setup",
            "mock_style": "unittest.mock or pytest-mock",
            "file_naming": "test_<module>.py"
        },
        "node": {
            "test_structure": "describe/it blocks or test() functions",
            "naming_convention": "descriptive test names",
            "assertion_style": "expect() assertions",
            "fixture_usage": "beforeEach/afterEach or test-specific setup",
            "mock_style": "jest.mock() or sinon",
            "file_naming": "<module>.test.js or <module>.spec.js"
        },
        "java": {
            "test_structure": "@Test methods with clear names",
            "naming_convention": "test<MethodName><Scenario>",
            "assertion_style": "JUnit assertions or AssertJ",
            "fixture_usage": "@Before/@After or @BeforeEach/@AfterEach",
            "mock_style": "Mockito annotations and methods",
            "file_naming": "<ClassName>Test.java"
        }
    }
    
    return guidelines.get(stack, {})

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GenAI Test Platform - Context Builder")
    parser.add_argument("--output", default=str(ARTIFACTS / "context.json"), 
                       help="Output file path")
    parser.add_argument("--stack", choices=["python", "node", "java"], 
                       help="Override stack detection")
    
    args = parser.parse_args()
    
    try:
        context = build_llm_context()
        
        if args.output != str(ARTIFACTS / "context.json"):
            output_path = pathlib.Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(context, indent=2))
            print(f"Context written to: {output_path}")
        
        print(f"✅ Context building completed successfully")
        print(f"📊 Stack: {context['metadata']['stack']}")
        print(f"📁 Files analyzed: {context['repository_manifest']['total_files']}")
        print(f"🎯 Public surface items: {len(context['public_surface'])}")
        print(f"🧪 Existing test files: {len(context['existing_tests']['existing_test_files'])}")
        
    except Exception as e:
        logger.error(f"Context building failed: {e}")
        raise

if __name__ == "__main__":
    main()