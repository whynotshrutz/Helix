"""Unit tests for Helix tools."""
import pytest
from pathlib import Path
import tempfile
import os
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from helix.tools import file_reader_tool, search_tool, doc_helper_tool


class TestFileReaderTool:
    def test_read_existing_file(self, tmp_path):
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        result = file_reader_tool("test.txt", base_dir=str(tmp_path))
        assert result["ok"] is True
        assert result["content"] == "Hello, World!"
        assert result["type"] == "file"
    
    def test_read_nonexistent_file(self, tmp_path):
        result = file_reader_tool("nonexistent.txt", base_dir=str(tmp_path))
        assert result["ok"] is False
        assert result["error"] == "file_not_found"
    
    def test_read_directory(self, tmp_path):
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        
        result = file_reader_tool(".", base_dir=str(tmp_path))
        assert result["ok"] is True
        assert result["type"] == "dir"
        assert len(result["files"]) >= 2


class TestSearchTool:
    def test_search_text(self, tmp_path):
        # Create test files
        (tmp_path / "file1.txt").write_text("Hello, World!")
        (tmp_path / "file2.txt").write_text("Goodbye, World!")
        
        results = search_tool("Hello", base_dir=str(tmp_path))
        assert len(results) == 1
        assert "Hello" in results[0]["snippet"]
    
    def test_search_regex(self, tmp_path):
        # Create test files
        (tmp_path / "file1.txt").write_text("test123")
        (tmp_path / "file2.txt").write_text("test456")
        
        results = search_tool(r"test\d+", base_dir=str(tmp_path), use_regex=True)
        assert len(results) == 2
    
    def test_max_results(self, tmp_path):
        # Create many matching files
        for i in range(10):
            (tmp_path / f"file{i}.txt").write_text("match")
        
        results = search_tool("match", base_dir=str(tmp_path), max_results=3)
        assert len(results) == 3


class TestDocHelperTool:
    def test_explain_code(self):
        code = """
def hello():
    pass

class MyClass:
    pass
"""
        result = doc_helper_tool(code, request="explain")
        assert result["ok"] is True
        assert "hello" in result["functions"]
        assert "MyClass" in result["classes"]
    
    def test_generate_docstring(self):
        code = "def test(): pass"
        result = doc_helper_tool(code, request="docstring")
        assert result["ok"] is True
        assert "docstring" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
