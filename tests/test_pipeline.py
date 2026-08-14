import pytest

from src.pipeline import (
    FormalizationError,
    ModelNotAvailableError,
    formalize_fol,
    formalize_nl,
)


def test_formalize_fol_happy_path():
    result = formalize_fol("∀x (Man(x) → Mortal(x))", theorem_name="syllogism")

    assert result.fol == "∀x (Man(x) → Mortal(x))"
    assert "theorem syllogism : ∀ x, (Man x → Mortal x) := by sorry" in result.lean


def test_formalize_fol_invalid_input_raises_formalization_error():
    with pytest.raises(FormalizationError):
        formalize_fol("this is not valid FOL (((")


def test_formalize_nl_without_model_repo_raises_clear_error():
    with pytest.raises(ModelNotAvailableError):
        formalize_nl("some sentence", model_repo=None)
