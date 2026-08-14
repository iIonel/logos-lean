from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from src.argument.model import Argument
from src.lean_toolchain import compile_lean
from src.verify.case_split import find_countermodel
from src.verify.emit_argument import collect_atoms, emit_invalid_proof, emit_valid_proof


class Verdict(Enum):
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class VerdictResult:
    verdict: Verdict
    lean_source: str
    diagnostic: str
    countermodel: Optional[Dict[str, bool]] = None


def _finalize(
    source: str,
    timeout: float,
    ok_verdict: Verdict,
    ok_diagnostic: str,
    err_diagnostic: str,
    countermodel: Optional[Dict[str, bool]] = None,
) -> VerdictResult:
    result = compile_lean(source, timeout=timeout)
    if result.proved:
        return VerdictResult(ok_verdict, source, ok_diagnostic, countermodel=countermodel)
    return VerdictResult(
        Verdict.ERROR,
        source,
        f"{err_diagnostic}:\n{result.stdout}{result.stderr}",
        countermodel=countermodel,
    )


def check(
    argument: Argument, theorem_name: str = "argument_check", timeout: float = 30.0
) -> VerdictResult:
    atoms = collect_atoms(argument)
    countermodel = find_countermodel(argument.premises, argument.conclusion, atoms)

    if countermodel is None:
        source = emit_valid_proof(argument, atoms, theorem_name=theorem_name)
        return _finalize(
            source,
            timeout,
            Verdict.VALID,
            "Lean accepted the case-split proof -- holds for every truth assignment.",
            "Python's truth table says valid, but Lean rejected the case-split proof "
            "(this would be a bug in the decision procedure)",
        )

    source = emit_invalid_proof(argument, atoms, countermodel, theorem_name=theorem_name)
    return _finalize(
        source,
        timeout,
        Verdict.INVALID,
        f"Lean accepted the countermodel witness {countermodel} -- premises can hold "
        "while the conclusion fails.",
        f"Python found countermodel {countermodel}, but Lean rejected the witness proof "
        "(this would be a bug in the decision procedure)",
        countermodel=countermodel,
    )
