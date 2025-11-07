#!/usr/bin/env python3
"""
Enhanced LLM Test Generator with Import Path Validation

This module generates pytest test cases using LLM while ensuring:
1. Correct import paths for the current project structure
2. Proper error handling and validation
3. Context-aware test generation based on actual code structure
"""

import os
import json
import re
import requests
import ast
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class EnhancedTestGenerator:
    def __init__(self, project_root: str = None):
        self.root = Path(project_root or Path(__file__).resolve().parents[1])
        self.bundle_path = self.root / "ci_artifacts" / "context_bundle.json"
        self.out_dir = self.root / "tests" / "generated"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:1.5b")
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.max_retries = 3
        self.timeout = 120
        
        # Load improved prompt template
        self.prompt_template = self._load_prompt_template()
        
    def _load_prompt_template(self) -> str:
        """Load and enhance the prompt template with project-specific guidance"""
        template_path = self.root / "llm_agent" / "prompt_template.txt"
        if template_path.exists():
            base_template = template_path.read_text(encoding="utf-8")
        else:
            base_template = self._get_default_template()
        
        # Add project-specific import guidance
        project_guidance = self._generate_import_guidance()
        return f"{base_template}\n\n{project_guidance}"
    
    def _generate_import_guidance(self) -> str:
        """Generate project-specific import guidance based on actual structure"""
        guidance = ["=== PROJECT-SPECIFIC IMPORT GUIDANCE ==="]
        
        # Check project structure
        src_exists = (self.root / "src").exists()
        packages = self._find_python_packages()
        
        if src_exists:
            guidance.append("- This project uses src/ layout: import with 'from src.module import ...'")
        else:
            guidance.append("- This project uses flat layout: import directly 'from module import ...'")
            guidance.append("- NO src/ directory exists - do NOT use 'from src.' imports")
        
        if packages:
            guidance.append(f"- Available packages: {', '.join(packages)}")
        
        # Add sys.path guidance for local imports
        guidance.extend([
            "- For local module imports, add at the top of test file:",
            "  import sys, os",
            "  sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))",
            "",
            "- Use ONLY these import patterns:",
            "  ✅ from llm_agent.generate_tests import SomeClass",
            "  ✅ from tools.context_builder import some_function", 
            "  ❌ from src.nonexistent import anything  # src/ doesn't exist!",
            "",
            "- For LangChain imports, use MODERN syntax:",
            "  ✅ from langchain_openai import OpenAIEmbeddings",
            "  ✅ from langchain_community.vectorstores import Chroma",
            "  ❌ from langchain.embeddings import OpenAIEmbeddings  # deprecated"
        ])
        
        return "\n".join(guidance)
    
    def _find_python_packages(self) -> List[str]:
        """Find Python packages in the project"""
        packages = []
        for item in self.root.iterdir():
            if (item.is_dir() and 
                not item.name.startswith('.') and 
                (item / '__init__.py').exists()):
                packages.append(item.name)
        return packages
    
    def _get_default_template(self) -> str:
        """Default prompt template if none exists"""
        return """
ROLE: You are a senior test automation engineer specializing in pytest.

TASK: Generate comprehensive pytest unit tests for changed Python functions/classes.

REQUIREMENTS:
1. Generate ONLY valid pytest code - no explanations, no markdown outside code blocks
2. Use correct import paths based on project structure (see guidance below)
3. Include positive, negative, boundary, and edge case tests
4. Use pytest fixtures and parametrize appropriately
5. Add proper error handling tests with pytest.raises()
6. Make tests deterministic and isolated

OUTPUT: Single Python file wrapped in ```python ``` code block only.
"""
    
    def load_context_bundle(self) -> Dict:
        """Load the context bundle with error handling"""
        if not self.bundle_path.exists():
            raise FileNotFoundError(f"Context bundle not found: {self.bundle_path}")
        
        try:
            with open(self.bundle_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in context bundle: {e}")
    
    def build_enhanced_prompt(self, bundle: Dict, module_path: str) -> Optional[str]:
        """Build an enhanced prompt with better context and validation"""
        files = bundle.get("files", [])
        target_file = next((f for f in files if f["path"] == module_path), None)
        
        if not target_file:
            print(f"Module {module_path} not found in bundle")
            return None
        
        # Build comprehensive context
        prompt_parts = [
            self.prompt_template,
            "\n=== TARGET MODULE FOR TESTING ===",
            f"File: {target_file['path']}",
            f"Language: {target_file.get('language', 'python')}",
        ]
        
        # Add diff if available
        if target_file.get("unified_diff"):
            prompt_parts.extend([
                "\nCHANGES (unified diff):",
                "```diff",
                target_file["unified_diff"][:5000],  # Limit diff size
                "```"
            ])
        
        # Add full file content
        if target_file.get("full_text"):
            prompt_parts.extend([
                "\nFULL FILE CONTENT:",
                "```python",
                target_file["full_text"][:15000],  # Limit content size
                "```"
            ])
        
        # Add context from related files
        related_files = [f for f in files if f["path"] != module_path and f.get("full_text")]
        if related_files:
            prompt_parts.append("\n=== CONTEXT FILES (for imports/dependencies) ===")
            for rf in related_files[:3]:  # Limit to first 3 related files
                prompt_parts.extend([
                    f"\n## {rf['path']}",
                    "```python",
                    rf["full_text"][:8000],  # Smaller limit for context files
                    "```"
                ])
        
        # Add analysis results if available
        targets = bundle.get("targets", {})
        if module_path in targets:
            prompt_parts.extend([
                "\n=== CODE ANALYSIS ===",
                json.dumps(targets[module_path], indent=2)
            ])
        
        return "\n".join(prompt_parts)
    
    def call_ollama_with_retry(self, prompt: str) -> Optional[str]:
        """Call Ollama with retry logic and better error handling"""
        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Lower temperature for more consistent code
                "top_p": 0.9,
                "num_predict": 4096,
            }
        }
        
        for attempt in range(self.max_retries):
            try:
                print(f"🤖 Calling Ollama (attempt {attempt + 1}/{self.max_retries})...")
                response = requests.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                
                result = response.json()
                if "response" in result:
                    return result["response"]
                else:
                    print(f"Unexpected response format: {result}")
                    continue
                    
            except requests.exceptions.Timeout:
                print(f"Timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    time.sleep(5)
                    continue
            except requests.exceptions.RequestException as e:
                print(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                    continue
            except Exception as e:
                print(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
        
        print(f"❌ Failed to get response after {self.max_retries} attempts")
        return None
    
    def extract_and_validate_code(self, llm_response: str) -> Optional[str]:
        """Extract Python code from LLM response and validate it"""
        if not llm_response:
            return None
        
        # Extract code from markdown code blocks
        code_blocks = re.findall(r'```python\s*\n(.*?)\n```', llm_response, re.DOTALL)
        if not code_blocks:
            # Try without language specifier
            code_blocks = re.findall(r'```\s*\n(.*?)\n```', llm_response, re.DOTALL)
        
        if not code_blocks:
            # If no code blocks, try to use the whole response if it looks like Python
            if ('import ' in llm_response and 'def test_' in llm_response):
                code = llm_response.strip()
            else:
                print("❌ No valid Python code blocks found in LLM response")
                return None
        else:
            code = code_blocks[0].strip()
        
        # Basic syntax validation
        try:
            ast.parse(code)
            print("✅ Generated code passed syntax validation")
            return code
        except SyntaxError as e:
            print(f"❌ Generated code has syntax errors: {e}")
            return None
    
    def save_test_file(self, code: str, module_path: str) -> Path:
        """Save the generated test code to a file"""
        # Generate test filename
        module_name = Path(module_path).stem
        test_filename = f"test_{module_name}_generated.py"
        test_path = self.out_dir / test_filename
        
        # Add file header with metadata
        header = f'''#!/usr/bin/env python3
"""
Generated test file for {module_path}
Created by: Enhanced LLM Test Generator
Generated at: {time.strftime("%Y-%m-%d %H:%M:%S")}
Model: {self.model}

This file contains automatically generated pytest test cases.
"""

import sys
import os
# Add project root to Python path for local imports  
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

'''
        
        # Write the file
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(header + code)
        
        print(f"💾 Saved test file: {test_path}")
        return test_path
    
    def generate_tests_for_module(self, module_path: str) -> Optional[Path]:
        """Generate tests for a specific module"""
        try:
            print(f"\n🎯 Generating tests for: {module_path}")
            
            # Load context
            bundle = self.load_context_bundle()
            
            # Build prompt
            prompt = self.build_enhanced_prompt(bundle, module_path)
            if not prompt:
                return None
            
            # Call LLM
            llm_response = self.call_ollama_with_retry(prompt)
            if not llm_response:
                return None
            
            # Extract and validate code
            test_code = self.extract_and_validate_code(llm_response)
            if not test_code:
                return None
            
            # Save test file
            test_path = self.save_test_file(test_code, module_path)
            return test_path
            
        except Exception as e:
            print(f"❌ Error generating tests for {module_path}: {e}")
            return None
    
    def generate_all_tests(self) -> List[Path]:
        """Generate tests for all modules in the context bundle"""
        try:
            bundle = self.load_context_bundle()
            files = bundle.get("files", [])
            python_files = [f["path"] for f in files if f.get("language") == "python"]
            
            print(f"📁 Found {len(python_files)} Python files to test")
            
            generated_files = []
            for module_path in python_files:
                test_file = self.generate_tests_for_module(module_path)
                if test_file:
                    generated_files.append(test_file)
            
            print(f"\n✅ Generated {len(generated_files)} test files:")
            for file_path in generated_files:
                print(f"   📄 {file_path}")
            
            return generated_files
            
        except Exception as e:
            print(f"❌ Error in generate_all_tests: {e}")
            return []

def main():
    """Main entry point"""
    generator = EnhancedTestGenerator()
    
    if len(sys.argv) > 1:
        # Generate tests for specific module
        module_path = sys.argv[1]
        test_file = generator.generate_tests_for_module(module_path)
        return test_file is not None
    else:
        # Generate tests for all modules
        test_files = generator.generate_all_tests()
        return len(test_files) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)