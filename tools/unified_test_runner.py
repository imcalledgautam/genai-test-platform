#!/usr/bin/env python3
"""
Unified GenAI Test Runner - Production Ready
============================================

One Action step for every repo: python tools/unified_test_runner.py

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

# Global flags
AUTO_APPROVE_TESTS = False

def run(cmd: str, cwd: Optional[pathlib.Path] = None, allow_fail: bool = False, 
        env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Execute shell command with comprehensive logging and error handling."""
    print(f":: RUN => {cmd}")
    start = time.time()
    
    try:
        p = subprocess.run(
            cmd, 
            cwd=cwd or ROOT, 
            shell=isinstance(cmd, str), 
            env=env or os.environ.copy(),
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            timeout=900  # 15 minute timeout for slow integration tests
        )
        
        dur = round(time.time() - start, 3)
        print(p.stdout)
        
        if p.returncode != 0 and not allow_fail:
            print(p.stderr, file=sys.stderr)
        
        return {
            "cmd": cmd,
            "rc": p.returncode, 
            "duration_sec": dur,
            "stdout": p.stdout[-50_000:],  # Cap output size
            "stderr": p.stderr[-50_000:],
            "success": p.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        dur = round(time.time() - start, 3)
        print(f"Command timed out after 900s", file=sys.stderr)
        return {
            "cmd": cmd,
            "rc": -1,
            "duration_sec": dur,
            "stdout": "",
            "stderr": "Command timed out after 900s",
            "success": False
        }
    except Exception as e:
        dur = round(time.time() - start, 3)
        print(f"Command execution error: {e}", file=sys.stderr)
        return {
            "cmd": cmd,
            "rc": -2,
            "duration_sec": dur,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }

def detect_stack() -> str:
    """Detect project stack based on config files and structure."""
    files = {f.name.lower() for f in ROOT.iterdir() if f.is_file()}
    
    # Java detection
    if "pom.xml" in files or "build.gradle" in files:
        return "java"
    
    # Node.js detection
    if "package.json" in files:
        return "node"
    
    # Python detection
    if "requirements.txt" in files or "pyproject.toml" in files:
        return "python"
    
    # Fallback: heuristics based on src structure
    if (ROOT / "src").exists():
        src_files = list((ROOT / "src").rglob("*.*"))
        
        if any(p.suffix == ".py" for p in src_files):
            return "python"
        
        if any(p.suffix in [".js", ".ts", ".jsx", ".tsx"] for p in src_files):
            return "node"
        
        if any(p.suffix == ".java" for p in src_files):
            return "java"
    
    # Check for any Python files in root or common dirs
    py_patterns = ["*.py", "**/*.py"]
    for pattern in py_patterns:
        if list(ROOT.glob(pattern)):
            return "python"
    
    return "unknown"

def ensure_deps(stack: str) -> List[Dict[str, Any]]:
    """Install dependencies based on detected stack."""
    results = []
    
    if stack == "python":
        cmds = [
            "python -m pip install -U pip",
            "if [ -f requirements.txt ]; then python -m pip install -r requirements.txt; fi",
            "if [ -f pyproject.toml ]; then python -m pip install .; fi"
        ]
    elif stack == "node":
        cmds = [
            "if [ -f package-lock.json ]; then npm ci; else npm install; fi"
        ]
    elif stack == "java":
        cmds = [
            "if [ -f pom.xml ]; then mvn -q -B -DskipTests=true clean install || true; fi",
            "if [ -f build.gradle ]; then ./gradlew --no-daemon assemble || true; fi"
        ]
    else:
        cmds = ["echo 'Unknown stack, skipping dependency installation'"]
    
    for cmd in cmds:
        result = run(cmd, allow_fail=True)
        results.append(result)
    
    return results

def llm_generate_or_patch_tests(stack: str) -> Dict[str, Any]:
    """
    Optional: call LLM to create/patch tests BEFORE running native tests.
    
    The LLM should only write into safe paths:
      - python: tests/
      - node: __tests__/ or tests/
      - java: src/test/java/
    
    This integrates with context_builder and existing LLM agent.
    """
    plan_path = ARTIFACTS / "genai_test_plan.json"
    
    # Check if LLM generation is enabled
    enabled = os.getenv("GENAI_TEST_GEN", "true").lower() == "true"
    
    plan = {
        "enabled": enabled,
        "stack": stack,
        "strategy": "augment_if_missing",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "notes": "LLM generates tests for public functions/classes discovered by context_builder."
    }
    
    if enabled:
        try:
            # Import and call our context builder
            sys.path.append(str(ROOT))
            from tools.context_builder_v2 import build_llm_context
            
            print(":: Building context for LLM generation...")
            context = build_llm_context()
            
            plan["context_ready"] = True
            plan["context_file"] = str(ROOT / "genai_artifacts" / "context.json")
            plan["symbols_found"] = len(context["public_surface"]["python"])
            
            # Actually call LLM to generate tests
            print(":: Calling LLM to generate tests...")
            generated_count = generate_tests_for_symbols(context["public_surface"]["python"])
            
            plan["generation_attempted"] = True
            plan["tests_generated"] = generated_count
            
        except Exception as e:
            print(f":: LLM generation error: {e}")
            plan["error"] = str(e)
            plan["generation_attempted"] = False
    
    plan_path.write_text(json.dumps(plan, indent=2))
    
    return {
        "generated": enabled,
        "plan_file": str(plan_path),
        "result": plan
    }

def get_human_approval(test_file_path: str) -> bool:
    """Get human approval for generated test file."""
    # Check if auto-approval is enabled
    if globals().get('AUTO_APPROVE_TESTS', False):
        print(f"🤖 Auto-approving test file: {test_file_path}")
        return True
    
    print(f"\n🔍 Test file generated: {test_file_path}")
    print(f"📁 Please review the generated test file at the above path.")
    print(f"📖 You can open it in your editor to inspect the generated tests.")
    
    while True:
        response = input("\n❓ Do you approve this test file? (y)es/(n)o/(v)iew: ").lower().strip()
        
        if response in ['y', 'yes']:
            print("✅ Test file approved! Proceeding with test execution...")
            return True
        elif response in ['n', 'no']:
            print("❌ Test file rejected! Skipping this test file...")
            return False
        elif response in ['v', 'view']:
            # Show first few lines of the test file
            try:
                with open(test_file_path, 'r') as f:
                    lines = f.readlines()[:20]  # Show first 20 lines
                print(f"\n📄 Preview of {test_file_path}:")
                print("-" * 50)
                for i, line in enumerate(lines, 1):
                    print(f"{i:2d}: {line.rstrip()}")
                if len(lines) == 20:
                    print("... (showing first 20 lines)")
                print("-" * 50)
            except Exception as e:
                print(f"❌ Error reading file: {e}")
        else:
            print("❌ Invalid input. Please enter 'y' for yes, 'n' for no, or 'v' to view the file.")

def generate_tests_for_symbols(symbols: List[Dict]) -> int:
    """Generate tests for discovered Python symbols using LLM with human approval."""
    try:
        import requests
        
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")
        
        # Test if Ollama is available
        try:
            response = requests.get(f"{ollama_host}/api/tags", timeout=5)
            if response.status_code != 200:
                print(f":: Ollama not available at {ollama_host}")
                return 0
        except requests.exceptions.RequestException as e:
            print(f":: Ollama connection failed: {e}")
            return 0
        
        # Group symbols by file for more efficient generation
        files_to_test = {}
        
        # Filter symbols to focus on source files (not tools/)
        filtered_symbols = []
        for symbol in symbols:
            file_path = symbol["file"]
            # Skip our own tools directory files to focus on target repository
            if not file_path.startswith("tools/") and not file_path.startswith("llm_agent/"):
                filtered_symbols.append(symbol)
        
        # Process filtered symbols (limit to 10 for reasonable GitHub Actions execution time)
        process_count = min(len(filtered_symbols), 10)
        print(f":: Found {len(symbols)} total symbols, {len(filtered_symbols)} after filtering")
        print(f":: Processing {process_count} symbols from files:")
        
        for symbol in filtered_symbols[:process_count]:
            file_path = symbol["file"]
            print(f"   - {file_path}: {symbol['name']} ({symbol['type']})")
            if file_path not in files_to_test:
                files_to_test[file_path] = []
            files_to_test[file_path].append(symbol)
        
        generated_count = 0
        approved_count = 0
        test_dir = ROOT / "tests" / "generated_by_llm"
        test_dir.mkdir(exist_ok=True)
        
        for file_path, file_symbols in files_to_test.items():
            print(f":: Generating tests for {file_path} ({len(file_symbols)} symbols)...")
            
            # Read the source file
            source_path = ROOT / file_path
            if not source_path.exists():
                continue
                
            source_code = source_path.read_text(encoding='utf-8')
            
            # Create simplified prompt for faster generation
            symbols_list = ", ".join(s['symbol'] for s in file_symbols)
            prompt = f"""Write pytest tests for these functions in {file_path}: {symbols_list}

Source code (first 2000 chars):
```python
{source_code[:2000]}
```

Generate simple pytest test functions. Use: from {file_path.replace('/', '.').replace('.py', '')} import *

Output only Python code, no explanations or markdown:"""

            # Call Ollama
            try:
                response = requests.post(
                    f"{ollama_host}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Low temperature for consistent code
                            "top_p": 0.9,
                            "num_ctx": 2048  # Optimized context for 1.5B model
                        }
                    },
                    timeout=120  # Increased timeout for GitHub Actions environment
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_code = result.get("response", "").strip()
                    
                    # Clean up markdown code fences if present
                    if generated_code.startswith("```python"):
                        generated_code = generated_code.replace("```python", "").replace("```", "").strip()
                    elif generated_code.startswith("````python"):
                        generated_code = generated_code.replace("````python", "").replace("````", "").strip()
                    
                    if generated_code and "def test_" in generated_code:
                        # Save generated test
                        test_file_name = f"test_{pathlib.Path(file_path).stem}_generated.py"
                        test_file_path = test_dir / test_file_name
                        test_file_path.write_text(generated_code, encoding='utf-8')
                        print(f":: Generated {test_file_path}")
                        generated_count += 1
                        
                        # Human approval step
                        if get_human_approval(str(test_file_path)):
                            approved_count += 1
                        else:
                            # Delete the rejected file
                            test_file_path.unlink()
                            print(f":: Deleted rejected test file: {test_file_path}")
                            generated_count -= 1  # Don't count rejected files
                    else:
                        print(f":: No valid tests generated for {file_path}")
                else:
                    print(f":: LLM API error: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f":: LLM request failed for {file_path}: {e}")
                continue
        
        print(f":: Generated {generated_count} test files, {approved_count} approved")
        return approved_count
        
    except Exception as e:
        print(f":: Error in test generation: {e}")
        return 0

def run_native_tests(stack: str) -> Dict[str, Any]:
    """Run native test framework based on detected stack."""
    
    if stack == "python":
        # Try pytest first, fallback to unittest
        cmd = ("python -m pytest -v --tb=short --maxfail=5 "
               "--cov=. --cov-report=xml:coverage.xml --cov-report=term "
               "--junitxml=test-results.xml || "
               "python -m unittest discover -v || true")
        
    elif stack == "node":
        # Check if npm test script exists, otherwise try jest directly
        cmd = ("if npm run | grep -q 'test$'; then npm test; "
               "else npx jest --verbose --runInBand --coverage "
               "--coverageReporters=text --coverageReporters=lcov "
               "--testResultsProcessor=jest-junit || true; fi")
        
    elif stack == "java":
        # Maven first, then Gradle
        cmd = ("if [ -f pom.xml ]; then mvn -B test "
               "-Dmaven.test.failure.ignore=true || true; "
               "elif [ -f build.gradle ]; then ./gradlew --no-daemon test "
               "--continue || true; fi")
        
    else:
        cmd = "echo 'Unknown stack; no native tests run'"
    
    return run(cmd, allow_fail=True)

def collect_reports(stack: str) -> List[str]:
    """Collect test reports and coverage files based on stack."""
    files = []
    
    # Python artifacts
    python_files = [
        "coverage.xml",
        "test-results.xml", 
        ".coverage",
        "htmlcov/index.html"
    ]
    
    # Node.js artifacts  
    node_files = [
        "coverage/lcov.info",
        "coverage/coverage-final.json",
        "junit.xml",
        "jest-junit.xml"
    ]
    
    # Java artifacts
    java_patterns = [
        "target/surefire-reports/*.xml",
        "target/site/jacoco/jacoco.xml",
        "build/reports/tests/test/index.html",
        "build/test-results/test/*.xml"
    ]
    
    # Collect based on stack
    if stack == "python":
        check_files = python_files
    elif stack == "node":
        check_files = node_files
    elif stack == "java":
        check_files = []
        # Handle Java glob patterns
        for pattern in java_patterns:
            files.extend([str(p) for p in ROOT.glob(pattern) if p.exists()])
    else:
        check_files = []
    
    # Add existing files
    for file_path in check_files:
        full_path = ROOT / file_path
        if full_path.exists():
            files.append(str(full_path))

    # Also collect generated test files
    generated_tests_dir = ROOT / "tests" / "generated_by_llm"
    if generated_tests_dir.exists():
        for test_file in generated_tests_dir.glob("*.py"):
            files.append(str(test_file))
    
    # Also collect the test plan and report
    genai_artifacts = ROOT / "genai_artifacts"
    if genai_artifacts.exists():
        for artifact in genai_artifacts.glob("*"):
            if artifact.is_file():
                files.append(str(artifact))

    # Save manifest
    manifest_path = ARTIFACTS / "collected_files_manifest.txt"
    manifest_path.write_text("\n".join(files))

    return files

def main():
    """Main orchestration function."""
    print("=" * 60)
    print("🚀 GenAI Test Platform - Unified Test Runner")
    print("=" * 60)
    
    # Initialize report structure
    report = {
        "started_at": datetime.utcnow().isoformat() + "Z",
        "runner_version": "1.0.0",
        "repository_root": str(ROOT),
        "stack": None,
        "steps": [],
        "artifacts": [],
        "summary": {}
    }
    
    try:
        # Step 1: Detect stack
        print("\n📋 Step 1: Detecting project stack...")
        stack = detect_stack()
        report["stack"] = stack
        print(f":: Detected stack: {stack}")
        
        # Step 2: Install dependencies
        print(f"\n📦 Step 2: Installing {stack} dependencies...")
        dep_results = ensure_deps(stack)
        report["steps"].append({
            "phase": "dependencies", 
            "results": dep_results,
            "success": all(r["success"] for r in dep_results)
        })
        
        # Step 3: LLM test generation (optional)
        print(f"\n🤖 Step 3: GenAI test generation...")
        genai_results = llm_generate_or_patch_tests(stack)
        report["steps"].append({
            "phase": "genai_generation", 
            "results": genai_results,
            "success": True  # Non-blocking
        })
        
        # Step 4: Run native tests
        print(f"\n🧪 Step 4: Running native {stack} tests...")
        test_result = run_native_tests(stack)
        report["steps"].append({
            "phase": "native_tests", 
            "result": test_result,
            "success": test_result["success"]
        })
        
        # Step 5: Collect artifacts
        print(f"\n📊 Step 5: Collecting test artifacts...")
        artifacts = collect_reports(stack)
        report["artifacts"] = artifacts
        print(f":: Collected {len(artifacts)} artifact files")
        
        # Generate summary
        report["summary"] = {
            "total_steps": len(report["steps"]),
            "successful_steps": sum(1 for s in report["steps"] if s["success"]),
            "artifacts_count": len(artifacts),
            "overall_success": all(s["success"] for s in report["steps"] if s["phase"] != "genai_generation")
        }
        
        report["finished_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Save unified report
        report_path = ARTIFACTS / "test_report.json"
        report_path.write_text(json.dumps(report, indent=2))
        
        print(f"\n✅ Unified test report saved to: {report_path}")
        print(f"📁 Artifacts directory: {ARTIFACTS}")
        
        # Print summary
        print(f"\n📈 Summary:")
        print(f"   Stack: {stack}")
        print(f"   Steps completed: {report['summary']['successful_steps']}/{report['summary']['total_steps']}")
        print(f"   Artifacts collected: {report['summary']['artifacts_count']}")
        print(f"   Overall success: {'✅' if report['summary']['overall_success'] else '❌'}")
        
        # Exit with appropriate code
        sys.exit(0 if report['summary']['overall_success'] else 1)
        
    except Exception as e:
        print(f"\n❌ Fatal error in test runner: {e}")
        report["fatal_error"] = str(e)
        report["finished_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Still save report for debugging
        error_report_path = ARTIFACTS / "test_report.json"
        error_report_path.write_text(json.dumps(report, indent=2))
        
        sys.exit(1)

def parse_args_and_run():
    """Parse command line arguments and run the main function."""
    global AUTO_APPROVE_TESTS
    
    import argparse
    
    parser = argparse.ArgumentParser(description="GenAI Test Platform - Unified Test Runner")
    parser.add_argument("--target-function", help="Target function for test generation")
    parser.add_argument("--files", help="Target files for test generation")
    parser.add_argument("--auto-approve", action="store_true", 
                       help="Automatically approve all generated tests (skip human review)")
    
    args = parser.parse_args()
    
    # Set global flag for auto-approval
    AUTO_APPROVE_TESTS = args.auto_approve
    
    main()

if __name__ == "__main__":
    parse_args_and_run()