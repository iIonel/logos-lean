import sys
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gradio as gr
import yaml

from src.pipeline import (
    FormalizationError,
    ModelNotAvailableError,
    formalize_fol,
    formalize_nl,
)
from src.pipeline_argument import check_argument_fol

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"


def _load_hf_model_repo() -> Optional[str]:
    if not _CONFIG_PATH.exists():
        return None
    with _CONFIG_PATH.open() as f:
        return (yaml.safe_load(f) or {}).get("hf_model_repo")


def fol_to_lean(fol_text: str) -> str:
    if not fol_text.strip():
        return ""
    try:
        return formalize_fol(fol_text).lean
    except FormalizationError as e:
        return f"Parse error: {e}"


def nl_to_lean(nl_text: str) -> Tuple[str, str]:
    if not nl_text.strip():
        return "", ""
    model_repo = _load_hf_model_repo()
    try:
        result = formalize_nl(nl_text, model_repo=model_repo)
        return result.fol, result.lean
    except ModelNotAvailableError as e:
        return "", str(e)
    except FormalizationError as e:
        return "", f"Model generated invalid FOL: {e}"


def check_argument(premises_text: str, conclusion_text: str) -> Tuple[str, str, str]:
    if not premises_text.strip() or not conclusion_text.strip():
        return "", "", ""
    premise_lines = premises_text.strip().split("\n")
    try:
        result = check_argument_fol(premise_lines, conclusion_text)
    except FormalizationError as e:
        return f"## ERROR: {e}", "", ""
    return f"## {result.verdict.name}", result.lean_source, result.diagnostic


with gr.Blocks(title="logos-lean") as demo:
    gr.Markdown(
        "# logos-lean\n"
        "Formalizing logical/philosophical statements: natural language → "
        "first-order logic (FOL) → Lean4. See [examples/formalizations.md]("
        "https://github.com/iIonel/logos-lean/blob/main/examples/formalizations.md) "
        "for curated samples."
    )

    with gr.Tab("FOL → Lean"):
        gr.Markdown("Works now — deterministic stage, no trained model needed.")
        fol_input = gr.Textbox(
            label="FOL formula",
            placeholder="∀x (Man(x) → Mortal(x))",
            value="∀x (Man(x) → Mortal(x))",
        )
        fol_button = gr.Button("Formalize")
        fol_lean_output = gr.Code(label="Lean4")
        fol_button.click(fol_to_lean, inputs=fol_input, outputs=fol_lean_output)

    with gr.Tab("NL → FOL → Lean"):
        gr.Markdown(
            "Needs a trained NL→FOL model (see `src/train.py`, run on Kaggle) — "
            "shows an explanatory message until one is configured."
        )
        nl_input = gr.Textbox(
            label="Natural language statement",
            placeholder="All men are mortal.",
        )
        nl_button = gr.Button("Formalize")
        nl_fol_output = gr.Textbox(label="Generated FOL")
        nl_lean_output = gr.Code(label="Lean4")
        nl_button.click(nl_to_lean, inputs=nl_input, outputs=[nl_fol_output, nl_lean_output])

    with gr.Tab("Argument Checker"):
        gr.Markdown(
            "Give it premises + a conclusion (FOL, one propositional atom per "
            "predicate -- no `∀`/`∃` yet, see README) and get a **Lean-checked** "
            "verdict: VALID means Lean found a real proof; INVALID means Lean "
            "checked an explicit countermodel. Not a statistical guess -- a "
            "kernel-verified certificate either way."
        )
        premises_input = gr.Textbox(
            label="Premises (one FOL formula per line)",
            lines=4,
            placeholder="P → Q\nP",
            value="P → Q\nP",
        )
        conclusion_input = gr.Textbox(
            label="Conclusion (FOL)",
            placeholder="Q",
            value="Q",
        )
        argument_button = gr.Button("Check argument")
        verdict_output = gr.Markdown(label="Verdict")
        argument_lean_output = gr.Code(label="Lean4 certificate")
        diagnostic_output = gr.Textbox(label="Diagnostic", lines=3)
        argument_button.click(
            check_argument,
            inputs=[premises_input, conclusion_input],
            outputs=[verdict_output, argument_lean_output, diagnostic_output],
        )


if __name__ == "__main__":
    demo.launch()
