"""
Lint rules (ruff, configured in pyproject.toml), checked on every test run.

If this fails, run `python3 -m ruff check .` to see the findings and fix them
(many are auto-fixable with `python3 -m ruff check . --fix`).
"""

import os
import subprocess
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_ruff_reports_no_findings():
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", ".", "--no-cache", "--output-format", "concise"],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, f"ruff findings:\n{result.stdout}{result.stderr}"
