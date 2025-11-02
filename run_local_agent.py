#!/usr/bin/env python3
"""
Local test runner for the LLM agent.
This script builds the context bundle and generates tests locally.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run_command(cmd, description):
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, cwd=ROOT, check=True, text=True, capture_output=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    print("🚀 GenAI Test Platform - Local LLM Agent Runner")
    print("=" * 50)
    
    # Step 1: Build context bundle
    if not run_command([sys.executable, "llm_agent/context_builder.py"], 
                      "Building context bundle"):
        return 1
    
    # Step 2: Generate tests (requires Ollama)
    print("\n⚠️  About to call Ollama. Make sure:")
    print("   - Ollama is running (ollama serve)")
    print("   - qwen2.5-coder model is available (ollama pull qwen2.5-coder:7b)")
    
    response = input("\nContinue with test generation? (y/N): ").strip().lower()
    if response != 'y':
        print("Stopping before LLM call. Context bundle is ready in ci_artifacts/")
        return 0
    
    if not run_command([sys.executable, "llm_agent/generate_tests.py"],
                      "Generating tests with LLM"):
        return 1
    
    print("\n🎉 All steps completed successfully!")
    print("📁 Check tests/generated/ for new test files")
    return 0

if __name__ == "__main__":
    sys.exit(main())