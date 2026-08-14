from itertools import product
from typing import Dict, List, Optional

from src.fol_parser import BinOp, Formula, Not, Pred
from src.lean_emit import sanitize_identifier

_BOOL_OPS = {
    "∧": lambda a, b: a and b,
    "∨": lambda a, b: a or b,
    "→": lambda a, b: (not a) or b,
    "↔": lambda a, b: a == b,
    "⊕": lambda a, b: a != b,
}


def evaluate(formula: Formula, assignment: Dict[str, bool]) -> bool:
    if isinstance(formula, Pred):
        return assignment[formula.name]
    if isinstance(formula, Not):
        return not evaluate(formula.expr, assignment)
    if isinstance(formula, BinOp):
        left = evaluate(formula.left, assignment)
        right = evaluate(formula.right, assignment)
        return _BOOL_OPS[formula.op](left, right)
    raise TypeError(f"not a propositional formula node: {formula!r}")


def find_countermodel(
    premises: List[Formula], conclusion: Formula, atoms: List[str]
) -> Optional[Dict[str, bool]]:
    if not atoms:
        premises_hold = all(evaluate(p, {}) for p in premises)
        conclusion_holds = evaluate(conclusion, {})
        return {} if premises_hold and not conclusion_holds else None

    for bits in product([False, True], repeat=len(atoms)):
        assignment = dict(zip(atoms, bits))
        if all(evaluate(p, assignment) for p in premises) and not evaluate(conclusion, assignment):
            return assignment
    return None


def generate_case_split_tactic(atoms: List[str]) -> str:
    if not atoms:
        return "simp_all"
    cases = " <;> ".join(
        f"by_cases c{i} : {sanitize_identifier(atom)}" for i, atom in enumerate(atoms)
    )
    return f"classical\n  {cases} <;> simp_all"
