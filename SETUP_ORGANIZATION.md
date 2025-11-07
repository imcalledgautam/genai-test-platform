# 🚀 Organization-Wide GenAI Test Platform Setup

## Step 1: Create GitHub Personal Access Token

1. Go to **GitHub Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **"Generate new token (classic)"**
3. Select these permissions:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
   - ✅ `admin:org` (Full control of orgs and teams)
4. Copy the token (you'll need it in step 3)

## Step 2: Identify Your Organization

Your GitHub organization name is visible in GitHub URLs like:
`https://github.com/YOUR_ORG_NAME/repository-name`

## Step 3: Deploy to All Repositories

### Option A: Automated Script (Recommended)
```bash
# Set your credentials
export GITHUB_TOKEN="your_github_personal_access_token_here"
export GITHUB_ORG="your_organization_name_here"

# Download and run deployment script
curl -L https://raw.githubusercontent.com/imcalledgautam/genai-test-platform/main/deploy-organization-wide.sh | bash
```

### Option B: Manual Repository Selection
```bash
# Clone this platform first
git clone https://github.com/imcalledgautam/genai-test-platform.git
cd genai-test-platform

# Run selective deployment
./deploy-organization-wide.sh --interactive
```

## Step 4: Verify Deployment ✅

After running the script, check any Python repository in your organization:
- Go to **Actions** tab
- You should see "GenAI Test Platform" workflow
- It will run automatically on next push/PR

## What Gets Added to Each Repository

The script automatically adds this workflow file to each Python repository:
`.github/workflows/genai-test-platform.yml`

This workflow:
- 🔍 **Detects** the technology stack (Python/Node/Java)
- 🤖 **Generates** AI-powered tests using Ollama + Qwen2.5-Coder
- 📊 **Runs** tests with coverage reporting
- 🛡️ **Validates** code quality and security
- 📈 **Creates** rich GitHub Actions summaries

## Customization Per Repository

Each repository can customize the workflow by editing:
```yaml
env:
  OLLAMA_MODEL: 'qwen2.5-coder:1.5b'  # Change AI model
  COVERAGE_THRESHOLD: '70'             # Change coverage target
  STACK_OVERRIDE: 'python'             # Force specific stack
```

## Monitoring Organization-Wide Results

View all GenAI test results across your organization:
1. Go to **Organization** → **Actions**
2. Filter by workflow: "GenAI Test Platform"
3. See test generation results across all repositories

## Troubleshooting

**Common Issues:**
- ❌ **403 Forbidden**: Check your GitHub token has `repo` and `workflow` permissions
- ❌ **Repository not found**: Verify organization name is correct
- ❌ **No Python repos found**: Script only deploys to Python repositories

**Get Help:**
- Check the deployment logs for detailed error messages
- Verify permissions on GitHub tokens
- Ensure organization admin access