from typing import List

from src.argument.formalize import parse_argument
from src.verify.verdict import VerdictResult, check


def check_argument_fol(
    premise_texts: List[str], conclusion_text: str, theorem_name: str = "argument_check"
) -> VerdictResult:
    argument = parse_argument(premise_texts, conclusion_text)
    return check(argument, theorem_name=theorem_name)
