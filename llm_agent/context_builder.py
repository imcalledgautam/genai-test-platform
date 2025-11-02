import os, re, json, subprocess, textwrap, pathlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "ci_artifacts"
OUT_DIR.mkdir(exist_ok=True, parents=True)

def run(cmd, cwd=None):
    return subprocess.check_output(cmd, cwd=cwd or ROOT, text=True, shell=True)

def list_changed_files():
    # if first commit on CI you already handled; locally we fallback safely
    try:
        diff_list = run("git diff --name-only HEAD~1 HEAD").strip().splitlines()
        if not diff_list:
            # possibly no previous commit or nothing changed; include key .py files for demo
            py_files = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*.py") if p.is_file()]
            # Filter out our own llm_agent files to avoid recursion and focus on application code
            return [f for f in py_files if not f.startswith("llm_agent") and not f.startswith("tests")]
        return diff_list
    except subprocess.CalledProcessError:
        py_files = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*.py") if p.is_file()]
        # Filter out our own llm_agent files to avoid recursion and focus on application code
        return [f for f in py_files if not f.startswith("llm_agent") and not f.startswith("tests")]

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
        mods.add(top)
    return mods

def find_local_module_file(mod_name):
    # simple heuristics: <mod>.py under repo root or under code/app folders
    candidates = [
        ROOT / f"{mod_name}.py",
        ROOT / "code" / f"{mod_name}.py",
        ROOT / "app" / f"{mod_name}.py",
        ROOT / "src" / f"{mod_name}.py",
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
    changed = list_changed_files()
    changed = [f for f in changed if f.endswith(".py")]
    files_payload = []

    deps_seen = set()

    for f in changed:
        src = read_file(f)
        diff = get_unified_diff(f)
        files_payload.append({
            "path": f,
            "full_text": src,
            "unified_diff": diff
        })
        # shallow dependency harvest
        for mod in direct_imports(src):
            mod_file = find_local_module_file(mod)
            if mod_file and mod_file.exists():
                key = str(mod_file.relative_to(ROOT))
                if key not in deps_seen and key not in [x["path"] for x in files_payload]:
                    deps_seen.add(key)
                    files_payload.append({
                        "path": key,
                        "full_text": read_file(key),
                        "unified_diff": ""  # not changed, but context
                    })

    context = {
        "readme": small_read("README.md"),
        "requirements": small_read("requirements.txt") or small_read("requirements/requirements.txt"),
        "sample_data": {}
    }

    # include tiny sample rows from common data files if present
    for candidate in ["data/transactions.csv", "data/sample.json"]:
        p = ROOT / candidate
        if p.exists():
            context["sample_data"][candidate] = small_read(candidate)

    # simple target harvesting: which public functions and which local dependents are impacted
    import ast
    from pathlib import Path as _Path

    def public_functions(py_src):
        try:
            tree = ast.parse(py_src)
        except Exception:
            return []
        out = []
        for n in tree.body:
            if isinstance(n, ast.FunctionDef) and not n.name.startswith("_"):
                out.append(n.name)
        return out

    def harvest_targets(files_payload):
        # returns mapping {path: {"functions": [...], "dependents": [...]}}
        module_funcs = {}
        for f in files_payload:
            if f["path"].endswith(".py") and f.get("full_text"):
                module_funcs[f["path"]] = set(public_functions(f["full_text"]))

        dependents = {p: set() for p in module_funcs}
        for f in files_payload:
            txt = f.get("full_text") or ""
            for other in module_funcs:
                if other == f["path"]:
                    continue
                top = _Path(other).stem
                if f"import {top}" in txt or f"from {top} " in txt:
                    dependents[other].add(f["path"])

        return {
            p: {
                "functions": sorted(list(funcs)),
                "dependents": sorted(list(dependents[p]))
            } for p, funcs in module_funcs.items()
        }

    targets = harvest_targets(files_payload)

    bundle = {"files": files_payload, "context": context, "targets": targets}
    (OUT_DIR / "context_bundle.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"✅ wrote {OUT_DIR/'context_bundle.json'} with {len(files_payload)} files and {len(targets)} targets")

if __name__ == "__main__":
    gather_context()