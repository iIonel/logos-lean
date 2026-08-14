from dataclasses import dataclass
from typing import Optional

from src.fol_parser import parse_fol
from src.lean_emit import emit_lean


class FormalizationError(Exception):
    pass


class ModelNotAvailableError(Exception):
    pass


@dataclass
class FormalizationResult:
    fol: str
    lean: str


def formalize_fol(fol_text: str, theorem_name: str = "formalized") -> FormalizationResult:
    try:
        ast = parse_fol(fol_text)
    except Exception as e:
        raise FormalizationError(f"couldn't parse as FOL: {e}") from e
    lean = emit_lean(ast, theorem_name=theorem_name)
    return FormalizationResult(fol=fol_text.strip(), lean=lean)


_nl_to_fol_model = None


def _load_nl_to_fol_model(model_repo: str):
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_repo)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_repo)
    return tokenizer, model


def formalize_nl(
    nl_text: str, model_repo: Optional[str], theorem_name: str = "formalized"
) -> FormalizationResult:
    if not model_repo:
        raise ModelNotAvailableError(
            "no NL->FOL model configured yet -- train one with src/train.py on "
            "Kaggle, push it to the HF Hub, then set hf_model_repo in config/config.yaml"
        )

    global _nl_to_fol_model
    if _nl_to_fol_model is None or _nl_to_fol_model[0] != model_repo:
        tokenizer, model = _load_nl_to_fol_model(model_repo)
        _nl_to_fol_model = (model_repo, tokenizer, model)

    _, tokenizer, model = _nl_to_fol_model
    inputs = tokenizer(nl_text, return_tensors="pt", truncation=True)
    output_ids = model.generate(**inputs, max_new_tokens=256)
    fol_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return formalize_fol(fol_text, theorem_name=theorem_name)
