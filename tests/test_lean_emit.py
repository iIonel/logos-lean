from src.fol_parser import parse_fol
from src.lean_emit import emit_lean


def test_syllogism_emits_expected_lean():
    ast = parse_fol("∀x (Man(x) → Mortal(x))")
    lean = emit_lean(ast, theorem_name="socrates_syllogism")

    assert "variable (U : Type)" in lean
    assert "variable (Man : U → Prop)" in lean
    assert "variable (Mortal : U → Prop)" in lean
    assert "variable (x : U)" not in lean
    assert "theorem socrates_syllogism : ∀ x, (Man x → Mortal x) := by sorry" in lean


def test_constant_gets_declared():
    ast = parse_fol("Man(socrates) → Mortal(socrates)")
    lean = emit_lean(ast)

    assert "variable (socrates : U)" in lean
    assert "theorem formalized : (Man socrates → Mortal socrates) := by sorry" in lean


def test_xor_uses_prefix_form_with_parenthesized_args():
    ast = parse_fol("¬(Student(rina) ⊕ ¬AwareThatDrug(rina, caffeine))")
    lean = emit_lean(ast)

    assert "(Xor' (Student rina) (¬AwareThatDrug rina caffeine))" in lean


def test_predicate_named_like_lean_reserved_word_gets_renamed():
    ast = parse_fol("∀x (Exists(x) → ∃y (Explains(y, x)))")
    lean = emit_lean(ast)

    assert "variable (Exists_ : U → Prop)" in lean
    assert "variable (Exists :" not in lean
    assert "theorem formalized : ∀ x, (Exists_ x → (∃ y, Explains y x)) := by sorry" in lean


def test_zero_arity_predicate_is_prop():
    ast = parse_fol("¬(Rains ∧ Cold)")
    lean = emit_lean(ast)

    assert "variable (Rains : Prop)" in lean
    assert "variable (Cold : Prop)" in lean
    assert "theorem formalized : ¬(Rains ∧ Cold) := by sorry" in lean
