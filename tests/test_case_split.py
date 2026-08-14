from src.fol_parser import parse_fol
from src.verify.case_split import evaluate, find_countermodel, generate_case_split_tactic


def test_evaluate_implication():
    formula = parse_fol("P → Q")
    assert evaluate(formula, {"P": True, "Q": False}) is False
    assert evaluate(formula, {"P": False, "Q": False}) is True


def test_evaluate_negation_and_conjunction():
    formula = parse_fol("¬(P ∧ Q)")
    assert evaluate(formula, {"P": True, "Q": True}) is False
    assert evaluate(formula, {"P": True, "Q": False}) is True


def test_find_countermodel_none_for_valid_argument():
    premises = [parse_fol("P → Q"), parse_fol("P")]
    conclusion = parse_fol("Q")
    assert find_countermodel(premises, conclusion, ["P", "Q"]) is None


def test_find_countermodel_found_for_invalid_argument():
    premises = [parse_fol("P → Q"), parse_fol("Q")]
    conclusion = parse_fol("P")
    model = find_countermodel(premises, conclusion, ["P", "Q"])
    assert model == {"P": False, "Q": True}


def test_generate_case_split_tactic_covers_every_atom():
    tactic = generate_case_split_tactic(["P", "Q", "R"])
    assert tactic.count("by_cases") == 3
    assert "simp_all" in tactic


def test_generate_case_split_tactic_no_atoms():
    assert generate_case_split_tactic([]) == "simp_all"
