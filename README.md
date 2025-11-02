# 🤖 GenAI Test Platform
**An AI-powered automated testing platform that generates comprehensive tests from code changes using LLMs.**

A complete CI/CD solution that automatically detects code changes, analyzes context, generates targeted tests using Large Language Models, and provides comprehensive coverage reporting.

---

## 🚀 **Complete Automated Workflow**

Push commits → GitHub Actions automatically:
1. **Detects Changes** - Identifies modified Python files
2. **Builds Context** - Creates comprehensive analysis bundle  
3. **Installs Ollama** - Sets up LLM environment in CI
4. **Generates Tests** - Creates pytest files using AI
5. **Runs Tests** - Executes tests with coverage analysis
6. **Reports Results** - Comprehensive GitHub Actions summary

## ✨ **Key Features**

- 🔍 **Smart Change Detection** - Git-based Python file analysis
- 🧠 **AI Test Generation** - Context-aware test creation using Qwen2.5-Coder
- 🛡️ **Safety Validation** - AST parsing, import safety, retry logic
- 📊 **Coverage Analysis** - Comprehensive test coverage reporting
- 🔄 **Complete CI Automation** - Zero manual intervention required
- 📈 **GitHub Integration** - Rich summaries and artifact uploads

---

## 🎯 **POC Demonstration**

This repository demonstrates a complete **Proof of Concept** for automated test generation:

### **What It Generates**
- **Functional Tests**: Core logic validation
- **Edge Case Tests**: Boundary conditions and error handling  
- **Regression Tests**: Prevents breaking existing functionality
- **Comprehensive Coverage**: Multiple test approaches per function

### **Current Test Results**
- ✅ **30 generated tests** across multiple modules
- 📊 **28% coverage** with room for improvement
- 🔧 **2 failing tests** (revealing actual code issues!)
- 🚀 **Fully automated pipeline** ready for production scaling

---

## 🛠️ **Technologies & Architecture**

### **Core Stack**
- **🐍 Python 3.10+** - Primary development language
- **🤖 Ollama + Qwen2.5-Coder** - Local LLM for test generation
- **🧪 pytest + coverage** - Testing framework and analysis
- **⚡ GitHub Actions** - Complete CI/CD automation
- **📊 Streamlit** - Demo dashboard (legacy component)

### **LLM Agent Components**
- `enhanced_context_builder.py` - Git diff analysis & context bundling
- `generate_tests.py` - AI-powered test generation with validation
- `run_tests.py` - Local test execution with coverage
- `code_analyzer.py` - Static code analysis and guidance

---

## 🚀 **Quick Start**

### **Automatic (Recommended)**
Just push your code changes to trigger the complete pipeline:

```bash
git add .
git commit -m "feat: your changes here"  
git push origin main
```

**→ Check GitHub Actions tab for complete automated results!**

### **Manual Local Testing**
```bash
# 1. Clone repository
git clone https://github.com/imcalledgautam/genai-test-platform.git
cd genai-test-platform

# 2. Install dependencies  
pip install -r requirements.txt

# 3. Build context bundle
python llm_agent/enhanced_context_builder.py

# 4. Generate tests (requires Ollama)
python llm_agent/generate_tests.py

# 5. Run tests with coverage
python llm_agent/run_tests.py
```

---

## 📂 **Repository Structure**

```
genai-test-platform/
├── .github/workflows/           # GitHub Actions CI/CD
│   ├── detect_changes.yml      # Main pipeline (complete automation)
│   └── run_tests.yml           # Standalone test runner
├── llm_agent/                  # AI test generation engine
│   ├── enhanced_context_builder.py  # Context analysis
│   ├── generate_tests.py       # LLM test generation  
│   ├── run_tests.py           # Test execution
│   └── prompt_template.txt     # LLM prompt template
├── tests/generated/            # AI-generated test files
├── code/                      # Sample application code
├── ci_artifacts/              # Build artifacts & context bundles
└── requirements.txt           # Python dependencies
```

---

## 🎯 **Next Steps & Roadmap**

### **Phase 2 Enhancements**
- 🎨 **Risk-Based Prioritization** - Focus on high-impact changes
- 💬 **Natural Language Interface** - Chat-based test requests
- 🔧 **Self-Healing Tests** - Automatic test maintenance
- 📊 **Advanced Metrics** - Quality scoring and trends
- 🌐 **Multi-Language Support** - Beyond Python

### **Production Scaling**
- 🏗️ **Self-Hosted Runners** - Dedicated CI infrastructure
- 🔐 **Enterprise Security** - Advanced safety controls
- 📈 **Performance Optimization** - Faster test generation
- 🔄 **Workflow Customization** - Team-specific configurations

---

## 🤝 **Contributing**

This is a **Proof of Concept** demonstrating AI-powered test automation. 

**Current Status**: ✅ **Complete automated pipeline ready for production scaling**

**Key Achievement**: End-to-end workflow from code push → AI analysis → test generation → execution → reporting

---

## 📄 **License**

This project is open source and available under the [MIT License](LICENSE).

---

**🚀 Ready to see AI-powered testing in action? Just push a commit and watch the magic happen!**
```
streamlit run dashboard.py
```
Data Source
The current data is mock data generated using Faker for demonstration purposes.

To generate your own transaction data, simply run:
```
python generate_mock_data.py
```

🤝 Contributing
Feel free to fork this repository, submit issues, and send pull requests. Contributions are welcome!
