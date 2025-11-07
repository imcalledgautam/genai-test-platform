#!/usr/bin/env python3
"""
Test Import Fixer - Fix import paths in LLM-generated tests

This script addresses common issues with LLM-generated test files:
1. Missing src directory imports (when src doesn't exist)  
2. Outdated LangChain import paths
3. Missing pytest imports
4. Path resolution issues
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

class TestImportFixer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.fixes_applied = []
        
    def find_test_files(self, test_dirs: List[str] = None) -> List[Path]:
        """Find all test files in specified directories"""
        if test_dirs is None:
            test_dirs = ["tests", "test"]
            
        test_files = []
        for test_dir in test_dirs:
            test_path = self.project_root / test_dir
            if test_path.exists():
                test_files.extend(test_path.rglob("test_*.py"))
                test_files.extend(test_path.rglob("*_test.py"))
        
        return test_files
    
    def fix_import_paths(self, file_path: Path) -> bool:
        """Fix common import path issues in a test file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_made = []
            
            # Fix 1: Remove non-existent src imports
            if not (self.project_root / "src").exists():
                # Replace 'from src.module import ...' with 'from module import ...'
                pattern = r'from src\.([a-zA-Z_][a-zA-Z0-9_]*) import'
                replacement = r'from \1 import'
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    fixes_made.append("Removed 'src.' prefix from imports")
            
            # Fix 2: Update LangChain imports
            langchain_fixes = [
                (r'from langchain\.embeddings import OpenAIEmbeddings', 
                 'from langchain_openai import OpenAIEmbeddings'),
                (r'from langchain\.llms import OpenAI', 
                 'from langchain_openai import OpenAI'),
                (r'from langchain\.chat_models import ChatOpenAI', 
                 'from langchain_openai import ChatOpenAI'),
                (r'from langchain\.vectorstores import Chroma', 
                 'from langchain_community.vectorstores import Chroma'),
            ]
            
            for old_import, new_import in langchain_fixes:
                if re.search(old_import, content):
                    content = content.replace(old_import, new_import)
                    fixes_made.append(f"Updated LangChain import: {old_import}")
            
            # Fix 3: Add missing pytest import
            if 'import pytest' not in content and 'pytest.' in content:
                # Add pytest import after other imports
                import_section = []
                other_lines = []
                in_imports = True
                
                for line in content.split('\n'):
                    if line.strip().startswith(('import ', 'from ')) and in_imports:
                        import_section.append(line)
                    elif line.strip() == '' and in_imports:
                        import_section.append(line)
                    else:
                        if in_imports and line.strip():
                            import_section.append('import pytest')
                            import_section.append('')
                            in_imports = False
                        other_lines.append(line)
                
                if in_imports:  # All lines were imports
                    import_section.append('import pytest')
                    import_section.append('')
                
                content = '\n'.join(import_section + other_lines)
                fixes_made.append("Added missing 'import pytest'")
            
            # Fix 4: Add PYTHONPATH imports for local modules
            local_modules = self._find_local_modules()
            for module in local_modules:
                old_pattern = rf'from {module} import'
                if re.search(old_pattern, content):
                    # Add sys.path.insert if not already present
                    if 'sys.path.insert' not in content:
                        pytest_import_line = 'import pytest'
                        if pytest_import_line in content:
                            content = content.replace(
                                pytest_import_line, 
                                f'import sys\nimport os\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n{pytest_import_line}'
                            )
                            fixes_made.append("Added sys.path configuration for local imports")
                            break
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fixes_applied.append({
                    'file': str(file_path),
                    'fixes': fixes_made
                })
                return True
            
            return False
            
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False
    
    def _find_local_modules(self) -> List[str]:
        """Find local Python modules that might be imported"""
        modules = []
        
        # Check for common module directories
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                if (item / '__init__.py').exists() or any(item.glob('*.py')):
                    modules.append(item.name)
        
        # Check for single Python files that might be modules
        for py_file in self.project_root.glob('*.py'):
            if not py_file.name.startswith('test_') and not py_file.name.endswith('_test.py'):
                modules.append(py_file.stem)
        
        return modules
    
    def fix_all_tests(self, test_dirs: List[str] = None) -> dict:
        """Fix import issues in all test files"""
        test_files = self.find_test_files(test_dirs)
        
        results = {
            'total_files': len(test_files),
            'files_fixed': 0,
            'files_skipped': 0,
            'fixes_applied': []
        }
        
        for test_file in test_files:
            print(f"Checking {test_file}...")
            if self.fix_import_paths(test_file):
                results['files_fixed'] += 1
                print(f"  ✅ Fixed imports in {test_file}")
            else:
                results['files_skipped'] += 1
                print(f"  ⏭️  No fixes needed for {test_file}")
        
        results['fixes_applied'] = self.fixes_applied
        return results

def main():
    """Run the test import fixer"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    print(f"🔧 Fixing test imports in {project_root}")
    
    fixer = TestImportFixer(project_root)
    results = fixer.fix_all_tests()
    
    print(f"\n📊 Results:")
    print(f"   Total files: {results['total_files']}")
    print(f"   Files fixed: {results['files_fixed']}")
    print(f"   Files skipped: {results['files_skipped']}")
    
    if results['fixes_applied']:
        print(f"\n🛠️  Fixes applied:")
        for fix in results['fixes_applied']:
            print(f"   📄 {fix['file']}:")
            for fix_desc in fix['fixes']:
                print(f"      • {fix_desc}")
    
    return results['files_fixed'] > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)