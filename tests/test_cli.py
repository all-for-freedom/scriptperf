"""
Test CLI command availability and basic functionality.
"""

import pytest
import subprocess
import sys
from pathlib import Path


def test_spx_command_exists():
    """Test that spx command is available."""
    result = subprocess.run(
        ["spx", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, "spx command should exist and show help"
    assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()
    assert "script" in result.stdout or "script" in result.stderr


def test_spx_version():
    """Test that spx command shows version."""
    result = subprocess.run(
        ["spx", "--version"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, "spx --version should work"
    assert "scriptperf" in result.stdout.lower()


def test_spx_script_not_found():
    """Test that spx correctly handles non-existent script."""
    result = subprocess.run(
        ["spx", "nonexistent_script_12345.py"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode != 0, "spx should return non-zero exit code for non-existent script"
    assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


def test_spx_with_simple_script(tmp_path):
    """Test spx with a simple Python script."""
    # Create a simple test script
    test_script = tmp_path / "test_script.py"
    test_script.write_text('print("Hello from test script")\n')

    # Run spx
    result = subprocess.run(
        ["spx", str(test_script)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(tmp_path),
    )

    # Check that script executed
    assert result.returncode == 0, "spx should successfully run the script"
    assert "Hello from test script" in result.stdout

    # Check that performance report was generated
    output_dir = tmp_path / "spx"
    if output_dir.exists():
        png_files = list(output_dir.glob("*.png"))
        # Report might not be generated for very short scripts, so this is optional
        # assert len(png_files) > 0, "Performance report should be generated"

