import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_FALLBACK_LEAN_PATH = Path.home() / ".elan" / "bin" / "lean"

_SORRY_MARKER = "declaration uses `sorry`"


class LeanToolchainNotFoundError(Exception):
    pass


@dataclass
class CompileResult:
    success: bool
    used_sorry: bool
    stdout: str
    stderr: str
    returncode: int
    elapsed: float

    @property
    def proved(self) -> bool:
        return self.success and not self.used_sorry


def find_lean_binary() -> str:
    found = shutil.which("lean")
    if found:
        return found
    if _FALLBACK_LEAN_PATH.exists():
        return str(_FALLBACK_LEAN_PATH)
    raise LeanToolchainNotFoundError(
        "no `lean` binary on PATH or at ~/.elan/bin/lean -- install elan: "
        "https://github.com/leanprover/elan"
    )


def is_lean_available() -> bool:
    try:
        find_lean_binary()
        return True
    except LeanToolchainNotFoundError:
        return False


def compile_lean(
    source: str, timeout: float = 30.0, lean_binary: Optional[str] = None
) -> CompileResult:
    binary = lean_binary or find_lean_binary()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".lean", delete=False, encoding="utf-8") as f:
        f.write(source)
        tmp_path = f.name

    start = time.monotonic()
    try:
        proc = subprocess.run(
            [binary, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.monotonic() - start
        combined = proc.stdout + proc.stderr
        return CompileResult(
            success=proc.returncode == 0,
            used_sorry=_SORRY_MARKER in combined,
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
            elapsed=elapsed,
        )
    except subprocess.TimeoutExpired as e:
        elapsed = time.monotonic() - start
        return CompileResult(
            success=False,
            used_sorry=False,
            stdout=(e.stdout or ""),
            stderr=f"compile timed out after {timeout}s",
            returncode=-1,
            elapsed=elapsed,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
