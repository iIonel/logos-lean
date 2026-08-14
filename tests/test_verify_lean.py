import pytest

from src.lean_toolchain import is_lean_available
from src.pipeline_argument import check_argument_fol
from src.verify.verdict import Verdict

pytestmark = [
    pytest.mark.lean,
    pytest.mark.skipif(not is_lean_available(), reason="no local Lean toolchain (elan) on PATH"),
]


@pytest.mark.parametrize(
    "premises,conclusion,expected",
    [
        pytest.param(["P → Q", "P"], "Q", Verdict.VALID, id="modus_ponens"),
        pytest.param(["P ∨ Q", "¬P"], "Q", Verdict.VALID, id="disjunctive_syllogism"),
        pytest.param(["P → Q", "Q"], "P", Verdict.INVALID, id="affirming_the_consequent"),
        pytest.param(["P → Q", "¬P"], "¬Q", Verdict.INVALID, id="denying_the_antecedent"),
    ],
)
def test_golden_set_verdicts(premises, conclusion, expected):
    result = check_argument_fol(premises, conclusion, theorem_name="t")
    assert result.verdict == expected, result.diagnostic


def test_valid_verdict_has_no_countermodel():
    result = check_argument_fol(["P → Q", "P"], "Q", theorem_name="t")
    assert result.countermodel is None


def test_invalid_verdict_reports_countermodel():
    result = check_argument_fol(["P → Q", "Q"], "P", theorem_name="t")
    assert result.countermodel == {"P": False, "Q": True}
