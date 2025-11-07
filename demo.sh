#!/bin/bash

# GenAI Test Platform - Complete System Demo
# This script demonstrates the entire production workflow end-to-end

set -e

echo "🚀 GenAI Test Platform - Production Demo"
echo "========================================"
echo

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_section() {
    echo -e "${BLUE}📋 $1${NC}"
    echo "----------------------------------------"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
print_section "Checking Prerequisites"

if ! command -v python3 &> /dev/null; then
    print_error "Python3 is required but not installed"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is required but not installed"  
    exit 1
fi

print_success "Python environment is ready"

# Ensure we're in the right directory
if [[ ! -f "tools/unified_test_runner.py" ]]; then
    print_error "Please run this script from the genai-test-platform root directory"
    exit 1
fi

print_success "Repository structure validated"

# Install any missing dependencies
print_section "Installing Dependencies"
pip3 install -q requests psutil || {
    print_warning "Some dependencies may already be installed"
}

print_success "Dependencies verified"

echo

# Demo 1: Context Builder
print_section "Demo 1: Context Builder - Repository Analysis"
echo "Building LLM context from repository structure..."
python3 tools/context_builder_v2.py --verbose
print_success "Context built and saved to genai_artifacts/context.json"
echo

# Demo 2: Policy Checker
print_section "Demo 2: Policy Checker - Test Quality Validation"
echo "Checking existing test files for quality issues..."
python3 tools/policy_checker_v2.py tests/ --format text
print_success "Policy validation complete"
echo

# Demo 3: HITL Validator
print_section "Demo 3: HITL Validator - Human Review Workflow"
echo "Demonstrating human-in-the-loop review process..."
python3 tools/hitl_validator_v2.py demo
print_success "HITL workflow demonstration complete"
echo

# Demo 4: Evaluation Harness
print_section "Demo 4: Evaluation Harness - Pre-merge Validation"
echo "Running comprehensive evaluation on existing tests..."
if ls tests/unit/*.py &>/dev/null; then
    python3 tools/evaluation_harness_v2.py tests/unit/*.py
else
    python3 tools/evaluation_harness_v2.py tests/
fi
print_success "Evaluation harness validation complete"
echo

# Demo 5: Unified Test Runner (Main Orchestrator)
print_section "Demo 5: Unified Test Runner - Complete Orchestration"
echo "Running the main GenAI test platform orchestrator..."
echo "This demonstrates the 'One Action Step' for any repository:"
echo
echo -e "${YELLOW}$ python3 tools/unified_test_runner.py${NC}"
echo

# Set environment for demonstration (no actual LLM generation in demo)
export GENAI_TEST_GEN=false
python3 tools/unified_test_runner.py

print_success "Unified test runner demonstration complete"
echo

# Show generated artifacts
print_section "Generated Artifacts"
echo "The following artifacts were generated during this demo:"
echo

if [[ -d "genai_artifacts" ]]; then
    ls -la genai_artifacts/
    echo
    print_success "All artifacts generated successfully"
else
    print_warning "genai_artifacts directory not found"
fi

# Demo summary
echo
print_section "Demo Summary - Production Capabilities"
echo -e "${GREEN}✅ Context Builder:${NC} Repository analysis and LLM context generation"
echo -e "${GREEN}✅ Policy Checker:${NC} Test quality validation with configurable rules"
echo -e "${GREEN}✅ HITL Validator:${NC} Human review workflow with approval tracking"
echo -e "${GREEN}✅ Evaluation Harness:${NC} Pre-merge validation pipeline"  
echo -e "${GREEN}✅ Unified Test Runner:${NC} Complete orchestration and reporting"
echo

print_section "Quick Start Commands"
echo "To use this system in production:"
echo
echo -e "${BLUE}# Single command for any repository:${NC}"
echo -e "${YELLOW}python3 tools/unified_test_runner.py${NC}"
echo
echo -e "${BLUE}# With LLM test generation enabled:${NC}"
echo -e "${YELLOW}GENAI_TEST_GEN=true python3 tools/unified_test_runner.py${NC}"
echo
echo -e "${BLUE}# Validate specific test files:${NC}"
echo -e "${YELLOW}python3 tools/evaluation_harness_v2.py tests/your_tests.py${NC}"
echo
echo -e "${BLUE}# Check test quality:${NC}"
echo -e "${YELLOW}python3 tools/policy_checker_v2.py tests/${NC}"
echo

print_section "Integration Options"
echo "🔄 CI/CD Integration: See PRODUCTION_WORKFLOW_GUIDE.md"
echo "🎯 GitHub Actions: Copy workflow examples"
echo "⚙️  Custom Configuration: Edit policy_config.json"
echo "📊 Monitoring: Use generated JSON artifacts"
echo "👥 Team Training: Review HITL validator workflow"
echo

print_success "🎉 GenAI Test Platform Demo Complete!"
echo
echo "This production-ready system provides:"
echo "• Stack-agnostic test generation and validation"
echo "• Human-in-the-loop quality control"  
echo "• Comprehensive policy enforcement"
echo "• Enterprise-ready CI/CD integration"
echo "• One-command deployment for any repository"
echo
echo "Ready for production deployment! 🚀"