"""
Enhanced context builder that can work with GitHub Actions environment
and the changed-files artifact produced by the workflow.
"""

import os, re, json, subprocess, textwrap, pathlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "ci_artifacts"
OUT_DIR.mkdir(exist_ok=True, parents=True)

def run(cmd, cwd=None):
    return subprocess.check_output(cmd, cwd=cwd or ROOT, text=True, shell=True)

def load_changed_files_from_ci():
    """Load changed files from GitHub Actions artifact or local file."""
    # Check for GitHub Actions environment
    if os.getenv("GITHUB_ACTIONS"):
        # In CI, look for the changed_files.txt from previous step
        changed_files_path = ROOT / "changed_files.txt"
        if changed_files_path.exists():
            files = changed_files_path.read_text().strip().splitlines()
            return [f for f in files if f.strip() and f.endswith('.py')]
    
    # Check for downloaded artifacts
    artifact_locations = [
        ROOT / "downloaded_artifacts" / "changed-files" / "changed_files.txt",
        ROOT / "changed_files.txt"
    ]
    
    for location in artifact_locations:
        if location.exists():
            files = location.read_text().strip().splitlines()
            return [f for f in files if f.strip() and f.endswith('.py')]
    
    return None

def list_changed_files():
    """Get changed files from various sources with fallback logic."""
    # First, try to load from CI artifacts or GitHub Actions
    ci_files = load_changed_files_from_ci()
    if ci_files:
        print(f"📋 Loaded {len(ci_files)} changed files from CI/artifacts")
        return ci_files
    
    # Fallback to git diff detection
    try:
        diff_output = run("git diff --name-only HEAD~1 HEAD").strip()
        print(f"🔍 Git diff output: '{diff_output}'")
        if diff_output:
            diff_list = diff_output.splitlines()
            py_files = [f for f in diff_list if f.endswith('.py')]
            print(f"📋 Found {len(py_files)} changed Python files via git diff")
            return py_files
        else:
            print("📋 Git diff returned empty - no changes detected")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git diff failed: {e}")
        pass
    
    # Last resort: include all application Python files
    py_files = []
    for p in ROOT.rglob("*.py"):
        if p.is_file():
            rel_path = str(p.relative_to(ROOT)).replace("\\", "/")  # Normalize path separators
            py_files.append(rel_path)
    
    print(f"🔍 Found {len(py_files)} total Python files: {py_files}")
    
    # Filter out our own llm_agent files and tests to focus on application code
    app_files = [f for f in py_files if not f.startswith("llm_agent") and not f.startswith("tests") and not f.startswith(".")]
    
    print(f"🎯 Filtered to {len(app_files)} application files: {app_files}")
    
    if app_files:
        print(f"📋 No changes detected, including {len(app_files)} application Python files")
        return app_files
    
    print("⚠️  No Python files found to analyze")
    return []

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
        # Skip standard library and common third-party modules
        if top not in ['os', 'sys', 'json', 'datetime', 'pathlib', 'requests', 
                      'pandas', 'numpy', 'matplotlib', 'seaborn', 'streamlit']:
            mods.add(top)
    return mods

def find_local_module_file(mod_name):
    """Find local module files with better heuristics."""
    candidates = [
        ROOT / f"{mod_name}.py",
        ROOT / "code" / f"{mod_name}.py",
        ROOT / "app" / f"{mod_name}.py",
        ROOT / "src" / f"{mod_name}.py",
        ROOT / "lib" / f"{mod_name}.py",
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

def gather_context():
    """Enhanced context gathering with CI integration."""
    changed = list_changed_files()
    files_payload = []
    deps_seen = set()

    # Process changed files
    for f in changed:
        print(f"📄 Processing: {f}")
        src = read_file(f)
        diff = get_unified_diff(f)
        files_payload.append({
            "path": f,
            "full_text": src,
            "unified_diff": diff
        })
        
        # Shallow dependency harvest
        for mod in direct_imports(src):
            mod_file = find_local_module_file(mod)
            if mod_file and mod_file.exists():
                key = str(mod_file.relative_to(ROOT))
                if key not in deps_seen and key not in [x["path"] for x in files_payload]:
                    deps_seen.add(key)
                    print(f"📦 Adding dependency: {key}")
                    files_payload.append({
                        "path": key,
                        "full_text": read_file(key),
                        "unified_diff": ""  # not changed, but context
                    })

    # Gather repository context
    context = {
        "readme": small_read("README.md"),
        "requirements": small_read("requirements.txt") or small_read("requirements/requirements.txt"),
        "sample_data": {}
    }

    # Include sample data
    data_patterns = ["data/*.csv", "data/*.json", "*.csv", "*.json"]
    for pattern in data_patterns:
        for data_file in ROOT.glob(pattern):
            if data_file.is_file() and data_file.stat().st_size < 50000:  # < 50KB
                rel_path = str(data_file.relative_to(ROOT))
                context["sample_data"][rel_path] = small_read(rel_path)

    # Add CI environment info if available
    if os.getenv("GITHUB_ACTIONS"):
        context["ci_info"] = {
            "github_actions": True,
            "ref": os.getenv("GITHUB_REF", ""),
            "sha": os.getenv("GITHUB_SHA", ""),
            "actor": os.getenv("GITHUB_ACTOR", ""),
            "event_name": os.getenv("GITHUB_EVENT_NAME", "")
        }

    bundle = {
        "files": files_payload, 
        "context": context,
        "metadata": {
            "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
            "total_files": len(files_payload),
            "changed_files": len([f for f in files_payload if f.get("unified_diff")]),
            "dependency_files": len([f for f in files_payload if not f.get("unified_diff")])
        }
    }
    
    output_path = OUT_DIR / "context_bundle.json"
    output_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    
    print(f"✅ Context bundle written to: {output_path}")
    print(f"📊 Bundle contains:")
    print(f"   - {bundle['metadata']['total_files']} total files")
    print(f"   - {bundle['metadata']['changed_files']} changed files")
    print(f"   - {bundle['metadata']['dependency_files']} dependency files")
    print(f"   - {len(context['sample_data'])} sample data files")

if __name__ == "__main__":
    gather_context()