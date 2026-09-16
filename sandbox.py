"""Cortex Agent - Sandboxed Python Code Execution & Data Science Plot Engine.

Executes Python code in an isolated subprocess with timeout constraints,
AST security filtering, and automatic headless Matplotlib plot harvesting.
"""

import ast
import base64
import io
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Optional, Tuple

WORKSPACE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = WORKSPACE_DIR / ".venv" / "Scripts" / "python.exe"
PYTHON_BIN = str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))
DEFAULT_TIMEOUT_SECONDS = 15

# Forbidden patterns in AST that attempt to format/destroy systems or hijack OS
DISALLOWED_MODULES = {
    "pty", "winreg",
}

DISALLOWED_CALLS = {
    ("shutil", "rmtree"),
    ("os", "system"),
    ("os", "popen"),
    ("os", "spawn"),
    ("os", "remove"),
    ("os", "unlink"),
    ("subprocess", "Popen"),
    ("subprocess", "call"),
    ("subprocess", "run"),
}

DISALLOWED_BUILTINS = {
    "eval", "exec", "compile", "__import__"
}


def validate_code_safety(code: str) -> Tuple[bool, Optional[str]]:
    """Inspect abstract syntax tree (AST) for explicitly malicious/destructive actions."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Let python run and produce regular SyntaxError tracebacks
        return True, None

    for node in ast.walk(tree):
        # 1. Detect disallowed imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                if root_pkg in DISALLOWED_MODULES:
                    return False, f"Importing '{alias.name}' is restricted in the execution sandbox."
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                if root_pkg in DISALLOWED_MODULES:
                    return False, f"Importing from '{node.module}' is restricted in the execution sandbox."

        # 2. Block dangerous system destruction and builtin eval calls
        if isinstance(node, ast.Call):
            # Form: os.system(...), shutil.rmtree(...)
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    mod_name = node.func.value.id
                    func_name = node.func.attr
                    if (mod_name, func_name) in DISALLOWED_CALLS:
                        return False, f"Calling '{mod_name}.{func_name}()' is blocked for sandbox security."
            # Form: eval(...), exec(...)
            elif isinstance(node.func, ast.Name):
                if node.func.id in DISALLOWED_BUILTINS:
                    return False, f"Calling '{node.func.id}()' is blocked for sandbox security."

    return True, None


EXECUTION_WRAPPER = """
import sys, os

# Ensure headless Agg backend before importing pyplot
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except Exception:
    plt = None

exec_error = False

# User code execution
try:
    exec(compile(__USER_CODE_REPR__, '<cortex_sandbox>', 'exec'))
except Exception:
    import traceback
    traceback.print_exc()
    exec_error = True

# Harvest any opened matplotlib figures
if plt is not None:
    try:
        import io, base64
        fignums = plt.get_fignums()
        for fignum in fignums:
            fig = plt.figure(fignum)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', dpi=120)
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode('ascii')
            print(f"\\n__CORTEX_PLOT_B64__:data:image/png;base64,{b64}\\n")
            plt.close(fig)
    except Exception:
        pass

if exec_error:
    sys.exit(1)
"""


def run_python_code(code: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS, **kwargs) -> dict:
    """Execute Python code safely inside an isolated subprocess in the workspace virtual environment.

    Returns:
        dict with keys: ok, success, stdout, stderr, exit_code, duration_ms, plots, figures, timed_out, error
    """
    timeout_seconds = kwargs.get("timeout_secs", timeout_seconds)
    clean_code = code.strip()
    if not clean_code:
        return {
            "ok": False,
            "success": False,
            "stdout": "",
            "stderr": "Error: Code cannot be empty.",
            "exit_code": 1,
            "duration_ms": 0,
            "plots": [],
            "figures": [],
            "timed_out": False,
            "error": "Empty code payload",
        }

    # Safety validation
    is_safe, reason = validate_code_safety(clean_code)
    if not is_safe:
        return {
            "ok": False,
            "success": False,
            "stdout": "",
            "stderr": f"Security Notice: {reason}",
            "exit_code": 1,
            "duration_ms": 0,
            "plots": [],
            "figures": [],
            "timed_out": False,
            "error": reason,
        }

    # Build runner script
    runner_script = EXECUTION_WRAPPER.replace("__USER_CODE_REPR__", repr(clean_code))

    start_time = time.perf_counter()
    try:
        proc = subprocess.run(
            [PYTHON_BIN, "-c", runner_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            cwd=str(WORKSPACE_DIR),
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg"},
        )
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        raw_stdout = proc.stdout or ""
        raw_stderr = proc.stderr or ""
        exit_code = proc.returncode

        # Extract harvested plots from stdout
        plots = []
        plot_matches = re.findall(r"__CORTEX_PLOT_B64__:(data:image\/png;base64,[A-Za-z0-9+/=]+)", raw_stdout)
        for p in plot_matches:
            plots.append(p)

        # Clean stdout by removing plot markers
        clean_stdout = re.sub(r"__CORTEX_PLOT_B64__:data:image\/png;base64,[A-Za-z0-9+/=]+\n?", "", raw_stdout).strip()
        clean_stderr = raw_stderr.strip()

        ok = (
            (exit_code == 0)
            and ("Traceback (most recent call last):" not in clean_stdout)
            and ("Traceback (most recent call last):" not in clean_stderr)
            and ("SyntaxError:" not in clean_stderr)
        )

        return {
            "ok": ok,
            "success": ok,
            "stdout": clean_stdout,
            "stderr": clean_stderr,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "plots": plots,
            "figures": plots,
            "timed_out": False,
            "error": None if ok else (clean_stderr or "Execution encountered an error"),
        }

    except subprocess.TimeoutExpired:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "ok": False,
            "success": False,
            "stdout": "",
            "stderr": f"Execution Timed Out: Code exceeded the {timeout_seconds}-second execution limit.",
            "exit_code": 124,
            "duration_ms": duration_ms,
            "plots": [],
            "figures": [],
            "timed_out": True,
            "error": f"Timeout after {timeout_seconds}s",
        }
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "ok": False,
            "success": False,
            "stdout": "",
            "stderr": f"Execution System Failure: {exc}",
            "exit_code": 1,
            "duration_ms": duration_ms,
            "plots": [],
            "figures": [],
            "timed_out": False,
            "error": str(exc),
        }
