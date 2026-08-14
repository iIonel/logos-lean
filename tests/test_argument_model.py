import pytest

from src.argument.formalize import parse_argument
from src.argument.model import UnsupportedArgumentError
from src.pipeline import FormalizationError


def test_parse_valid_propositional_argument():
    argument = parse_argument(["P → Q", "P"], "Q")
    assert len(argument.premises) == 2
    assert argument.conclusion is not None


def test_blank_premise_lines_are_skipped():
    argument = parse_argument(["P → Q", "", "  ", "P"], "Q")
    assert len(argument.premises) == 2


def test_no_premises_raises_formalization_error():
    with pytest.raises(FormalizationError):
        parse_argument([""], "Q")


def test_bad_fol_raises_formalization_error():
    with pytest.raises(FormalizationError):
        parse_argument(["this is not fol((("], "Q")


def test_quantifier_rejected():
    with pytest.raises(UnsupportedArgumentError):
        parse_argument(["∀x (Man(x) → Mortal(x))"], "Mortal(socrates)")


def test_predicate_with_args_rejected():
    with pytest.raises(UnsupportedArgumentError):
        parse_argument(["Man(socrates)"], "Mortal(socrates)")


def test_xor_rejected():
    with pytest.raises(UnsupportedArgumentError):
        parse_argument(["P xor Q"], "P")


def test_unsupported_argument_error_is_a_formalization_error():
    assert issubclass(UnsupportedArgumentError, FormalizationError)
