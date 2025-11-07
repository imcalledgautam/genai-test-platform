# GitHub Actions Workflow Troubleshooting Guide

## Current Status Check

To verify if your GitHub Actions are working:

1. **Visit**: https://github.com/imcalledgautam/genai-test-platform/actions
2. **Look for**: Recent workflow runs triggered by commits `37d900d` and `4ea85c8`
3. **Expected workflows**:
   - "GenAI Test Platform - Complete CI Pipeline" (from detect_changes.yml)
   - "GenAI Test Generation" (from genai-testing.yml) 
   - "Standalone Test Runner" (manual/scheduled only)

## Common Issues and Solutions

### Issue 1: Workflow Not Triggering
**Symptoms**: No workflows appear after pushing commits with Python files
**Solutions**:
- Check that you pushed to the `main` branch
- Verify workflow YAML syntax is valid
- Ensure the repository has Actions enabled

### Issue 2: Multiple Workflows Running  
**Symptoms**: Multiple workflows trigger on the same push
**Current Status**: You have 2 workflows that trigger on push to main:
- `detect_changes.yml` (primary workflow)
- `genai-testing.yml` (secondary workflow)

**To fix** (if they conflict):
```bash
# Disable one of them by renaming
mv .github/workflows/genai-testing.yml .github/workflows/genai-testing.yml.disabled
git add . && git commit -m "Disable duplicate workflow" && git push
```

### Issue 3: Context Builder Not Found
**Fixed**: Added fallback logic in workflow
**Current behavior**: Tries builders in this order:
1. `tools/context_builder_v2.py`
2. `llm_agent/enhanced_context_builder.py` 
3. `llm_agent/context_builder.py`
4. Creates minimal bundle if none found

### Issue 4: Test Generation Fails
**Fixed**: Added enhanced test generator integration
**Current behavior**: Tries generators in this order:
1. `tools/enhanced_test_generator.py` (your new enhanced version)
2. `llm_agent/generate_tests.py` (original version)

### Issue 5: Missing Dependencies
**Fixed**: Workflow now installs `pytest`, `pytest-cov`, `coverage`

## Verification Steps

1. **Check latest commit triggered workflow**:
   ```bash
   # This should show recent commits
   git log --oneline -n 3
   ```

2. **If workflow still not running**:
   - Make a small change to any `.py` file
   - Commit and push
   - Check Actions tab within 1-2 minutes

3. **Manual trigger test**:
   - Go to Actions tab
   - Click "GenAI Test Generation" 
   - Click "Run workflow" button
   - Select main branch
   - Click "Run workflow"

## Expected Workflow Behavior

When working correctly, each push to main with Python changes should:

1. ✅ **Detect Changes**: Find modified Python files
2. ✅ **Build Context**: Create context bundle for LLM
3. ✅ **Install Ollama**: Set up LLM environment  
4. ✅ **Generate Tests**: Create pytest test files
5. ✅ **Run Tests**: Execute tests with coverage
6. ✅ **Upload Artifacts**: Save results and reports

## Next Steps

1. **Check Actions Tab Now**: Visit the GitHub Actions page
2. **If workflows are running**: ✅ Problem solved!
3. **If still no workflows**: Try the manual trigger method above
4. **If workflows fail**: Check the logs for specific error messages

The fixes we applied should resolve the most common issues with GitHub Actions not running after major repository changes.