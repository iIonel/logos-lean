from typing import List

from src.argument.model import Argument, assert_propositional
from src.fol_parser import Formula, parse_fol
from src.pipeline import FormalizationError


def _parse_or_raise(text: str, label: str) -> Formula:
    try:
        return parse_fol(text)
    except Exception as e:
        raise FormalizationError(f"{label} couldn't parse as FOL: {e}") from e


def parse_argument(premise_texts: List[str], conclusion_text: str) -> Argument:
    premises = [
        _parse_or_raise(text, f"premise {i}")
        for i, text in enumerate(premise_texts, start=1)
        if text.strip()
    ]
    if not premises:
        raise FormalizationError("at least one premise is required")

    conclusion = _parse_or_raise(conclusion_text, "conclusion")

    argument = Argument(premises=premises, conclusion=conclusion)
    assert_propositional(argument)
    return argument
