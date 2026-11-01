"""
Architecture rules (import-linter contracts in pyproject.toml), checked on every test run.

If test_import_contracts_are_kept fails, a module has imported across a layer boundary.
Fix the import rather than adding to ignore_imports in pyproject.toml.
"""

import os
import subprocess
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYPROJECT = os.path.join(PROJECT_ROOT, "pyproject.toml")


def _lint(config_path: str, project_root: str = PROJECT_ROOT):
    """
    Run import-linter in a subprocess: it reconfigures logging globally (disabling
    existing loggers), which would otherwise break later tests in the same process.
    """
    code = (
        "import sys; from importlinter.cli import lint_imports; "
        f"sys.exit(lint_imports(config_filename={config_path!r}, no_cache=True, no_logo=True))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=project_root, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": project_root},
    )
    return result.returncode, result.stdout + result.stderr


def test_import_contracts_are_kept():
    exit_code, output = _lint(PYPROJECT)
    assert exit_code == 0, f"Import contracts broken:\n{output}"
    assert "3 kept, 0 broken" in output


def test_contracts_detect_a_layer_violation(tmp_path):
    """The real contracts, run on a throwaway project where core imports clients, must break all three."""
    for package in ("clients", "core", "output", "config"):
        (tmp_path / package).mkdir()
        (tmp_path / package / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "clients" / "fx_client.py").write_text("RATE = 1.0\n", encoding="utf-8")
    (tmp_path / "core" / "currency_converter.py").write_text("from clients.fx_client import RATE\n", encoding="utf-8")
    (tmp_path / "output" / "section.py").write_text("import core.currency_converter\n", encoding="utf-8")
    with open(PYPROJECT, encoding="utf-8") as f:
        (tmp_path / "pyproject.toml").write_text(f.read(), encoding="utf-8")

    exit_code, output = _lint(str(tmp_path / "pyproject.toml"), project_root=str(tmp_path))

    assert exit_code != 0
    assert "0 kept, 3 broken" in output
    assert "core.currency_converter -> clients.fx_client" in output


def test_output_layer_reads_core_only_through_the_view_model():
    """M5/M7: sections only format — from core they import only the view model and the typed models."""
    import ast
    import glob
    root = os.path.join(os.path.dirname(__file__), "..")
    offenders = []
    for path in glob.glob(os.path.join(root, "output", "**", "*.py"), recursive=True):
        with open(path, encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.split('.')[0] == 'core':
                if node.module not in ('core.report_context', 'core.models'):
                    offenders.append(f"{os.path.relpath(path, root)}: {node.module}")
            elif isinstance(node, ast.Import):
                offenders += [f"{os.path.relpath(path, root)}: {a.name}" for a in node.names if a.name.startswith('core')]
    assert offenders == []
