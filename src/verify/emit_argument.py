from typing import Dict, List

from src.argument.model import Argument
from src.fol_parser import Formula, collect_signature
from src.lean_emit import format_formula, sanitize_identifier
from src.verify.case_split import generate_case_split_tactic


def collect_atoms(argument: Argument) -> List[str]:
    names = set()
    for formula in argument.formulas:
        preds, _ = collect_signature(formula)
        names.update(preds.keys())
    return sorted(names)


def _closed_formula(formula: Formula, assignment: Dict[str, bool]) -> str:
    return format_formula(formula, render_pred=lambda p: "True" if assignment[p.name] else "False")


def emit_valid_proof(
    argument: Argument, atoms: List[str], theorem_name: str = "argument_check"
) -> str:
    lines = [f"variable ({sanitize_identifier(a)} : Prop)" for a in atoms]
    hyps = " ".join(
        f"(h{i} : {format_formula(p)})" for i, p in enumerate(argument.premises, start=1)
    )
    lines.append("")
    lines.append(f"theorem {theorem_name} {hyps} : {format_formula(argument.conclusion)} := by")
    lines.append(f"  {generate_case_split_tactic(atoms)}")
    return "\n".join(lines)


def emit_invalid_proof(
    argument: Argument,
    atoms: List[str],
    countermodel: Dict[str, bool],
    theorem_name: str = "argument_check",
) -> str:
    binders = " ".join(f"({sanitize_identifier(a)} : Prop)" for a in atoms)
    witnesses = ", ".join("True" if countermodel[a] else "False" for a in atoms)

    premise_terms = [f"({_closed_formula(p, countermodel)})" for p in argument.premises]
    premises_conj = " ∧ ".join(premise_terms)
    body = f"{premises_conj} ∧ ¬({_closed_formula(argument.conclusion, countermodel)})"

    return f"theorem {theorem_name} : ∃ {binders}, {body} := ⟨{witnesses}, by decide⟩"
