"""
Complete workflow for downloading GitHub Actions artifacts and generating tests.
This script handles the entire pipeline from artifact download to test generation.
"""

import os
import sys
import json
import zipfile
import requests
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "downloaded_artifacts"

def download_github_artifact(repo_owner, repo_name, run_id, artifact_name, token=None):
    """Download artifact from GitHub Actions using GitHub API."""
    if not token:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise SystemExit("❌ GITHUB_TOKEN environment variable required for artifact download")
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get artifacts for the run
    artifacts_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{run_id}/artifacts"
    print(f"🔍 Fetching artifacts from: {artifacts_url}")
    
    response = requests.get(artifacts_url, headers=headers)
    response.raise_for_status()
    
    artifacts = response.json()["artifacts"]
    
    # Find the specific artifact
    target_artifact = None
    for artifact in artifacts:
        if artifact["name"] == artifact_name:
            target_artifact = artifact
            break
    
    if not target_artifact:
        available = [a["name"] for a in artifacts]
        raise SystemExit(f"❌ Artifact '{artifact_name}' not found. Available: {available}")
    
    # Download the artifact
    download_url = target_artifact["archive_download_url"]
    print(f"⬇️  Downloading artifact: {artifact_name}")
    
    download_response = requests.get(download_url, headers=headers)
    download_response.raise_for_status()
    
    # Save and extract
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    artifact_zip = ARTIFACTS_DIR / f"{artifact_name}.zip"
    artifact_zip.write_bytes(download_response.content)
    
    # Extract
    extract_dir = ARTIFACTS_DIR / artifact_name
    extract_dir.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(artifact_zip, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    print(f"📦 Extracted to: {extract_dir}")
    return extract_dir

def run_enhanced_context_builder():
    """Run the enhanced context builder."""
    print("🔧 Building enhanced context bundle...")
    result = subprocess.run([
        sys.executable, 
        str(ROOT / "llm_agent" / "enhanced_context_builder.py")
    ], cwd=ROOT)
    
    if result.returncode != 0:
        raise SystemExit("❌ Context builder failed")
    
    return ROOT / "ci_artifacts" / "context_bundle.json"

def run_test_generator():
    """Run the test generator."""
    print("🤖 Generating tests with LLM...")
    result = subprocess.run([
        sys.executable,
        str(ROOT / "llm_agent" / "generate_tests_from_artifacts.py")
    ], cwd=ROOT)
    
    if result.returncode != 0:
        raise SystemExit("❌ Test generator failed")

def main():
    print("🚀 GenAI Test Platform - Complete Workflow")
    print("=" * 50)
    
    import argparse
    parser = argparse.ArgumentParser(description="Download GitHub artifacts and generate tests")
    parser.add_argument("--repo", help="Repository in format owner/name")
    parser.add_argument("--run-id", help="GitHub Actions run ID")
    parser.add_argument("--artifact", default="context-bundle", help="Artifact name to download")
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--skip-download", action="store_true", help="Skip download, use existing artifacts")
    
    args = parser.parse_args()
    
    if not args.skip_download:
        if not args.repo or not args.run_id:
            print("💡 Usage examples:")
            print("   # Download and process artifacts:")
            print("   python workflow_runner.py --repo owner/repo --run-id 123456789")
            print("")
            print("   # Use existing downloaded artifacts:")
            print("   python workflow_runner.py --skip-download")
            print("")
            print("   # Or run individual components:")
            print("   python llm_agent/enhanced_context_builder.py")
            print("   python llm_agent/generate_tests_from_artifacts.py")
            return
        
        repo_parts = args.repo.split("/")
        if len(repo_parts) != 2:
            raise SystemExit("❌ Repository must be in format owner/name")
        
        owner, name = repo_parts
        
        # Download artifacts
        try:
            download_github_artifact(owner, name, args.run_id, args.artifact, args.token)
        except Exception as e:
            print(f"⚠️  Artifact download failed: {e}")
            print("🔄 Continuing with local context building...")
    
    # Build context from available sources
    context_bundle = run_enhanced_context_builder()
    
    # Generate tests
    run_test_generator()
    
    print("\n🎉 Workflow completed successfully!")
    print("📁 Check tests/generated/ for new test files")

if __name__ == "__main__":
    main()