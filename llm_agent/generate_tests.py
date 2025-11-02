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

MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
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


def validate_python(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except Exception:
        return False


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
    while attempts < 3:
        resp = call_ollama_once(prompt if attempts == 0 else (
            prompt + "\n\nThe previous output failed to parse. Fix syntax/imports and resend the corrected file."))
        m = re.search(r"```python(.*?)```", resp, flags=re.S | re.I)
        block = m.group(1).strip() if m else resp.strip()
        filename, code = extract_filename_and_code(block)

        if enforce_safe_imports(code) and validate_python(code):
            out_path = ROOT / filename
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(code, encoding="utf-8")
            print(f"✅ wrote {out_path}")
            return out_path

        attempts += 1
        last_text = resp

    fallback = ROOT / f"tests/generated/__invalid_{Path(module_path).stem}.txt"
    fallback.write_text(last_text, encoding="utf-8")
    print(f"⚠️ saved invalid output to {fallback}")
    return None


if __name__ == "__main__":
    bundle = load_bundle()
    changed_modules = [f["path"] for f in bundle["files"] if f["path"].endswith(".py")]
    changed_modules = [p for p in changed_modules if any(f["path"] == p and f.get("unified_diff") for f in bundle["files"])]
    if not changed_modules:
        print("ℹ️ No changed Python modules detected with diffs.")
    for mod in changed_modules:
        generate_for_module(bundle, mod)