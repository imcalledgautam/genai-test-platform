import subprocess, sys, pathlib, os

ROOT = pathlib.Path(__file__).resolve().parents[1]

def run_pytest():
    tests_dir = ROOT / "tests" / "generated"
    if not tests_dir.exists():
        print("❌  No generated tests found.")
        sys.exit(1)

    print("🧪  Running pytest with coverage...")
    
    # Set up environment with proper Python path
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT)
    
    cmd = [
        "coverage", "run", "--source=code", "-m", "pytest", str(tests_dir),
        "--maxfail=1", "--disable-warnings", "-q"
    ]
    result = subprocess.run(cmd, env=env, check=False)

    print("\n📊  Coverage Report:")
    subprocess.run(["coverage", "report", "-m"], env=env, check=False)
    subprocess.run(["coverage", "xml"], env=env, check=False)   # produce coverage.xml for CI
    print("✅  Test run complete.")
    
    return result.returncode

if __name__ == "__main__":
    exit_code = run_pytest()
    sys.exit(exit_code)