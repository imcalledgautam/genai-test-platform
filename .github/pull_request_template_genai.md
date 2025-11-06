# Pull Request Template for GenAI Generated Tests

## 🤖 AI-Generated Test Review

**This PR contains AI-generated tests that require human approval before merging.**

### 📊 Generation Summary

- **Files Generated**: <!-- Will be filled by workflow -->
- **Quality Score**: <!-- Will be filled by workflow -->
- **Validation Status**: <!-- Will be filled by workflow -->

---

## ✅ Human Review Checklist

Please review each section carefully before approving this PR.

### 🎯 Functional Correctness
- [ ] **Target Coverage**: All intended functions/classes have tests
- [ ] **Behavior Testing**: Tests actually verify the correct behavior, not just execution
- [ ] **Edge Cases**: Boundary conditions and edge cases are tested appropriately
- [ ] **Error Handling**: Exception cases and error conditions are covered
- [ ] **Integration Points**: Tests cover key integration points and dependencies

### 📏 Test Quality Standards
- [ ] **Descriptive Names**: Test methods have clear, descriptive names that explain what they test
- [ ] **AAA Structure**: Tests follow Arrange-Act-Assert or Given-When-Then pattern
- [ ] **Specific Assertions**: Assertions check actual values, not just `assert True`
- [ ] **Single Responsibility**: Each test focuses on one specific behavior
- [ ] **Readable Code**: Test code is clean and easy to understand

### 🛡️ Safety and Reliability
- [ ] **No Timing Dependencies**: No `sleep()`, `setTimeout()`, or time-based waits
- [ ] **No Network Calls**: No real HTTP requests (uses mocking instead)
- [ ] **Isolated**: Tests don't depend on external services, files, or databases
- [ ] **Deterministic**: Tests produce consistent results on every run
- [ ] **Clean State**: Tests don't modify global state or environment variables
- [ ] **Proper Cleanup**: Any setup is properly torn down

### 🔧 Technical Implementation
- [ ] **Valid Imports**: All import statements reference existing, available modules
- [ ] **Proper Mocking**: External dependencies are mocked appropriately
- [ ] **Framework Compliance**: Tests follow the project's testing framework conventions
- [ ] **Performance**: Tests run quickly (typically under 100ms each)

### 🧪 Local Validation
- [ ] **Tests Run**: All tests execute without import or syntax errors
- [ ] **Tests Pass**: Generated tests pass when run locally
- [ ] **Coverage**: Tests provide meaningful coverage of the target code
- [ ] **No Conflicts**: Tests don't conflict with existing test suite

---

## 📋 Review Instructions

### 1. **Download and Review**
```bash
# Checkout the PR branch
git fetch origin
git checkout genai/tests-YYYYMMDD-HHMMSS

# Review the generated files
ls tests/generated/
```

### 2. **Run Validation**
```bash
# Install dependencies
pip install -r requirements.txt

# Run the new tests
python -m pytest tests/generated/ -v

# Check coverage (optional)
python -m pytest tests/generated/ --cov=. --cov-report=term-missing
```

### 3. **Quality Assessment**
- Read through each test file
- Verify tests match the intended functionality
- Check that assertions are meaningful
- Ensure no dangerous patterns are present

### 4. **Approval Process**
- ✅ **Approve**: If all checklist items pass
- 🔄 **Request Changes**: If issues need to be addressed
- 💬 **Comment**: For questions or suggestions

---

## 🚨 Common Issues to Watch For

### ❌ **Anti-Patterns**
- Tests that always pass regardless of implementation
- Vague assertions like `assert result` or `assert True`
- Tests that depend on specific timing or external state
- Overly complex tests that test multiple things

### ⚠️ **Security Concerns**
- Any subprocess or system calls
- File operations outside of temp directories
- Network requests to real endpoints
- Dynamic code execution (eval, exec)

### 🔧 **Technical Issues**
- Import errors or missing dependencies
- Tests that fail inconsistently
- Slow tests (>1 second per test)
- Tests that modify global configuration

---

## 📚 Reference Materials

- [Testing Best Practices Guide](https://github.com/imcalledgautam/genai-test-platform/blob/main/TESTING_GUIDELINES.md)
- [GenAI Test Platform Documentation](https://github.com/imcalledgautam/genai-test-platform/blob/main/README.md)
- [Training Examples](https://github.com/imcalledgautam/genai-test-platform/tree/main/training_examples)

---

## 🤝 Questions?

If you have questions about reviewing these AI-generated tests:

1. Check the validation report in `genai_artifacts/validation_report.json`
2. Review the context bundle to understand what the AI analyzed
3. Look at similar examples in the training data
4. Ask questions in the PR comments

**Remember**: Human review is the final quality gate. When in doubt, request changes or ask questions.

---

*This template is part of the [GenAI Test Platform](https://github.com/imcalledgautam/genai-test-platform) Human-in-the-Loop workflow.*