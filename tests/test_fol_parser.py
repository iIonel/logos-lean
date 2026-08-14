from src.fol_parser import BinOp, Not, Pred, Quant, collect_signature, parse_fol


def test_simple_predicate():
    assert parse_fol("Man(socrates)") == Pred("Man", ["socrates"])


def test_zero_arity_predicate():
    assert parse_fol("Rains") == Pred("Rains", [])
    assert parse_fol("Rains()") == Pred("Rains", [])


def test_implication():
    ast = parse_fol("Man(socrates) → Mortal(socrates)")
    assert ast == BinOp("→", Pred("Man", ["socrates"]), Pred("Mortal", ["socrates"]))


def test_universal_syllogism():
    ast = parse_fol("∀x (Man(x) → Mortal(x))")
    assert ast == Quant("∀", "x", BinOp("→", Pred("Man", ["x"]), Pred("Mortal", ["x"])))


def test_negation_and_conjunction():
    ast = parse_fol("¬(Rains() ∧ Cold())")
    assert ast == Not(BinOp("∧", Pred("Rains", []), Pred("Cold", [])))


def test_ascii_fallback_operators():
    ast = parse_fol("∀x (Man(x) -> Mortal(x))")
    assert ast == Quant("∀", "x", BinOp("→", Pred("Man", ["x"]), Pred("Mortal", ["x"])))


def test_chained_quantifiers():
    ast = parse_fol("∀x ∃y (Loves(x, y))")
    assert ast == Quant("∀", "x", Quant("∃", "y", Pred("Loves", ["x", "y"])))


def test_collect_signature_distinguishes_bound_vars_from_constants():
    ast = parse_fol("∀x (Man(x) → Mortal(x))")
    preds, consts = collect_signature(ast)
    assert preds == {"Man": 1, "Mortal": 1}
    assert consts == set()


def test_collect_signature_finds_constants():
    ast = parse_fol("Man(socrates) → Mortal(socrates)")
    preds, consts = collect_signature(ast)
    assert preds == {"Man": 1, "Mortal": 1}
    assert consts == {"socrates"}
