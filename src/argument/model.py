from dataclasses import dataclass
from typing import List

from src.fol_parser import BinOp, Formula, Not, Pred, Quant
from src.pipeline import FormalizationError


class UnsupportedArgumentError(FormalizationError):
    pass


@dataclass
class Argument:
    premises: List[Formula]
    conclusion: Formula

    @property
    def formulas(self) -> List[Formula]:
        return [*self.premises, self.conclusion]


def assert_propositional(argument: Argument) -> None:
    for formula in argument.formulas:
        _walk(formula)


def _walk(node: Formula) -> None:
    if isinstance(node, Pred):
        if node.args:
            raise UnsupportedArgumentError(
                f"predicate '{node.name}' takes arguments -- Phase 1 only supports "
                f"bare propositional atoms (e.g. 'P', not 'Man(x)')"
            )
        return
    if isinstance(node, Not):
        _walk(node.expr)
        return
    if isinstance(node, BinOp):
        if node.op == "⊕":
            raise UnsupportedArgumentError(
                "XOR (⊕) not supported yet -- needs Mathlib's Xor', out of scope "
                "for Phase 1; rewrite as ¬(P ↔ Q)"
            )
        _walk(node.left)
        _walk(node.right)
        return
    if isinstance(node, Quant):
        raise UnsupportedArgumentError(
            "quantifiers (∀/∃) not supported yet -- Phase 1 is propositional-only "
            "(validity of quantified FOL is undecidable in general)"
        )
    raise TypeError(f"unknown formula node: {node!r}")
