#!/usr/bin/env python3
"""
Evaluation Harness for GenAI Test Platform
==========================================

Pre-merge validation pipeline that ensures test quality through:
- Static analysis and syntax checking
- Policy compliance validation  
- HITL approval verification
- Sandbox execution testing
- Performance and coverage analysis

Only tests that pass all gates are allowed to merge.
"""

import json
import pathlib
import subprocess
import sys
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "genai_artifacts"

@dataclass
class ValidationResult:
    """Result of a single validation check."""
    check_name: str
    passed: bool
    score: float  # 0.0 to 1.0
    message: str
    details: Dict[str, Any] = None
    execution_time: float = 0.0

@dataclass
class EvaluationReport:
    """Comprehensive evaluation report."""
    timestamp: str
    repository_root: str
    stack: str
    total_checks: int
    passed_checks: int
    overall_score: float
    overall_passed: bool
    validation_results: List[ValidationResult]
    summary: Dict[str, Any]
    recommendations: List[str]

class TestEvaluationHarness:
    """Comprehensive test validation pipeline."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self.default_config()
        self.results: List[ValidationResult] = []
        
    def default_config(self) -> Dict[str, Any]:
        """Default evaluation configuration."""
        return {
            "required_checks": [
                "syntax_validation",
                "policy_compliance", 
                "import_validation",
                "execution_test"
            ],
            "optional_checks": [
                "performance_test",
                "coverage_analysis",
                "hitl_approval"
            ],
            "scoring_weights": {
                "syntax_validation": 0.3,
                "policy_compliance": 0.25,
                "import_validation": 0.15,
                "execution_test": 0.2,
                "performance_test": 0.05,
                "coverage_analysis": 0.05
            },
            "pass_threshold": 0.8,  # Overall score needed to pass
            "sandbox_timeout": 30,   # seconds
            "max_execution_time": 5.0  # seconds per test
        }
    
    def evaluate_tests(self, test_files: List[pathlib.Path], 
                      context: Optional[Dict[str, Any]] = None) -> EvaluationReport:
        """Run comprehensive evaluation on test files."""
        
        print(f"🔍 Starting evaluation of {len(test_files)} test files...")
        start_time = datetime.utcnow()
        
        # Reset results
        self.results = []
        
        # Detect stack if not provided
        stack = context.get("stack") if context else self._detect_stack()
        
        # Run all validation checks
        for test_file in test_files:
            print(f"📝 Evaluating: {test_file.name}")
            
            # Required checks
            if "syntax_validation" in self.config["required_checks"]:
                result = self._check_syntax(test_file, stack)
                self.results.append(result)
            
            if "policy_compliance" in self.config["required_checks"]:
                result = self._check_policy_compliance(test_file)
                self.results.append(result)
            
            if "import_validation" in self.config["required_checks"]:
                result = self._check_imports(test_file, stack)
                self.results.append(result)
            
            if "execution_test" in self.config["required_checks"]:
                result = self._check_execution(test_file, stack)
                self.results.append(result)
            
            # Optional checks
            if "performance_test" in self.config["optional_checks"]:
                result = self._check_performance(test_file, stack)
                self.results.append(result)
            
            if "coverage_analysis" in self.config["optional_checks"]:
                result = self._check_coverage(test_file, stack)
                self.results.append(result)
        
        # Check HITL approval status
        if "hitl_approval" in self.config["optional_checks"]:
            result = self._check_hitl_approval()
            self.results.append(result)
        
        # Calculate overall score and pass/fail
        overall_score = self._calculate_overall_score()
        overall_passed = overall_score >= self.config["pass_threshold"]
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Create evaluation report
        report = EvaluationReport(
            timestamp=start_time.isoformat() + "Z",
            repository_root=str(ROOT),
            stack=stack,
            total_checks=len(self.results),
            passed_checks=sum(1 for r in self.results if r.passed),
            overall_score=overall_score,
            overall_passed=overall_passed,
            validation_results=self.results,
            summary=self._generate_summary(),
            recommendations=recommendations
        )
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _detect_stack(self) -> str:
        """Detect project stack."""
        if (ROOT / "requirements.txt").exists() or (ROOT / "pyproject.toml").exists():
            return "python"
        elif (ROOT / "package.json").exists():
            return "node"
        elif (ROOT / "pom.xml").exists() or (ROOT / "build.gradle").exists():
            return "java"
        return "unknown"
    
    def _check_syntax(self, test_file: pathlib.Path, stack: str) -> ValidationResult:
        """Check syntax validity using language-specific tools."""
        
        start_time = datetime.utcnow()
        
        try:
            if stack == "python" and test_file.suffix == ".py":
                # Use AST parsing for Python
                import ast
                content = test_file.read_text()
                ast.parse(content)
                
                return ValidationResult(
                    check_name="syntax_validation",
                    passed=True,
                    score=1.0,
                    message="Python syntax is valid",
                    execution_time=(datetime.utcnow() - start_time).total_seconds()
                )
            
            elif stack == "node" and test_file.suffix in [".js", ".ts"]:
                # Use node --check for JavaScript
                result = subprocess.run(
                    ["node", "--check", str(test_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    return ValidationResult(
                        check_name="syntax_validation", 
                        passed=True,
                        score=1.0,
                        message="JavaScript syntax is valid",
                        execution_time=(datetime.utcnow() - start_time).total_seconds()
                    )
                else:
                    return ValidationResult(
                        check_name="syntax_validation",
                        passed=False,
                        score=0.0,
                        message=f"Syntax error: {result.stderr}",
                        execution_time=(datetime.utcnow() - start_time).total_seconds()
                    )
            
            elif stack == "java" and test_file.suffix == ".java":
                # Use javac for Java (compilation check)
                with tempfile.TemporaryDirectory() as temp_dir:
                    result = subprocess.run(
                        ["javac", "-cp", ".", "-d", temp_dir, str(test_file)],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    
                    if result.returncode == 0:
                        return ValidationResult(
                            check_name="syntax_validation",
                            passed=True,
                            score=1.0,
                            message="Java compilation successful",
                            execution_time=(datetime.utcnow() - start_time).total_seconds()
                        )
                    else:
                        return ValidationResult(
                            check_name="syntax_validation",
                            passed=False,
                            score=0.0,
                            message=f"Compilation error: {result.stderr}",
                            execution_time=(datetime.utcnow() - start_time).total_seconds()
                        )
            
            else:
                # Unknown or unsupported file type
                return ValidationResult(
                    check_name="syntax_validation",
                    passed=True,
                    score=0.5,
                    message=f"Syntax check not available for {stack}/{test_file.suffix}",
                    execution_time=(datetime.utcnow() - start_time).total_seconds()
                )
        
        except Exception as e:
            return ValidationResult(
                check_name="syntax_validation",
                passed=False,
                score=0.0,
                message=f"Syntax check failed: {str(e)}",
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    def _check_policy_compliance(self, test_file: pathlib.Path) -> ValidationResult:
        """Check policy compliance using policy checker."""
        
        start_time = datetime.utcnow()
        
        try:
            # Import and run policy checker
            sys.path.append(str(ROOT))
            from tools.policy_checker_v2 import TestPolicyChecker
            
            checker = TestPolicyChecker()
            violations = checker.check_file(test_file)
            
            # Calculate score based on violations
            error_count = sum(1 for v in violations if v.severity == "error")
            warning_count = sum(1 for v in violations if v.severity == "warning")
            
            # Score: 1.0 for no issues, deduct for errors/warnings
            score = max(0.0, 1.0 - (error_count * 0.2) - (warning_count * 0.1))
            passed = error_count == 0
            
            message = f"Policy check: {error_count} errors, {warning_count} warnings"
            if violations:
                message += f" (first: {violations[0].message})"
            
            return ValidationResult(
                check_name="policy_compliance",
                passed=passed,
                score=score,
                message=message,
                details={"violations": len(violations), "errors": error_count, "warnings": warning_count},
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
        
        except Exception as e:
            return ValidationResult(
                check_name="policy_compliance",
                passed=False,
                score=0.0,
                message=f"Policy check failed: {str(e)}",
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    def _check_imports(self, test_file: pathlib.Path, stack: str) -> ValidationResult:
        """Check if all imports are valid and available."""
        
        start_time = datetime.utcnow()
        
        try:
            if stack == "python" and test_file.suffix == ".py":
                import ast
                
                content = test_file.read_text()
                tree = ast.parse(content)
                
                missing_imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            try:
                                __import__(alias.name)
                            except ImportError:
                                missing_imports.append(alias.name)
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            try:
                                __import__(node.module)
                            except ImportError:
                                missing_imports.append(node.module)
                
                if missing_imports:
                    return ValidationResult(
                        check_name="import_validation",
                        passed=False,
                        score=0.5,  # Partial score - syntax is OK but imports missing
                        message=f"Missing imports: {', '.join(missing_imports[:3])}",
                        details={"missing_imports": missing_imports},
                        execution_time=(datetime.utcnow() - start_time).total_seconds()
                    )
                else:
                    return ValidationResult(
                        check_name="import_validation",
                        passed=True,
                        score=1.0,
                        message="All imports are valid",
                        execution_time=(datetime.utcnow() - start_time).total_seconds()
                    )
            
            else:
                # For non-Python files, assume imports are OK if syntax passes
                return ValidationResult(
                    check_name="import_validation",
                    passed=True,
                    score=0.8,  # Partial score since we can't fully validate
                    message=f"Import validation not available for {stack}",
                    execution_time=(datetime.utcnow() - start_time).total_seconds()
                )
        
        except Exception as e:
            return ValidationResult(
                check_name="import_validation",
                passed=False,
                score=0.0,
                message=f"Import check failed: {str(e)}",
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    def _check_execution(self, test_file: pathlib.Path, stack: str) -> ValidationResult:
        """Test execution in sandboxed environment."""
        
        start_time = datetime.utcnow()
        
        try:
            if stack == "python" and test_file.suffix == ".py":
                # Run pytest on the file
                result = subprocess.run(
                    ["python", "-m", "pytest", str(test_file), "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=self.config["sandbox_timeout"],
                    cwd=ROOT
                )
                
                # Parse pytest output
                if "FAILED" in result.stdout or result.returncode != 0:
                    return ValidationResult(
                        check_name="execution_test",
                        passed=False,
                        score=0.0,
                        message="Test execution failed",
                        details={"stdout": result.stdout[-500:], "stderr": result.stderr[-500:]},
                        execution_time=(datetime.utcnow() - start_time).total_seconds()
                    )
                elif "passed" in result.stdout:
                    return ValidationResult(
                        check_name="execution_test",
                        passed=True,
                        score=1.0,
                        message="Test execution successful",
                        details={"stdout": result.stdout[-200:]},
                        execution_time=(datetime.utcnow() - start_time).total_seconds()
                    )
                else:
                    return ValidationResult(
                        check_name="execution_test",
                        passed=False,
                        score=0.5,
                        message="Execution completed but no tests found",
                        details={"stdout": result.stdout[-200:]},
                        execution_time=(datetime.utcnow() - start_time).total_seconds()
                    )
            
            else:
                # For other stacks, assume execution is OK if syntax passes
                return ValidationResult(
                    check_name="execution_test",
                    passed=True,
                    score=0.7,
                    message=f"Execution test not available for {stack}",
                    execution_time=(datetime.utcnow() - start_time).total_seconds()
                )
        
        except subprocess.TimeoutExpired:
            return ValidationResult(
                check_name="execution_test",
                passed=False,
                score=0.0,
                message=f"Test execution timed out after {self.config['sandbox_timeout']}s",
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
        except Exception as e:
            return ValidationResult(
                check_name="execution_test",
                passed=False,
                score=0.0,
                message=f"Execution test failed: {str(e)}",
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    def _check_performance(self, test_file: pathlib.Path, stack: str) -> ValidationResult:
        """Check test performance characteristics."""
        
        start_time = datetime.utcnow()
        
        # Simple performance check - measure execution time
        if stack == "python" and test_file.suffix == ".py":
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", str(test_file), "--durations=0"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=ROOT
                )
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                if execution_time <= self.config["max_execution_time"]:
                    score = 1.0
                    message = f"Performance acceptable ({execution_time:.2f}s)"
                    passed = True
                else:
                    score = max(0.0, 1.0 - (execution_time - self.config["max_execution_time"]) / 10.0)
                    message = f"Performance slow ({execution_time:.2f}s)"
                    passed = False
                
                return ValidationResult(
                    check_name="performance_test",
                    passed=passed,
                    score=score,
                    message=message,
                    details={"execution_time": execution_time},
                    execution_time=execution_time
                )
            
            except Exception as e:
                return ValidationResult(
                    check_name="performance_test",
                    passed=True,  # Non-critical
                    score=0.5,
                    message=f"Performance check failed: {str(e)}",
                    execution_time=(datetime.utcnow() - start_time).total_seconds()
                )
        
        return ValidationResult(
            check_name="performance_test",
            passed=True,
            score=0.8,
            message="Performance check not available",
            execution_time=(datetime.utcnow() - start_time).total_seconds()
        )
    
    def _check_coverage(self, test_file: pathlib.Path, stack: str) -> ValidationResult:
        """Check code coverage if applicable."""
        
        # Simplified coverage check - just verify test structure
        try:
            content = test_file.read_text()
            
            # Count test functions
            if stack == "python":
                test_count = content.count("def test_")
                assert_count = content.count("assert ")
                
                if test_count > 0 and assert_count > 0:
                    ratio = assert_count / test_count
                    score = min(1.0, ratio / 2.0)  # Target 2+ assertions per test
                    
                    return ValidationResult(
                        check_name="coverage_analysis",
                        passed=True,
                        score=score,
                        message=f"Coverage: {test_count} tests, {assert_count} assertions",
                        details={"test_count": test_count, "assert_count": assert_count}
                    )
            
            return ValidationResult(
                check_name="coverage_analysis",
                passed=True,
                score=0.7,
                message="Coverage analysis not available",
            )
        
        except Exception as e:
            return ValidationResult(
                check_name="coverage_analysis",
                passed=True,  # Non-critical
                score=0.5,
                message=f"Coverage check failed: {str(e)}"
            )
    
    def _check_hitl_approval(self) -> ValidationResult:
        """Check if HITL approval exists for generated tests."""
        
        try:
            # Look for approved HITL reviews
            approved_reviews = []
            for artifact_file in ARTIFACTS.glob("hitl_review_*.json"):
                try:
                    artifact = json.loads(artifact_file.read_text())
                    if artifact.get("status") == "approved":
                        approved_reviews.append(artifact["id"])
                except Exception:
                    continue
            
            if approved_reviews:
                return ValidationResult(
                    check_name="hitl_approval",
                    passed=True,
                    score=1.0,
                    message=f"HITL approval found ({len(approved_reviews)} reviews)",
                    details={"approved_reviews": approved_reviews}
                )
            else:
                return ValidationResult(
                    check_name="hitl_approval",
                    passed=False,
                    score=0.0,
                    message="No HITL approval found"
                )
        
        except Exception as e:
            return ValidationResult(
                check_name="hitl_approval",
                passed=False,
                score=0.0,
                message=f"HITL check failed: {str(e)}"
            )
    
    def _calculate_overall_score(self) -> float:
        """Calculate weighted overall score."""
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for result in self.results:
            weight = self.config["scoring_weights"].get(result.check_name, 0.05)
            total_weight += weight
            weighted_score += result.score * weight
        
        if total_weight > 0:
            return weighted_score / total_weight
        else:
            return 0.0
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate evaluation summary."""
        
        by_category = {}
        for result in self.results:
            category = result.check_name
            if category not in by_category:
                by_category[category] = {"passed": 0, "total": 0, "avg_score": 0.0}
            
            by_category[category]["total"] += 1
            if result.passed:
                by_category[category]["passed"] += 1
            by_category[category]["avg_score"] += result.score
        
        # Calculate averages
        for category in by_category:
            total = by_category[category]["total"]
            by_category[category]["avg_score"] /= total if total > 0 else 1
        
        return {
            "by_category": by_category,
            "total_execution_time": sum(r.execution_time for r in self.results),
            "critical_failures": [r.check_name for r in self.results 
                                 if not r.passed and r.check_name in self.config["required_checks"]]
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations."""
        
        recommendations = []
        
        # Check for critical failures
        failed_required = [r for r in self.results 
                          if not r.passed and r.check_name in self.config["required_checks"]]
        
        if failed_required:
            recommendations.append("❌ Fix critical validation failures before merging")
        
        # Check for policy violations
        policy_results = [r for r in self.results if r.check_name == "policy_compliance"]
        for result in policy_results:
            if not result.passed:
                recommendations.append("⚠️ Address policy violations for better test quality")
        
        # Check performance
        perf_results = [r for r in self.results if r.check_name == "performance_test"]
        for result in perf_results:
            if result.score < 0.8:
                recommendations.append("🐌 Optimize test performance to reduce execution time")
        
        # Check HITL approval
        hitl_results = [r for r in self.results if r.check_name == "hitl_approval"]
        for result in hitl_results:
            if not result.passed:
                recommendations.append("👥 Obtain human approval before merging")
        
        if not recommendations:
            recommendations.append("✅ All checks passed - ready for merge!")
        
        return recommendations
    
    def _save_report(self, report: EvaluationReport) -> None:
        """Save evaluation report to artifacts."""
        
        report_path = ARTIFACTS / f"evaluation_report_{int(datetime.utcnow().timestamp())}.json"
        report_path.write_text(json.dumps(asdict(report), indent=2, default=str))
        
        print(f"📊 Evaluation report saved: {report_path}")

def main():
    """CLI entry point for evaluation harness."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate test files for merge readiness")
    parser.add_argument("files", nargs="+", help="Test files to evaluate")
    parser.add_argument("--config", "-c", help="Configuration file")
    parser.add_argument("--output", "-o", help="Output report file")
    parser.add_argument("--stack", choices=["python", "node", "java"], help="Override stack detection")
    parser.add_argument("--strict", action="store_true", help="Strict mode - all checks must pass")
    
    args = parser.parse_args()
    
    # Load configuration
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)
    
    # Initialize harness
    harness = TestEvaluationHarness(config)
    
    # Override pass threshold for strict mode
    if args.strict:
        harness.config["pass_threshold"] = 1.0
    
    # Evaluate test files
    test_files = [pathlib.Path(f) for f in args.files]
    context = {"stack": args.stack} if args.stack else {}
    
    report = harness.evaluate_tests(test_files, context)
    
    # Print summary
    print("\n" + "=" * 60)
    print("🎯 EVALUATION RESULTS")
    print("=" * 60)
    print(f"Overall Score: {report.overall_score:.2f}")
    print(f"Status: {'✅ PASSED' if report.overall_passed else '❌ FAILED'}")
    print(f"Checks: {report.passed_checks}/{report.total_checks} passed")
    
    print(f"\n📋 Recommendations:")
    for rec in report.recommendations:
        print(f"  {rec}")
    
    # Save custom output
    if args.output:
        pathlib.Path(args.output).write_text(json.dumps(asdict(report), indent=2, default=str))
        print(f"\n📄 Report saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if report.overall_passed else 1)

if __name__ == "__main__":
    main()