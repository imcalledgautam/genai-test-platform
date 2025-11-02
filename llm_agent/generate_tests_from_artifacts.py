"""
Artifact-based test generator for GitHub Actions workflow integration.
This script can work with artifacts downloaded from GitHub Actions.
"""

import os, json, re, requests, datetime, pathlib, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "downloaded_artifacts"
BUNDLE_PATHS = [
    ROOT / "ci_artifacts" / "context_bundle.json",  # Local build
    ARTIFACTS_DIR / "context-bundle" / "context_bundle.json",  # Downloaded from CI
    ARTIFACTS_DIR / "context_bundle.json"  # Direct download
]
OUT_DIR = ROOT / "tests" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

def find_context_bundle():
    """Find context bundle from various possible locations."""
    for path in BUNDLE_PATHS:
        if path.exists():
            print(f"📁 Found context bundle at: {path}")
            return path
    
    print("❌ No context bundle found. Options:")
    print("1. Run locally: python llm_agent/context_builder.py")
    print("2. Download from GitHub Actions artifacts")
    print("3. Extract artifacts to downloaded_artifacts/ folder")
    return None

def load_bundle():
    bundle_path = find_context_bundle()
    if not bundle_path:
        raise SystemExit("Context bundle not found")
    return json.loads(bundle_path.read_text(encoding="utf-8"))

def extract_github_artifact(artifact_zip_path):
    """Extract downloaded GitHub artifact zip file."""
    artifact_path = Path(artifact_zip_path)
    if not artifact_path.exists():
        raise SystemExit(f"Artifact zip not found: {artifact_path}")
    
    extract_dir = ARTIFACTS_DIR / artifact_path.stem
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(artifact_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    print(f"📦 Extracted artifact to: {extract_dir}")
    return extract_dir

def build_prompt(bundle: dict) -> str:
    prompt_template = (ROOT / "llm_agent" / "prompt_template.txt").read_text(encoding="utf-8")
    parts = [prompt_template, "\n\n=== CODE ANALYSIS FOR TEST GENERATION ===\n"]
    
    if not bundle["files"]:
        parts.append("⚠️  No changed files detected. Generating tests for all Python files in the repository.")
    
    for f in bundle["files"]:
        parts.append(f"\n--- ANALYZING FILE: {f['path']} ---")
        
        # Add diff context if available
        if f.get("unified_diff"):
            parts.append(f"\nCHANGES MADE (Git Diff):\n```diff\n{f['unified_diff']}\n```")
        
        # Add full source code with analysis instructions
        parts.append(f"\nCOMPLETE SOURCE CODE TO ANALYZE:")
        parts.append("```python")
        parts.append((f.get("full_text") or "")[:20000])
        parts.append("```")
        
        # Add automated code analysis
        parts.append(f"\nAUTOMATED CODE ANALYSIS FOR {f['path']}:")
        try:
            from llm_agent.code_analyzer import analyze_python_file, generate_test_guidance
            file_path = ROOT / f['path']
            if file_path.exists():
                analysis = analyze_python_file(str(file_path))
                guidance = generate_test_guidance(analysis)
                parts.append(guidance)
            else:
                parts.append("⚠️ Could not analyze file - file not found for detailed analysis")
        except Exception as e:
            parts.append(f"⚠️ Code analysis failed: {e}")
        
        parts.append(f"\nIMPORT INSTRUCTION:")
        parts.append("Use: from " + f['path'].replace('/', '.').replace('.py', '') + " import ...")

    # Add repository context
    ctx = bundle.get("context", {})
    parts.append("\n=== REPOSITORY CONTEXT ===")
    
    if ctx.get("readme"):
        parts.append("\nProject Overview (README excerpt):")
        parts.append(ctx["readme"][:1500])
    
    if ctx.get("requirements"):
        parts.append("\nDependencies (requirements.txt):")
        parts.append(ctx["requirements"][:800])
    
    if ctx.get("sample_data"):
        parts.append("\nSample Data (for context):")
        parts.append(json.dumps(ctx["sample_data"], indent=2)[:1500])

    parts.append("\n" + "="*60)
    parts.append("GENERATE TESTS NOW:")
    parts.append("- Read the code carefully and understand what it actually does")
    parts.append("- Only test behaviors that are explicitly implemented")
    parts.append("- Use proper import paths for the test file")
    parts.append("- Follow the OUTPUT FORMAT exactly")
    parts.append("="*60)
    
    return "\n".join(parts)

def call_ollama(prompt: str) -> str:
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    
    print(f"🤖 Calling Ollama at {OLLAMA_HOST} with model {MODEL}")
    print(f"📝 Prompt length: {len(prompt)} characters")
    
    try:
        r = requests.post(url, json=payload, timeout=600)
        r.raise_for_status()
        return r.json()["response"]
    except requests.exceptions.ConnectionError:
        raise SystemExit(f"❌ Cannot connect to Ollama at {OLLAMA_HOST}. Make sure Ollama is running:\n   ollama serve")
    except requests.exceptions.RequestException as e:
        raise SystemExit(f"❌ Ollama request failed: {e}")

def extract_code_block(text: str) -> str:
    # find ```python ... ``` block
    m = re.search(r"```python\s*(.*?)```", text, flags=re.S | re.I)
    if m:
        return m.group(1).strip()
    # fallback: return whole text if no fence
    return text.strip()

def write_test_file(code: str) -> Path:
    stamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = OUT_DIR / f"test_generated_{stamp}.py"
    path.write_text(code, encoding="utf-8")
    return path

def main():
    print("🚀 GenAI Test Platform - Artifact-based Test Generator")
    print("=" * 55)
    
    # Check for command line artifact extraction
    import sys
    if len(sys.argv) > 1:
        artifact_zip = sys.argv[1]
        print(f"📦 Extracting artifact: {artifact_zip}")
        extract_github_artifact(artifact_zip)
    
    bundle = load_bundle()
    
    print(f"📊 Context bundle contains:")
    print(f"   - {len(bundle['files'])} changed files")
    print(f"   - README: {'✅' if bundle['context'].get('readme') else '❌'}")
    print(f"   - Requirements: {'✅' if bundle['context'].get('requirements') else '❌'}")
    print(f"   - Sample data: {len(bundle['context'].get('sample_data', {}))} files")
    
    prompt = build_prompt(bundle)
    resp = call_ollama(prompt)
    code = extract_code_block(resp)
    out = write_test_file(code)
    
    print(f"✅ Tests written to: {out}")
    print(f"📁 Run tests with: pytest {out}")

if __name__ == "__main__":
    main()