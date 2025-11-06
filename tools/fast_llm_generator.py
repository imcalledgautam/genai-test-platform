#!/usr/bin/env python3
"""
Fast LLM Test Generator
======================

Optimized for speed with minimal prompts and focused generation.
"""

import json
import requests
import os
from pathlib import Path
from typing import Dict, List, Any

ROOT = Path(__file__).resolve().parents[1]

def generate_minimal_prompt(file_info: Dict[str, Any]) -> str:
    """Create a minimal, focused prompt for fast generation."""
    
    functions = file_info.get("functions", [])
    classes = file_info.get("classes", [])
    module = file_info.get("module", "")
    
    prompt = f"""Generate pytest tests for {module}:

Functions to test:"""
    
    for func in functions[:2]:  # Only 2 functions max
        prompt += f"\n- {func['name']}: {func['docstring'][:50]}..."
    
    for cls in classes[:1]:  # Only 1 class max
        methods = ", ".join(cls['methods'][:3])
        prompt += f"\nClass {cls['name']} methods: {methods}"
    
    prompt += f"""

Requirements:
1. Import: from {module} import *
2. Simple test functions only
3. Basic assertions
4. No complex mocking

Generate 2-3 test functions maximum:"""
    
    return prompt

def fast_llm_generate(context: Dict[str, Any]) -> int:
    """Generate tests quickly with minimal prompts."""
    
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")  # Use available model
    
    # Test connection
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=3)
        if response.status_code != 200:
            print(f":: Ollama not available")
            return 0
    except Exception:
        print(f":: Ollama connection failed")
        return 0
    
    generated_count = 0
    test_dir = ROOT / "tests" / "fast_generated"
    test_dir.mkdir(exist_ok=True)
    
    files = context.get("files", [])
    
    for file_info in files[:2]:  # Process maximum 2 files
        print(f":: Fast generating for {file_info['file']}...")
        
        # Create minimal prompt
        prompt = generate_minimal_prompt(file_info)
        
        try:
            # Fast generation with tight constraints
            response = requests.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,    # Deterministic
                        "top_p": 0.8,
                        "num_ctx": 2048,       # Very small context
                        "num_predict": 500,    # Limit output length
                        "stop": ["\n\nclass", "\n\ndef test_test_"]  # Stop early
                    }
                },
                timeout=30  # Short timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_code = result.get("response", "").strip()
                
                # Clean markdown
                if "```python" in generated_code:
                    generated_code = generated_code.split("```python")[1].split("```")[0].strip()
                elif "```" in generated_code:
                    generated_code = generated_code.split("```")[1].strip()
                
                if generated_code and "def test_" in generated_code:
                    # Save test file
                    module_name = file_info['module'].split('.')[-1]
                    test_file = test_dir / f"test_{module_name}_fast.py"
                    test_file.write_text(generated_code, encoding='utf-8')
                    print(f":: ✅ Generated {test_file}")
                    generated_count += 1
                else:
                    print(f":: ❌ No valid tests for {file_info['file']}")
            else:
                print(f":: ❌ API error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f":: ⏰ Timeout for {file_info['file']}")
            continue
        except Exception as e:
            print(f":: 💥 Error for {file_info['file']}: {e}")
            continue
    
    print(f":: Fast generation completed: {generated_count} files")
    return generated_count

def main():
    """Main fast generation workflow."""
    # Import lightweight context builder
    import sys
    sys.path.append(str(ROOT / "tools"))
    
    try:
        from lightweight_context_builder import build_lightweight_context
        context = build_lightweight_context()
        generated = fast_llm_generate(context)
        
        print(f"\n🎯 Fast LLM Generation Summary:")
        print(f"   Files processed: {len(context.get('files', []))}")
        print(f"   Tests generated: {generated}")
        print(f"   Success rate: {generated/max(1,len(context.get('files',[]))):.1%}")
        
        return generated > 0
        
    except Exception as e:
        print(f"❌ Fast generation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)