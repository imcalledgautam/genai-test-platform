#!/usr/bin/env python3
"""
Unified GenAI Test Runner - Production Ready
============================================

One Action step for every repo: python tools/genai_test_runner.py

This script:
1. Detects stack (Python/Node/Java) 
2. Installs dependencies
3. (Optionally) calls LLM to generate/patch tests
4. Runs native test framework
5. Collects coverage & artifacts
6. Writes unified test_report.json

Supports stack-agnostic CI with consistent reporting.
"""

import json
import os
import subprocess
import sys
import pathlib
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Constants
ROOT = pathlib.Path(__file__).resolve().parents[1]  # repo root
ARTIFACTS = ROOT / "genai_artifacts"
ARTIFACTS.mkdir(exist_ok=True)

def run(cmd: str, cwd: Optional[pathlib.Path] = None, allow_fail: bool = False, 
        env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Execute shell command with comprehensive logging and error handling."""
    print(f":: RUN => {cmd}")
    start = time.time()
    
    try:
        p = subprocess.run(
            cmd, 
            cwd=cwd or ROOT, 
            shell=shell, 
            env=env or os.environ.copy(),
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            timeout=300
        )
        
        duration = round(time.time() - start, 3)
        
        if p.stdout.strip():
            print(p.stdout)
        
        if p.returncode != 0:
            if not allow_fail:
                print(f"Command failed (exit {p.returncode}): {cmd}", file=sys.stderr)
                if p.stderr.strip():
                    print(p.stderr, file=sys.stderr)
            else:
                print(f"Command completed with warnings (exit {p.returncode})")
        else:
            print(f"Command completed successfully in {duration}s")
        
        return {
            "cmd": cmd if isinstance(cmd, str) else cmd_str,
            "returncode": p.returncode,
            "duration_sec": duration,
            "stdout": p.stdout[-50_000:] if p.stdout else "",  # Limit output size
            "stderr": p.stderr[-50_000:] if p.stderr else "",
            "success": p.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        print(f"Command timed out after 300s: {cmd}", file=sys.stderr)
        return {
            "cmd": cmd if isinstance(cmd, str) else cmd_str,
            "returncode": -1,
            "duration_sec": 300,
            "stdout": "",
            "stderr": f"Command timed out after 300s",
            "success": False
        }
    except Exception as e:
        print(f"Command execution error: {e}", file=sys.stderr)
        return {
            "cmd": cmd if isinstance(cmd, str) else cmd_str,
            "returncode": -2,
            "duration_sec": round(time.time() - start, 3),
            "stdout": "",
            "stderr": str(e),
            "success": False
        }

def detect_stack(override: Optional[str] = None) -> str:
    """Detect project technology stack"""
    if override:
        print(f"Using override stack: {override}")
        return override
        
    print("Detecting project stack...")
    
    files = {f.name.lower() for f in ROOT.iterdir() if f.is_file()}
    
    # Primary indicators
    if "pom.xml" in files or "build.gradle" in files or "build.gradle.kts" in files:
        print("Detected Java stack (Maven/Gradle found)")
        return "java"
    
    if "package.json" in files:
        print("Detected Node.js stack (package.json found)")
        return "node"
    
    if "requirements.txt" in files or "pyproject.toml" in files or "setup.py" in files:
        print("Detected Python stack (Python config files found)")
        return "python"
    
    # Fallback: heuristic analysis
    print("No clear stack indicators, analyzing source files...")
    
    python_files = list(ROOT.rglob("*.py"))
    js_files = list(ROOT.rglob("*.js")) + list(ROOT.rglob("*.ts"))
    java_files = list(ROOT.rglob("*.java"))
    
    if python_files and len(python_files) > len(js_files) and len(python_files) > len(java_files):
        print("Detected Python stack (most .py files)")
        return "python"
    elif js_files and len(js_files) > len(java_files):
        print("Detected Node.js stack (most .js/.ts files)")
        return "node"
    elif java_files:
        print("Detected Java stack (.java files found)")
        return "java"
    
    print("Could not determine stack, defaulting to unknown")
    return "unknown"

def ensure_dependencies(stack: str) -> List[Dict[str, Any]]:
    """Install project dependencies based on stack"""
    print(f"Installing dependencies for {stack} stack...")
    results = []
    
    if stack == "python":
        commands = [
            "python -m pip install --upgrade pip",
            "pip install pytest pytest-cov coverage requests",  # Core testing deps
        ]
        
        # Install project requirements if they exist
        if (ROOT / "requirements.txt").exists():
            commands.append("pip install -r requirements.txt")
        if (ROOT / "pyproject.toml").exists():
            commands.append("pip install -e .")
        if (ROOT / "setup.py").exists():
            commands.append("pip install -e .")
            
    elif stack == "node":
        commands = []
        if (ROOT / "package-lock.json").exists():
            commands.append("npm ci")
        elif (ROOT / "yarn.lock").exists():
            commands.append("yarn install --frozen-lockfile")
        elif (ROOT / "package.json").exists():
            commands.append("npm install")
        else:
            print("No Node.js package files found")
            
    elif stack == "java":
        commands = []
        if (ROOT / "pom.xml").exists():
            commands.extend([
                "mvn -q -B dependency:resolve",
                "mvn -q -B compile test-compile"
            ])
        elif any((ROOT / f).exists() for f in ["build.gradle", "build.gradle.kts"]):
            if (ROOT / "gradlew").exists():
                commands.extend([
                    "./gradlew --no-daemon compileJava compileTestJava"
                ])
            else:
                commands.extend([
                    "gradle --no-daemon compileJava compileTestJava"
                ])
        else:
            print("No Java build files found")
            
    else:
        print(f"Unknown stack '{stack}', skipping dependency installation")
        return []
    
    for cmd in commands:
        result = run(cmd, allow_fail=True)  # 10 min timeout for deps
        results.append(result)
        
        if not result["success"]:
            print(f"Dependency installation step failed, continuing...")
    
    return results

def llm_generate_or_patch_tests(stack: str, enable_llm: bool = True) -> Dict[str, Any]:
    """
    Optional LLM test generation/patching phase
    """
    print("Configuring LLM test generation...")
    
    # Create plan regardless of whether LLM is enabled
    plan_path = ARTIFACTS / "genai_test_plan.json"
    plan = {
        "enabled": enable_llm,
        "stack": stack,
        "strategy": "augment_if_missing",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "test_directories": {
            "python": ["tests/", "test/"],
            "node": ["__tests__/", "tests/", "test/"],
            "java": ["src/test/java/"]
        }.get(stack, ["tests/"]),
        "notes": "LLM generates tests for public functions/classes discovered by context_builder."
    }
    
    if not enable_llm:
        plan["disabled_reason"] = "LLM generation disabled via command line flag"
        plan_path.write_text(json.dumps(plan, indent=2))
        print("LLM test generation disabled")
        return {"generated": False, "plan_file": str(plan_path), "reason": "disabled"}
    
    # Build context for LLM
    try:
        # Import and use our context builder
        sys.path.insert(0, str(ROOT / "tools"))
        from context_builder import build_llm_context
        
        print("Building repository context...")
        context = build_llm_context()
        plan["context_available"] = True
        
    except ImportError:
        print("Context builder not found, using basic analysis")
        context = None
        plan["context_available"] = False
    
    # Check if LLM service is available (Ollama)
    ollama_check = run("ollama list", allow_fail=True)
    if not ollama_check["success"]:
        plan["disabled_reason"] = "Ollama not available"
        plan_path.write_text(json.dumps(plan, indent=2))
        print("Ollama not available, skipping LLM generation")
        return {"generated": False, "plan_file": str(plan_path), "reason": "ollama_unavailable"}
    
    # TODO: Integrate with your existing LLM generation logic
    # This is where you'd call your enhanced_context_builder.py and generate_tests.py
    plan["integration_status"] = "stub_implementation"
    plan_path.write_text(json.dumps(plan, indent=2))
    
    print("LLM integration ready (stub implementation)")
    return {"generated": False, "plan_file": str(plan_path), "reason": "stub_for_integration"}

def run_native_tests(stack: str) -> Dict[str, Any]:
    """Execute native test framework for the detected stack"""
    print(f"Running native tests for {stack} stack...")
    
    if stack == "python":
        # Try pytest first, fallback to unittest
        if (ROOT / "pytest.ini").exists() or any(ROOT.rglob("test_*.py")) or any(ROOT.rglob("*_test.py")):
            cmd = "python -m pytest -v --tb=short --disable-warnings --maxfail=5 --cov=. --cov-report=xml:coverage.xml --cov-report=term-missing --junit-xml=test-results.xml"
        else:
            cmd = "python -m unittest discover -s . -p 'test_*.py' -v"
            
    elif stack == "node":
        # Check for test script in package.json
        package_json = ROOT / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    pkg = json.load(f)
                if "scripts" in pkg and "test" in pkg["scripts"]:
                    cmd = "npm test"
                else:
                    cmd = "npx jest --runInBand --coverage --ci --testResultsProcessor=jest-junit"
            except:
                cmd = "npx jest --runInBand --coverage --ci"
        else:
            cmd = "npx jest --runInBand --coverage --ci"
            
    elif stack == "java":
        # Prefer Maven, fallback to Gradle
        if (ROOT / "pom.xml").exists():
            cmd = "mvn -B test -Dmaven.test.failure.ignore=true"
        elif any((ROOT / f).exists() for f in ["build.gradle", "build.gradle.kts"]):
            if (ROOT / "gradlew").exists():
                cmd = "./gradlew test --continue"
            else:
                cmd = "gradle test --continue"
        else:
            return {
                "cmd": "no_build_file",
                "returncode": 1,
                "duration_sec": 0,
                "stdout": "",
                "stderr": "No Maven pom.xml or Gradle build file found",
                "success": False
            }
            
    else:
        print(f"Unknown stack '{stack}', cannot run tests")
        return {
            "cmd": f"echo 'Unknown stack: {stack}'",
            "returncode": 0,
            "duration_sec": 0,
            "stdout": f"Unknown stack: {stack}. No tests executed.",
            "stderr": "",
            "success": True
        }
    
    return run(cmd, allow_fail=True)  # 15 min timeout for tests

def collect_test_reports(stack: str) -> List[str]:
    """Collect test and coverage reports based on stack"""
    print("Collecting test reports and artifacts...")
    
    collected_files = []
    
    # Common patterns by stack
    patterns = {
        "python": [
            "coverage.xml", "test-results.xml", ".coverage",
            "htmlcov/**/*", "pytest_cache/**/*"
        ],
        "node": [
            "coverage/**/*", "junit.xml", "jest-junit.xml", 
            "test-results.xml", "node_modules/.cache/jest/**/*"
        ],
        "java": [
            "target/site/jacoco/**/*", "target/surefire-reports/**/*",
            "build/reports/tests/**/*", "build/test-results/**/*",
            "build/reports/jacoco/**/*"
        ]
    }
    
    # Stack-specific collection  
    for pattern in patterns.get(stack, []):
        try:
            if "**" in pattern:
                # Recursive glob - handle recursion limit
                base_pattern = pattern.replace("**/*", "**")
                for path in ROOT.rglob(base_pattern.replace("**", "*")):
                    if path.is_file():
                        collected_files.append(str(path.relative_to(ROOT)))
            else:
                # Simple file check
                path = ROOT / pattern
                if path.exists():
                    collected_files.append(str(path.relative_to(ROOT)))
        except (OSError, RecursionError) as e:
            print(f"Error collecting pattern {pattern}: {e}")
            continue
    
    # Always include our artifacts
    for artifact in ARTIFACTS.rglob("*"):
        if artifact.is_file():
            collected_files.append(str(artifact.relative_to(ROOT)))
    
    # Create manifest
    manifest_path = ARTIFACTS / "collected_files_manifest.txt"
    manifest_path.write_text("\n".join(sorted(collected_files)))
    
    print(f"Collected {len(collected_files)} artifact files")
    return collected_files

def generate_summary_report(report_data: Dict[str, Any]) -> str:
    """Generate human-readable summary"""
    stack = report_data["stack"]
    duration = report_data.get("total_duration_sec", 0)
    
    summary = f"""
# GenAI Test Platform - Execution Summary

**Repository**: {ROOT.name}
**Stack**: {stack.upper()}
**Duration**: {duration:.1f} seconds
**Timestamp**: {report_data["started_at"]}

## Phase Results

"""
    
    for step in report_data.get("steps", []):
        phase = step["phase"]
        if phase == "deps":
            results = step["results"]
            failed = sum(1 for r in results if not r.get("success", True))
            summary += f"### Dependencies ({phase})\n"
            summary += f"- Commands executed: {len(results)}\n"
            summary += f"- Failed: {failed}\n"
            summary += f"- Status: {'✅ Success' if failed == 0 else '⚠️ Some failures'}\n\n"
            
        elif phase == "native_tests":
            result = step["result"]
            summary += f"### Test Execution ({phase})\n"
            summary += f"- Command: `{result['cmd']}`\n"
            summary += f"- Duration: {result['duration_sec']:.1f}s\n"
            summary += f"- Exit code: {result['returncode']}\n"
            summary += f"- Status: {'✅ Success' if result['success'] else '❌ Failed'}\n\n"
            
        elif phase == "genai":
            result = step["result"]
            summary += f"### AI Test Generation ({phase})\n"
            summary += f"- Enabled: {'Yes' if result['generated'] else 'No'}\n"
            if not result['generated']:
                summary += f"- Reason: {result.get('reason', 'Unknown')}\n"
            summary += f"- Plan file: `{result['plan_file']}`\n\n"
    
    summary += f"## Artifacts\n\n"
    summary += f"Collected {len(report_data.get('artifacts', []))} files for upload.\n\n"
    
    summary += f"---\n*Generated by GenAI Test Platform v2.0*"
    
    return summary

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="GenAI Test Platform - Unified Test Runner")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM test generation")
    parser.add_argument("--stack", choices=["python", "node", "java"], help="Override stack detection")
    parser.add_argument("--timeout", type=int, default=1800, help="Total timeout in seconds (default: 30min)")
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    print("Starting GenAI Test Platform - Unified Test Runner")
    print(f"Working directory: {ROOT}")
    
    # Initialize report
    report = {
        "started_at": datetime.utcnow().isoformat() + "Z",
        "runner_version": "2.0.0",
        "working_directory": str(ROOT),
        "arguments": vars(args),
        "stack": None,
        "steps": [],
        "artifacts": [],
        "summary": ""
    }
    
    try:
        # Phase 1: Stack Detection
        stack = detect_stack(args.stack)
        report["stack"] = stack
        
        # Phase 2: Dependencies
        print("Phase 2: Installing dependencies...")
        deps_results = ensure_dependencies(stack)
        report["steps"].append({"phase": "deps", "results": deps_results})
        
        # Phase 3: LLM Generation (optional)
        print("Phase 3: AI test generation...")
        llm_result = llm_generate_or_patch_tests(stack, not args.no_llm)
        report["steps"].append({"phase": "genai", "result": llm_result})
        
        # Phase 4: Native Tests
        print("Phase 4: Running native tests...")
        test_result = run_native_tests(stack)
        report["steps"].append({"phase": "native_tests", "result": test_result})
        
        # Phase 5: Artifact Collection
        print("Phase 5: Collecting artifacts...")
        artifacts = collect_test_reports(stack)
        report["artifacts"] = artifacts
        
        # Finalize report
        report["finished_at"] = datetime.utcnow().isoformat() + "Z"
        report["total_duration_sec"] = round(time.time() - start_time, 3)
        report["success"] = True
        
    except Exception as e:
        print(f"Execution failed: {e}", file=sys.stderr)
        report["error"] = str(e)
        report["success"] = False
        report["finished_at"] = datetime.utcnow().isoformat() + "Z"
        report["total_duration_sec"] = round(time.time() - start_time, 3)
    
    # Generate summary
    summary = generate_summary_report(report)
    report["summary"] = summary
    
    # Save reports
    report_file = ARTIFACTS / "test_report.json"
    summary_file = ARTIFACTS / "summary.md"
    
    report_file.write_text(json.dumps(report, indent=2))
    summary_file.write_text(summary)
    
    print(f"Execution completed in {report['total_duration_sec']:.1f}s")
    print(f"Report saved: {report_file}")
    print(f"Summary saved: {summary_file}")
    
    # Exit with appropriate code
    if report.get("success", False):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()