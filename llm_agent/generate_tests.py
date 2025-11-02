import os
import json
import re
import requests
import ast
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "ci_artifacts" / "context_bundle.json"
OUT_DIR = ROOT / "tests" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")  # Smaller model for CI
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
PROMPT_TEMPLATE = (ROOT / "llm_agent" / "prompt_template.txt").read_text(encoding="utf-8")


def load_bundle():
    if not BUNDLE.exists():
        raise SystemExit(f"Context bundle not found: {BUNDLE}")
    return json.loads(BUNDLE.read_text(encoding="utf-8"))


def build_prompt_for_module(bundle, module_path):
    base = PROMPT_TEMPLATE
    files = bundle["files"]
    ctx = bundle.get("context", {})
    targets = bundle.get("targets", {})
    chosen = [f for f in files if f["path"] == module_path]
    if not chosen:
        return None
    f = chosen[0]

    parts = [base, "\n\n=== PRIMARY TARGET MODULE ===\n",
             f"PATH: {f['path']}\n",
             "UNIFIED DIFF:\n```diff\n" + (f.get("unified_diff") or "") + "\n```\n",
             "FULL TEXT:\n```python\n" + (f.get("full_text") or "")[:20000] + "\n```"]

    parts.append("\n=== CONTEXT MODULES (helpers/imports) ===\n")
    for h in files:
        if h["path"] != f["path"] and h.get("full_text"):
            parts.append(f"\n# {h['path']}\n```python\n{h['full_text'][:12000]}\n```")

    tinfo = targets.get(f['path'], {})
    parts.append("\n=== TARGETS ===\n")
    parts.append(json.dumps(tinfo, indent=2))

    # automated code analysis guidance (structured)
    try:
        from llm_agent.code_analyzer import analyze_python_file, generate_test_guidance
        guidance = generate_test_guidance(analyze_python_file(str(ROOT / f['path'])))
        parts.append("\n=== AUTOMATED CODE ANALYSIS GUIDANCE ===\n")
        parts.append(guidance)
    except Exception:
        parts.append("\n⚠️ Could not include automated code analysis guidance")

    if ctx.get("readme"):
        parts.append("\nREADME (excerpt):\n" + ctx["readme"][:1200])
    if ctx.get("requirements"):
        parts.append("\nrequirements.txt:\n" + ctx["requirements"][:800])

    parts.append("\n\nGenerate the pytest file now as per OUTPUT FORMAT.")
    return "\n".join(parts)


def extract_filename_and_code(block_text):
    lines = block_text.strip().splitlines()
    if not lines:
        name = f"tests/generated/test_generated_{int(time.time())}.py"
        return name, block_text
    hdr = lines[0]
    if "filename:" not in hdr.lower():
        name = f"tests/generated/test_generated_{int(time.time())}.py"
        return name, "\n".join(lines)
    m = re.search(r"filename:\s*(.+\.py)", hdr, flags=re.I)
    name = m.group(1).strip() if m else f"tests/generated/test_generated_{int(time.time())}.py"
    code = "\n".join(lines[1:])
    return name, code


def validate_python(code: str) -> tuple[bool, str]:
    """Validate Python code and return (is_valid, error_message)"""
    try:
        ast.parse(code)
        # Additional checks
        if not code.strip():
            return False, "Empty code block"
        if "import pytest" not in code:
            return False, "Missing pytest import"
        if not any(line.strip().startswith("def test_") for line in code.split('\n')):
            return False, "No test functions found (must start with 'def test_')"
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Parse error: {e}"


def enforce_safe_imports(code: str) -> bool:
    bad = ["subprocess", "os.system", "requests.", "httpx.", "selenium", "playwright"]
    return not any(b in code for b in bad)


def call_ollama_once(prompt: str) -> str:
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    r = requests.post(url, json=payload, timeout=600)
    r.raise_for_status()
    return r.json().get("response", "")


def generate_for_module(bundle, module_path):
    prompt = build_prompt_for_module(bundle, module_path)
    if not prompt:
        return None

    attempts = 0
    last_text = ""
    last_error = ""
    
    while attempts < 3:
        # Build retry prompt with specific error feedback
        if attempts == 0:
            current_prompt = prompt
        else:
            retry_guidance = f"\n\nPREVIOUS ATTEMPT FAILED: {last_error}\n"
            retry_guidance += "REQUIREMENTS FOR RETRY:\n"
            retry_guidance += "- Must include 'import pytest' at the top\n"
            retry_guidance += "- All functions must start with 'def test_'\n" 
            retry_guidance += "- Fix any syntax errors\n"
            retry_guidance += "- Use proper imports (no network/subprocess calls)\n"
            retry_guidance += "- Include pytest.raises for error cases\n"
            retry_guidance += "Please generate the corrected test file:"
            current_prompt = prompt + retry_guidance

        print(f"🔄 Attempt {attempts + 1}/3 for {module_path}")
        resp = call_ollama_once(current_prompt)
        
        # Extract code block
        m = re.search(r"```python(.*?)```", resp, flags=re.S | re.I)
        block = m.group(1).strip() if m else resp.strip()
        filename, code = extract_filename_and_code(block)

        # Validate safety and syntax
        if not enforce_safe_imports(code):
            last_error = "Code contains unsafe imports (subprocess, requests, etc.)"
            attempts += 1
            last_text = resp
            continue
            
        is_valid, error_msg = validate_python(code)
        if is_valid:
            out_path = ROOT / filename
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(code, encoding="utf-8")
            print(f"✅ Generated {out_path}")
            
            # Quick syntax check by importing
            try:
                import tempfile
                import sys
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                    tmp.write(code)
                    tmp.flush()
                    
                # Test import (don't actually import to avoid side effects)
                print(f"✅ Syntax validated for {filename}")
                return out_path
            except Exception as e:
                print(f"⚠️ Import test failed: {e}")
                last_error = f"Import validation failed: {e}"
        else:
            last_error = error_msg
            
        attempts += 1
        last_text = resp
        print(f"❌ Attempt {attempts}/3 failed: {last_error}")

    # All attempts failed - save for debugging
    fallback = ROOT / f"tests/generated/__invalid_{Path(module_path).stem}_{int(time.time())}.txt"
    fallback.write_text(f"FAILED AFTER 3 ATTEMPTS\nLast error: {last_error}\n\nLast response:\n{last_text}", encoding="utf-8")
    print(f"❌ Failed to generate valid tests for {module_path}. Debug info saved to {fallback}")
    return None


if __name__ == "__main__":
    bundle = load_bundle()
    changed_modules = [f["path"] for f in bundle["files"] if f["path"].endswith(".py")]
    changed_modules = [p for p in changed_modules if any(f["path"] == p and f.get("unified_diff") for f in bundle["files"])]
    if not changed_modules:
        print("ℹ️ No changed Python modules detected with diffs.")
    for mod in changed_modules:
        generate_for_module(bundle, mod)