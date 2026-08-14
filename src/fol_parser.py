from dataclasses import dataclass, field
from typing import List, Union

from lark import Lark, Transformer


@dataclass
class Pred:
    name: str
    args: List[str] = field(default_factory=list)


@dataclass
class Not:
    expr: "Formula"


@dataclass
class BinOp:
    op: str
    left: "Formula"
    right: "Formula"


@dataclass
class Quant:
    quantifier: str
    var: str
    body: "Formula"


Formula = Union[Pred, Not, BinOp, Quant]

_GRAMMAR = r"""
?formula: quantified
        | biconditional

quantified: QUANT VAR quant_body

?quant_body: quantified
           | "(" formula ")"
           | negation

?biconditional: implication (IFF implication)*
?implication: xor_or (IMPLIES xor_or)*
?xor_or: conjunction ((OR conjunction) | (XOR conjunction))*
?conjunction: negation (AND negation)*
?negation: NOT negation
         | atom
?atom: quantified
     | equality
     | predicate
     | "(" formula ")"

equality: term "=" term

predicate: NAME "(" [term ("," term)*] ")"
         | NAME

?term: NAME
     | NUMBER

NUMBER: /-?\d+(\.\d+)?/
QUANT: "∀" | "∃"
NOT: "¬" | "~"
AND: "∧" | "&"
OR: "∨" | "|"
XOR: "⊕" | "xor"
IMPLIES: "→" | "->"
IFF: "↔" | "<->"
VAR: /[A-Za-z][A-Za-z0-9_]*(-[A-Za-z0-9][A-Za-z0-9_]*)*/
NAME: /[A-Za-z][A-Za-z0-9_]*(-[A-Za-z0-9][A-Za-z0-9_]*)*/

%import common.WS
%ignore WS
"""

CANONICAL_OPERATORS = {
    "→": "→", "->": "→",
    "↔": "↔", "<->": "↔",
    "∧": "∧", "&": "∧",
    "∨": "∨", "|": "∨",
    "⊕": "⊕", "xor": "⊕",
}


class _ToAST(Transformer):
    def quantified(self, items):
        quant_tok, var_tok, body = items
        return Quant(str(quant_tok), str(var_tok), body)

    def biconditional(self, items):
        return self._fold_binary_chain(items)

    def implication(self, items):
        return self._fold_binary_chain(items)

    def xor_or(self, items):
        return self._fold_binary_chain(items)

    def conjunction(self, items):
        return self._fold_binary_chain(items)

    @staticmethod
    def _fold_binary_chain(items):
        node = items[0]
        i = 1
        while i < len(items):
            op = CANONICAL_OPERATORS[str(items[i])]
            node = BinOp(op, node, items[i + 1])
            i += 2
        return node

    def negation(self, items):
        return Not(items[-1])

    def predicate(self, items):
        name = str(items[0])
        args = [str(t) for t in items[1:]]
        return Pred(name, args)

    def equality(self, items):
        left, right = items
        return Pred("=", [str(left), str(right)])


_parser = Lark(_GRAMMAR, start="formula", parser="earley", maybe_placeholders=False)


def parse_fol(text: str) -> Formula:
    tree = _parser.parse(text.strip())
    return _ToAST().transform(tree)


def is_numeric_literal(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False


def collect_signature(formula: Formula):
    preds: dict = {}
    consts: set = set()

    def walk(node: Formula, bound: frozenset):
        if isinstance(node, Pred):
            if node.name != "=":
                preds.setdefault(node.name, len(node.args))
            for arg in node.args:
                if arg not in bound and not is_numeric_literal(arg):
                    consts.add(arg)
        elif isinstance(node, Not):
            walk(node.expr, bound)
        elif isinstance(node, BinOp):
            walk(node.left, bound)
            walk(node.right, bound)
        elif isinstance(node, Quant):
            walk(node.body, bound | {node.var})
        else:
            raise TypeError(f"unknown formula node: {node!r}")

    walk(formula, frozenset())
    return preds, consts
