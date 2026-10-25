"""
Architecture rules (import-linter contracts in pyproject.toml), checked on every test run.

If test_import_contracts_are_kept fails, a module has imported across a layer boundary.
Fix the import rather than adding to ignore_imports in pyproject.toml.
"""

import os
import re
import subprocess
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYPROJECT = os.path.join(PROJECT_ROOT, "pyproject.toml")


def _lint(config_path: str):
    """
    Run import-linter in a subprocess: it reconfigures logging globally (disabling
    existing loggers), which would otherwise break later tests in the same process.
    """
    code = (
        "import sys; from importlinter.cli import lint_imports; "
        f"sys.exit(lint_imports(config_filename={config_path!r}, no_cache=True, no_logo=True))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=PROJECT_ROOT, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": PROJECT_ROOT},
    )
    return result.returncode, result.stdout + result.stderr


def test_import_contracts_are_kept():
    exit_code, output = _lint(PYPROJECT)
    assert exit_code == 0, f"Import contracts broken:\n{output}"
    assert "3 kept, 0 broken" in output


def test_contracts_detect_the_known_violation(tmp_path):
    """Without the ignore_imports entries, the known core -> clients import must break all 3 contracts."""
    with open(PYPROJECT, encoding="utf-8") as f:
        config = f.read()
    without_ignores = re.sub(r"ignore_imports = \[.*?\]\n", "", config, flags=re.DOTALL)
    assert without_ignores != config
    strict_config = tmp_path / "pyproject.toml"
    strict_config.write_text(without_ignores, encoding="utf-8")

    exit_code, output = _lint(str(strict_config))

    assert exit_code != 0
    assert "0 kept, 3 broken" in output
    assert "core.currency_converter -> clients.fx_client" in output
