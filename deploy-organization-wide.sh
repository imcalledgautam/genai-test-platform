#!/bin/bash
# Organization-wide GenAI Test Platform Deployment Script
# Run this script to add GenAI testing to ALL repositories in your GitHub organization

set -e

GITHUB_TOKEN="${GITHUB_TOKEN}"
GITHUB_ORG="${GITHUB_ORG}"
WORKFLOW_TEMPLATE_URL="https://raw.githubusercontent.com/imcalledgautam/genai-test-platform/main/.github/workflow-templates/genai-test-platform.yml"

if [ -z "$GITHUB_TOKEN" ] || [ -z "$GITHUB_ORG" ]; then
    echo "❌ Error: Please set GITHUB_TOKEN and GITHUB_ORG environment variables"
    echo "Example:"
    echo "  export GITHUB_TOKEN='your_github_token'"
    echo "  export GITHUB_ORG='your_organization_name'"
    exit 1
fi

echo "🚀 Deploying GenAI Test Platform to ALL repositories in organization: $GITHUB_ORG"
echo "=================================================================="

# Function to add workflow to a repository
add_workflow_to_repo() {
    local repo_name=$1
    local repo_full_name="$GITHUB_ORG/$repo_name"
    
    echo "📦 Processing repository: $repo_full_name"
    
    # Check if repo is Python-based
    repo_info=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
                     "https://api.github.com/repos/$repo_full_name")
    
    language=$(echo "$repo_info" | grep -o '"language":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$language" != "Python" ] && [ "$language" != "python" ]; then
        echo "  ⏭️  Skipping (not a Python repository: $language)"
        return
    fi
    
    # Check if workflow already exists
    existing_workflow=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
                            "https://api.github.com/repos/$repo_full_name/contents/.github/workflows/genai-test-platform.yml" \
                            | grep -o '"name"')
    
    if [ -n "$existing_workflow" ]; then
        echo "  ✅ GenAI workflow already exists"
        return
    fi
    
    # Download the workflow template
    workflow_content=$(curl -s "$WORKFLOW_TEMPLATE_URL")
    
    # Create the workflow via GitHub API
    curl -s -X PUT \
         -H "Authorization: token $GITHUB_TOKEN" \
         -H "Content-Type: application/json" \
         "https://api.github.com/repos/$repo_full_name/contents/.github/workflows/genai-test-platform.yml" \
         -d "{
             \"message\": \"🤖 Add GenAI Test Platform automation\",
             \"content\": \"$(echo "$workflow_content" | base64 -w 0)\",
             \"branch\": \"main\"
         }" > /dev/null
    
    if [ $? -eq 0 ]; then
        echo "  ✅ GenAI Test Platform workflow added successfully"
    else
        echo "  ❌ Failed to add workflow (check permissions)"
    fi
}

# Get all repositories in the organization
echo "🔍 Fetching repositories from organization: $GITHUB_ORG"

page=1
while true; do
    repos=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
                 "https://api.github.com/orgs/$GITHUB_ORG/repos?page=$page&per_page=100" \
                 | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$repos" ]; then
        break
    fi
    
    for repo in $repos; do
        add_workflow_to_repo "$repo"
    done
    
    page=$((page + 1))
done

echo ""
echo "🎉 GenAI Test Platform deployment complete!"
echo ""
echo "📋 What was deployed:"
echo "  ✅ AI-powered test generation workflow"
echo "  ✅ Automatic coverage analysis" 
echo "  ✅ Rich GitHub Actions summaries"
echo "  ✅ Artifact uploads for test results"
echo ""
echo "🚀 Now ALL Python repositories in '$GITHUB_ORG' have automatic AI testing!"
echo "   Just push code changes to see GenAI in action."
echo ""
echo "📊 Monitor results at: https://github.com/orgs/$GITHUB_ORG/repositories"