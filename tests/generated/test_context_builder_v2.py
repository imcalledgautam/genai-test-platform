#!/usr/bin/env python3
"""
Tests for tools/context_builder_v2.py
Clean implementation that works with the actual module.
"""

import pytest
from pathlib import Path
import json
import tempfile
import os

# Import the actual module we're testing
from tools.context_builder_v2 import build_llm_context, summarize_repo, extract_python_surface

@pytest.mark.slow
@pytest.mark.integration
def test_build_llm_context():
    """Test that build_llm_context returns proper structure"""
    context = build_llm_context()
    
    # Check that all required keys are present
    assert "timestamp" in context
    assert "repository_root" in context
    assert "manifest" in context
    assert "public_surface" in context
    assert "conventions" in context
    
    # Check types
    assert isinstance(context["manifest"], dict)
    assert isinstance(context["public_surface"], dict)
    assert isinstance(context["conventions"], dict)
    
    # Check public surface has expected languages
    assert "python" in context["public_surface"]
    assert "javascript" in context["public_surface"]
    assert "java" in context["public_surface"]

@pytest.mark.slow
@pytest.mark.integration  
def test_summarize_repo():
    """Test repository summarization"""
    manifest = summarize_repo()
    
    # Check required keys
    assert "total_files" in manifest
    assert "files_sample" in manifest
    assert "config_files" in manifest
    assert "languages" in manifest
    assert "test_directories" in manifest
    
    # Check types
    assert isinstance(manifest["total_files"], int)
    assert isinstance(manifest["files_sample"], list)
    assert isinstance(manifest["config_files"], dict)
    assert isinstance(manifest["languages"], dict)
    assert isinstance(manifest["test_directories"], list)
    
    # Should detect Python in our repository
    assert manifest["languages"]["python"] is True

@pytest.mark.slow
@pytest.mark.integration
def test_extract_python_surface():
    """Test Python surface extraction - this analyzes actual repo files"""
    # This function analyzes the actual repository files
    surface = extract_python_surface()
    
    # Should find functions and classes in our repository (returns a list)
    assert isinstance(surface, list)
    
    # Should have Python items
    assert len(surface) > 0
    
    # Each item should be a dict with required keys
    for item in surface[:5]:  # Check first 5 items
        assert isinstance(item, dict)
        assert 'file' in item
        assert 'symbol' in item
        assert 'type' in item
    
    # In our repository, we should find some functions
    if surface:
        # Check that items have expected structure
        item = surface[0]
        assert 'file' in item
        assert 'symbol' in item
        assert 'type' in item

def test_context_file_creation():
    """Test that context.json file is properly created"""
    # Build context (this should create the file)
    context = build_llm_context()
    
    # Check that the file was created
    context_file = Path("genai_artifacts/context.json")
    assert context_file.exists()
    
    # Check that we can read it back
    with open(context_file) as f:
        saved_context = json.load(f)
    
    # Should have the same structure
    assert saved_context.keys() == context.keys()
    assert "public_surface" in saved_context
    assert "python" in saved_context["public_surface"]