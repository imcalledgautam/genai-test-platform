# 🤖 GenAI Test Platform - Deployment Mode Options

## Mode 1: Fully Automated (Default) 
**File**: `.github/workflows/genai-unified-runner.yml`

```yaml
# Automatically runs tests after AI generation
- Push code → AI generates tests → Tests run immediately → Results reported
```

**Best for**: Development repos, quick feedback, CI/CD pipelines

---

## Mode 2: Human-in-the-Loop (HITL)
**File**: `.github/workflows/genai-hitl-workflow.yml` 

```yaml
# Creates PR for human review before test execution
- Push code → AI generates tests → Creates PR for review → Human approves → Tests run
```

**Best for**: Production systems, critical code, compliance requirements

---

## Switching Between Modes

### Deploy Automated Mode (Default)
```bash
# Uses genai-unified-runner.yml
./deploy-organization-wide.sh
```

### Deploy Human Review Mode  
```bash
# Edit the deployment script to use HITL workflow
export WORKFLOW_TEMPLATE="genai-hitl-workflow.yml"
./deploy-organization-wide.sh
```

---

## Customization Per Repository

Each repo can customize behavior in the workflow file:

```yaml
env:
  # AI Configuration
  GENAI_ENABLE: 'true'           # Enable/disable AI generation
  OLLAMA_MODEL: 'qwen2.5-coder:1.5b'  # AI model choice
  
  # Testing Configuration  
  COVERAGE_THRESHOLD: '70'       # Minimum coverage required
  STACK_OVERRIDE: 'auto'         # Force specific stack detection
  
  # Human Review Mode
  HITL_MODE: 'false'            # Enable human approval requirement
  AUTO_MERGE: 'false'           # Auto-merge approved tests
```

---

## What Languages Get What Support

| **Language** | **Auto-Detection** | **Test Frameworks** | **AI Generation** |
|-------------|-------------------|-------------------|------------------|
| **Python** | ✅ requirements.txt, *.py | pytest, unittest | ✅ Full support |
| **Java** | ✅ pom.xml, build.gradle | JUnit, TestNG | ✅ Full support | 
| **Node.js** | ✅ package.json, *.js | Jest, Mocha | ✅ Full support |
| **C/C++** | 🔄 CMake, Makefile | Google Test | ⚠️ Experimental |
| **Go** | 🔄 go.mod | Go test | ⚠️ Planned |

---

## Organization-Wide Impact

After deployment, **every eligible repository** gets:

✅ **Automatic stack detection** (Python/Java/Node/etc)  
✅ **Framework-specific setup** (pytest/JUnit/Jest/etc)
✅ **AI-powered test generation** using local Ollama
✅ **Security validation** and quality scoring
✅ **Rich GitHub Actions summaries** with coverage reports
✅ **Artifact uploads** (test results, coverage XML)

**Total setup time**: ~5 minutes for entire organization!