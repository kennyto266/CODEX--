"""
Contract tests for CLI interface.

These tests ensure the CLI interface meets its contract specifications.
"""

import pytest
import subprocess
import sys
from pathlib import Path


@pytest.fixture
def sample_data_path():
    """Path to sample data file."""
    return "data/0700_HK_sample.csv"


@pytest.mark.contract
def test_cli_help():
    """Test --help flag."""
    result = subprocess.run(
        [sys.executable, "rsi_backtest_optimizer.py", "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "RSI Backtest Optimizer" in result.stdout
    assert "--help" in result.stdout


@pytest.mark.contract
def test_cli_version():
    """Test --version flag."""
    result = subprocess.run(
        [sys.executable, "rsi_backtest_optimizer.py", "--version"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "RSI Backtest Optimizer" in result.stdout or result.stderr


@pytest.mark.contract
@pytest.mark.slow
def test_cli_default_run(sample_data_path):
    """Test default run with minimal parameters."""
    result = subprocess.run(
        [
            sys.executable, "rsi_backtest_optimizer.py",
            "--data", sample_data_path,
            "--start-window", "10",
            "--end-window", "20",
            "--step", "5",
            "--output-dir", "results/test_cli",
            "--no-charts"
        ],
        capture_output=True,
        text=True,
        timeout=60
    )

    # Should complete successfully
    assert result.returncode == 0, f"CLI failed: {result.stderr}"

    # Output should contain key information
    assert "Optimal RSI Window" in result.stdout


@pytest.mark.contract
def test_cli_missing_file():
    """Test error handling for missing data file."""
    result = subprocess.run(
        [
            sys.executable, "rsi_backtest_optimizer.py",
            "--data", "nonexistent_file.csv"
        ],
        capture_output=True,
        text=True
    )

    # Should fail with error code
    assert result.returncode != 0
    assert "ERROR" in result.stderr or "not found" in result.stderr.lower()


@pytest.mark.contract
def test_cli_invalid_parameters():
    """Test validation of invalid parameters."""
    result = subprocess.run(
        [
            sys.executable, "rsi_backtest_optimizer.py",
            "--start-window", "100",
            "--end-window", "50"  # Invalid: start > end
        ],
        capture_output=True,
        text=True
    )

    # Should fail with validation error
    assert result.returncode != 0
    assert "ERROR" in result.stderr or "must be <" in result.stderr


@pytest.mark.contract
@pytest.mark.slow
def test_cli_output_files(sample_data_path, tmp_path):
    """Test that all expected output files are created."""
    output_dir = tmp_path / "test_output"

    result = subprocess.run(
        [
            sys.executable, "rsi_backtest_optimizer.py",
            "--data", sample_data_path,
            "--start-window", "10",
            "--end-window", "15",
            "--output-dir", str(output_dir),
            "--no-charts"
        ],
        capture_output=True,
        text=True,
        timeout=60
    )

    assert result.returncode == 0

    # Check expected files exist
    assert (output_dir / "optimization_results.csv").exists()
    assert (output_dir / "top_10_windows.csv").exists()
    assert (output_dir / "summary_report.txt").exists()
