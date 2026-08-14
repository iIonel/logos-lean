from src.fol_parser import BinOp, Formula, Not, Pred, Quant, collect_signature, is_numeric_literal

INFIX_OPERATORS = {"∧": "∧", "∨": "∨", "→": "→", "↔": "↔"}

RESERVED_LEAN_IDENTIFIERS = {
    "True",
    "False",
    "Not",
    "And",
    "Or",
    "Eq",
    "Iff",
    "Exists",
    "Type",
    "Prop",
}


def sanitize_identifier(name: str) -> str:
    identifier = name.replace("-", "_")
    if identifier in RESERVED_LEAN_IDENTIFIERS:
        identifier += "_"
    return identifier


def _format_term(term: str) -> str:
    return term if is_numeric_literal(term) else sanitize_identifier(term)


def _format_predicate(node: Pred) -> str:
    if node.name == "=":
        left, right = node.args
        return f"{_format_term(left)} = {_format_term(right)}"
    name = sanitize_identifier(node.name)
    args = [_format_term(arg) for arg in node.args]
    return f"{name} " + " ".join(args) if args else name


def _negation_needs_parens(expr: Formula) -> bool:
    return isinstance(expr, Quant) or (isinstance(expr, Pred) and expr.name == "=")


def _format_negation(node: Not, render_pred) -> str:
    inner = _format(node.expr, render_pred)
    if _negation_needs_parens(node.expr):
        return f"¬({inner})"
    return f"¬{inner}"


def _format_xor(left: Formula, right: Formula, render_pred) -> str:
    return f"(Xor' ({_format(left, render_pred)}) ({_format(right, render_pred)}))"


def _format_binary_op(node: BinOp, render_pred) -> str:
    if node.op == "⊕":
        return _format_xor(node.left, node.right, render_pred)
    left = _format_operand(node.left, render_pred)
    right = _format_operand(node.right, render_pred)
    return f"({left} {INFIX_OPERATORS[node.op]} {right})"


def _format(node: Formula, render_pred=_format_predicate) -> str:
    if isinstance(node, Pred):
        return render_pred(node)
    if isinstance(node, Not):
        return _format_negation(node, render_pred)
    if isinstance(node, BinOp):
        return _format_binary_op(node, render_pred)
    if isinstance(node, Quant):
        return (
            f"{node.quantifier} {sanitize_identifier(node.var)}, {_format(node.body, render_pred)}"
        )
    raise TypeError(f"unknown formula node: {node!r}")


def _format_operand(node: Formula, render_pred) -> str:
    text = _format(node, render_pred)
    return f"({text})" if isinstance(node, Quant) else text


def format_formula(formula: Formula, render_pred=_format_predicate) -> str:
    return _format(formula, render_pred)


def emit_lean(formula: Formula, theorem_name: str = "formalized") -> str:
    preds, consts = collect_signature(formula)

    lines = ["variable (U : Type)"]
    for name, arity in sorted(preds.items()):
        ty = " → ".join(["U"] * arity + ["Prop"]) if arity > 0 else "Prop"
        lines.append(f"variable ({sanitize_identifier(name)} : {ty})")
    for const in sorted(consts):
        lines.append(f"variable ({sanitize_identifier(const)} : U)")

    lines.append("")
    lines.append(f"theorem {theorem_name} : {_format(formula)} := by sorry")
    return "\n".join(lines)
