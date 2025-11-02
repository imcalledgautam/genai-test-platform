# GenAI Test Platform - Complete Workflow Guide

This guide explains how to use the GitHub Actions workflow artifacts with the LLM test generation system.

## 🔄 Complete Workflow

```
Developer Push → GitHub Actions → Artifacts → Local LLM → Generated Tests
```

### Step 1: Push Code (triggers GitHub Actions)
When you push code, the GitHub Actions workflow:
1. Detects changed files
2. Builds a comprehensive context bundle
3. Uploads artifacts: `changed-files` and `context-bundle`

### Step 2: Use Artifacts for Test Generation

You have several options:

## Option A: Automated Workflow Runner (Recommended)

```bash
# Download artifacts and generate tests in one command
python workflow_runner.py --repo your-username/your-repo --run-id 123456789

# Or use existing downloaded artifacts
python workflow_runner.py --skip-download
```

## Option B: Manual Download + Generation

1. **Download artifacts from GitHub Actions:**
   - Go to your repository → Actions → latest workflow run
   - Download `context-bundle` artifact
   - Extract to `downloaded_artifacts/context-bundle/`

2. **Generate tests:**
   ```bash
   python llm_agent/generate_tests_from_artifacts.py
   ```

## Option C: Direct API Download

```bash
# Set your GitHub token
export GITHUB_TOKEN=your_github_token

# Download specific artifacts
python workflow_runner.py --repo owner/repo --run-id 123456789 --artifact context-bundle
```

## 🛠️ Setup Requirements

### 1. Ollama Setup
```bash
# Install Ollama (visit https://ollama.ai)
ollama pull qwen2.5-coder:7b
ollama serve
```

### 2. Environment Variables (Optional)
```bash
export OLLAMA_MODEL=qwen2.5-coder:7b
export OLLAMA_HOST=http://localhost:11434
export GITHUB_TOKEN=your_token_here  # For artifact downloads
```

### 3. Python Dependencies
```bash
pip install requests pytest pytest-cov
```

## 📁 File Structure

```
genai-test-platform/
├── .github/workflows/
│   └── detect_changes.yml          # GitHub Actions workflow
├── llm_agent/
│   ├── enhanced_context_builder.py # Smart context gathering
│   ├── generate_tests_from_artifacts.py # LLM test generator
│   └── prompt_template.txt         # LLM prompt template
├── tests/generated/                # Generated test files
├── ci_artifacts/                   # Local context bundles
├── downloaded_artifacts/           # Downloaded GitHub artifacts
└── workflow_runner.py              # Complete automation script
```

## 🔍 How Context Bundle Works

The context bundle (`context_bundle.json`) contains:

```json
{
  "files": [
    {
      "path": "code/dashboard.py",
      "full_text": "# Complete file content...",
      "unified_diff": "# Git diff output..."
    }
  ],
  "context": {
    "readme": "# Repository overview...",
    "requirements": "streamlit\npandas...",
    "sample_data": {
      "data/transactions.csv": "sample,data,rows..."
    }
  },
  "metadata": {
    "total_files": 2,
    "changed_files": 1,
    "dependency_files": 1
  }
}
```

## 🚀 Quick Start Examples

### After Pushing Code:

1. **Check GitHub Actions:**
   ```
   Go to: https://github.com/your-username/your-repo/actions
   Click on latest workflow run
   Note the run ID (in URL: /runs/123456789)
   ```

2. **Generate tests locally:**
   ```bash
   # Method 1: Full automation
   python workflow_runner.py --repo your-username/your-repo --run-id 123456789
   
   # Method 2: Download manually, then:
   python llm_agent/generate_tests_from_artifacts.py
   
   # Method 3: Build context locally
   python llm_agent/enhanced_context_builder.py
   python llm_agent/generate_tests_from_artifacts.py
   ```

3. **Run generated tests:**
   ```bash
   pytest tests/generated/ -v
   ```

## 🔧 Troubleshooting

### Context Bundle Not Found
- Check `ci_artifacts/context_bundle.json` exists
- Or download from GitHub Actions artifacts
- Or run: `python llm_agent/enhanced_context_builder.py`

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama
ollama serve

# Pull model if needed
ollama pull qwen2.5-coder:7b
```

### GitHub API Rate Limits
- Set `GITHUB_TOKEN` environment variable
- Use personal access token with `repo` scope

## 📊 Monitoring & Debugging

The workflow creates detailed summaries in GitHub Actions, showing:
- Number of files analyzed
- Changed vs dependency files
- Context bundle size
- Next steps for local execution

Check the "Summary" tab in your GitHub Actions run for detailed information.

## 🎯 Integration with Step 5 (pytest + coverage)

Once tests are generated, the next step will automatically:
1. Discover generated tests in `tests/generated/`
2. Run pytest with coverage
3. Report results back to GitHub

Stay tuned for Step 5 implementation!