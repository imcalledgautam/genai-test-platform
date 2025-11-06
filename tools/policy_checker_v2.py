#!/usr/bin/env python3
"""
Policy Checker for GenAI Test Platform
======================================

Enforces test quality guardrails and validation hooks.
Ensures LLM-generated tests follow best practices:
- No flaky patterns (sleep, random without seed, network calls)
- Deterministic behavior
- Proper isolation and mocking
- Clear assertions
- Valid imports and syntax

This prevents bad tests from being merged into the codebase.
"""

import ast
import re
import json
import pathlib
import subprocess
import sys
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PolicyViolation:
    """Represents a policy violation found in test code."""
    file_path: str
    line: int
    rule: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    code_snippet: str = ""

class TestPolicyChecker:
    """Comprehensive test quality checker with configurable rules."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self.default_config()
        self.violations: List[PolicyViolation] = []
        
    def default_config(self) -> Dict[str, Any]:
        """Default policy configuration."""
        return {
            "forbidden_imports": [
                "time.sleep",
                "random.random", 
                "requests.get",
                "requests.post",
                "urllib.request",
                "socket",
                "http.client",
                "subprocess.run",
                "os.system"
            ],
            "allowed_test_imports": [
                "pytest", "unittest", "mock", "unittest.mock",
                "pytest_mock", "responses", "httpx_mock"
            ],
            "required_patterns": {
                "python": [r"def test_\w+", r"class Test\w+"],
                "javascript": [r"describe\(", r"it\(", r"test\("],
                "java": [r"@Test", r"public.*test\w+"]
            },
            "forbidden_patterns": [
                r"time\.sleep\(",
                r"Thread\.sleep\(",
                r"setTimeout\(",
                r"random\(\)",
                r"Math\.random\(\)",
                r"new Date\(\)",
                r"datetime\.now\(\)",
                r"\.real\b",  # accessing real network/db
                r"localhost:\d+",
                r"127\.0\.0\.1",
                r"http://",
                r"https://",
                r"assert True\b",
                r"assert False\b",
                r"assertTrue\(True\)",
                r"assertFalse\(False\)"
            ],
            "max_file_size": 10000,  # characters
            "max_test_lines": 100
        }
    
    def check_file(self, file_path: pathlib.Path) -> List[PolicyViolation]:
        """Check a single test file for policy violations."""
        violations = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Check file size
            if len(content) > self.config["max_file_size"]:
                violations.append(PolicyViolation(
                    file_path=str(file_path),
                    line=1,
                    rule="file_size",
                    severity="warning",
                    message=f"File too large ({len(content)} chars, max {self.config['max_file_size']})"
                ))
            
            # Check forbidden patterns
            violations.extend(self._check_forbidden_patterns(file_path, content, lines))
            
            # Language-specific checks
            if file_path.suffix == '.py':
                violations.extend(self._check_python_specific(file_path, content))
            elif file_path.suffix in ['.js', '.ts']:
                violations.extend(self._check_javascript_specific(file_path, content))
            elif file_path.suffix == '.java':
                violations.extend(self._check_java_specific(file_path, content))
            
            # Check test structure
            violations.extend(self._check_test_structure(file_path, content, lines))
            
        except Exception as e:
            violations.append(PolicyViolation(
                file_path=str(file_path),
                line=1,
                rule="parse_error",
                severity="error",
                message=f"Failed to parse file: {str(e)}"
            ))
        
        return violations
    
    def _check_forbidden_patterns(self, file_path: pathlib.Path, content: str, lines: List[str]) -> List[PolicyViolation]:
        """Check for forbidden patterns that make tests flaky or unsafe."""
        violations = []
        
        for pattern in self.config["forbidden_patterns"]:
            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    violations.append(PolicyViolation(
                        file_path=str(file_path),
                        line=line_num,
                        rule="forbidden_pattern",
                        severity="error",
                        message=f"Forbidden pattern '{pattern}' found",
                        code_snippet=line.strip()
                    ))
        
        return violations
    
    def _check_python_specific(self, file_path: pathlib.Path, content: str) -> List[PolicyViolation]:
        """Python-specific policy checks."""
        violations = []
        
        try:
            # Parse AST for deeper analysis
            tree = ast.parse(content)
            
            # Check imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.config["forbidden_imports"]:
                            violations.append(PolicyViolation(
                                file_path=str(file_path),
                                line=node.lineno,
                                rule="forbidden_import",
                                severity="error",
                                message=f"Forbidden import: {alias.name}"
                            ))
                
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module or ""
                    for alias in node.names:
                        full_name = f"{module_name}.{alias.name}"
                        if full_name in self.config["forbidden_imports"]:
                            violations.append(PolicyViolation(
                                file_path=str(file_path),
                                line=node.lineno,
                                rule="forbidden_import",
                                severity="error",
                                message=f"Forbidden import: {full_name}"
                            ))
                
                # Check for proper test structure
                elif isinstance(node, ast.FunctionDef):
                    if node.name.startswith('test_'):
                        # Check test function length
                        func_lines = node.end_lineno - node.lineno + 1
                        if func_lines > self.config["max_test_lines"]:
                            violations.append(PolicyViolation(
                                file_path=str(file_path),
                                line=node.lineno,
                                rule="test_too_long",
                                severity="warning",
                                message=f"Test function too long ({func_lines} lines, max {self.config['max_test_lines']})"
                            ))
                        
                        # Check for proper assertions
                        has_assertion = False
                        for child in ast.walk(node):
                            if isinstance(child, ast.Assert) or (
                                isinstance(child, ast.Call) and 
                                isinstance(child.func, ast.Attribute) and
                                child.func.attr.startswith('assert')
                            ):
                                has_assertion = True
                                break
                        
                        if not has_assertion:
                            violations.append(PolicyViolation(
                                file_path=str(file_path),
                                line=node.lineno,
                                rule="no_assertions",
                                severity="error",
                                message=f"Test function '{node.name}' has no assertions"
                            ))
        
        except SyntaxError as e:
            violations.append(PolicyViolation(
                file_path=str(file_path),
                line=e.lineno or 1,
                rule="syntax_error",
                severity="error",
                message=f"Python syntax error: {str(e)}"
            ))
        
        return violations
    
    def _check_javascript_specific(self, file_path: pathlib.Path, content: str) -> List[PolicyViolation]:
        """JavaScript/TypeScript-specific policy checks."""
        violations = []
        
        # Check for test framework patterns
        has_test_framework = False
        for pattern in self.config["required_patterns"]["javascript"]:
            if re.search(pattern, content):
                has_test_framework = True
                break
        
        if not has_test_framework:
            violations.append(PolicyViolation(
                file_path=str(file_path),
                line=1,
                rule="no_test_framework",
                severity="error",
                message="No test framework patterns found (describe, it, test)"
            ))
        
        # Check for proper async handling
        async_without_await = re.findall(r'(async\s+\w+.*?\{(?:[^{}]*\{[^{}]*\})*[^{}]*\})', content, re.DOTALL)
        for match in async_without_await:
            if 'await' not in match and 'return' not in match:
                violations.append(PolicyViolation(
                    file_path=str(file_path),
                    line=content[:content.find(match)].count('\n') + 1,
                    rule="async_without_await",
                    severity="warning",
                    message="Async function without await or return"
                ))
        
        return violations
    
    def _check_java_specific(self, file_path: pathlib.Path, content: str) -> List[PolicyViolation]:
        """Java-specific policy checks."""
        violations = []
        
        # Check for @Test annotation
        if not re.search(r'@Test', content):
            violations.append(PolicyViolation(
                file_path=str(file_path),
                line=1,
                rule="no_test_annotation",
                severity="error",
                message="No @Test annotations found"
            ))
        
        # Check for proper imports
        if '@Test' in content and not re.search(r'import.*junit.*Test', content):
            violations.append(PolicyViolation(
                file_path=str(file_path),
                line=1,
                rule="missing_junit_import",
                severity="error",
                message="Using @Test but missing JUnit import"
            ))
        
        return violations
    
    def _check_test_structure(self, file_path: pathlib.Path, content: str, lines: List[str]) -> List[PolicyViolation]:
        """Check general test structure and quality."""
        violations = []
        
        # Check for descriptive test names
        test_functions = re.findall(r'def (test_\w+)', content)
        for func_name in test_functions:
            if len(func_name) < 10:  # Very short test names
                violations.append(PolicyViolation(
                    file_path=str(file_path),
                    line=1,  # Would need more parsing to get exact line
                    rule="short_test_name",
                    severity="warning",
                    message=f"Test name '{func_name}' should be more descriptive"
                ))
        
        # Check for TODO/FIXME comments in tests
        for line_num, line in enumerate(lines, 1):
            if re.search(r'(TODO|FIXME|XXX)', line, re.IGNORECASE):
                violations.append(PolicyViolation(
                    file_path=str(file_path),
                    line=line_num,
                    rule="todo_comment",
                    severity="info",
                    message="Test contains TODO/FIXME comment",
                    code_snippet=line.strip()
                ))
        
        return violations
    
    def check_directory(self, directory: pathlib.Path) -> Dict[str, List[PolicyViolation]]:
        """Check all test files in a directory."""
        results = {}
        
        test_patterns = ["test_*.py", "*_test.py", "*.test.js", "*.spec.js", "*Test.java"]
        
        for pattern in test_patterns:
            for test_file in directory.rglob(pattern):
                if test_file.is_file():
                    violations = self.check_file(test_file)
                    if violations:
                        results[str(test_file)] = violations
        
        return results
    
    def validate_syntax(self, file_path: pathlib.Path) -> bool:
        """Validate syntax using language-specific tools."""
        try:
            if file_path.suffix == '.py':
                # Use ast.parse for Python
                content = file_path.read_text()
                ast.parse(content)
                return True
            
            elif file_path.suffix in ['.js', '.ts']:
                # Use node for JavaScript/TypeScript (if available)
                result = subprocess.run(
                    ['node', '--check', str(file_path)],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            
            elif file_path.suffix == '.java':
                # Use javac for Java (if available)
                result = subprocess.run(
                    ['javac', '-cp', '.', str(file_path)],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            
        except Exception:
            pass
        
        return True  # If tools aren't available, assume valid
    
    def generate_report(self, results: Dict[str, List[PolicyViolation]]) -> Dict[str, Any]:
        """Generate a comprehensive policy check report."""
        total_violations = sum(len(violations) for violations in results.values())
        error_count = sum(1 for violations in results.values() 
                         for v in violations if v.severity == 'error')
        warning_count = sum(1 for violations in results.values() 
                           for v in violations if v.severity == 'warning')
        
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "summary": {
                "files_checked": len(results),
                "total_violations": total_violations,
                "errors": error_count,
                "warnings": warning_count,
                "passed": error_count == 0
            },
            "violations_by_file": {},
            "violations_by_rule": {},
            "config": self.config
        }
        
        # Group violations by file and rule
        for file_path, violations in results.items():
            report["violations_by_file"][file_path] = [
                {
                    "line": v.line,
                    "rule": v.rule,
                    "severity": v.severity,
                    "message": v.message,
                    "code_snippet": v.code_snippet
                }
                for v in violations
            ]
            
            for violation in violations:
                if violation.rule not in report["violations_by_rule"]:
                    report["violations_by_rule"][violation.rule] = 0
                report["violations_by_rule"][violation.rule] += 1
        
        return report

def main():
    """CLI entry point for policy checker."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check test files for policy violations")
    parser.add_argument("path", help="File or directory to check")
    parser.add_argument("--config", "-c", help="Configuration file (JSON)")
    parser.add_argument("--output", "-o", help="Output report file")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    
    args = parser.parse_args()
    
    # Load configuration
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)
    
    # Initialize checker
    checker = TestPolicyChecker(config)
    
    # Check files
    path = pathlib.Path(args.path)
    if path.is_file():
        violations = checker.check_file(path)
        results = {str(path): violations} if violations else {}
    else:
        results = checker.check_directory(path)
    
    # Generate report
    report = checker.generate_report(results)
    
    # Output report
    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        # Text format
        lines = [
            "=" * 60,
            "Test Policy Check Report",
            "=" * 60,
            f"Files checked: {report['summary']['files_checked']}",
            f"Total violations: {report['summary']['total_violations']}",
            f"Errors: {report['summary']['errors']}",
            f"Warnings: {report['summary']['warnings']}",
            f"Status: {'✅ PASSED' if report['summary']['passed'] else '❌ FAILED'}",
            ""
        ]
        
        if report["violations_by_file"]:
            lines.append("Violations by file:")
            lines.append("-" * 40)
            for file_path, violations in report["violations_by_file"].items():
                lines.append(f"\n📄 {file_path}")
                for v in violations:
                    emoji = "🚨" if v["severity"] == "error" else "⚠️" if v["severity"] == "warning" else "ℹ️"
                    lines.append(f"  {emoji} Line {v['line']}: {v['message']} ({v['rule']})")
                    if v["code_snippet"]:
                        lines.append(f"     Code: {v['code_snippet']}")
        
        output = "\n".join(lines)
    
    # Save or print
    if args.output:
        pathlib.Path(args.output).write_text(output)
        print(f"Report saved to {args.output}")
    else:
        print(output)
    
    # Exit code
    has_errors = report['summary']['errors'] > 0
    has_warnings = report['summary']['warnings'] > 0
    
    if has_errors or (args.strict and has_warnings):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()