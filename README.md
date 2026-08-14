# logos-lean

![tests](https://github.com/iIonel/logos-lean/actions/workflows/tests.yml/badge.svg)
![license](https://img.shields.io/badge/license-MIT-blue)

Formalizing logical and philosophical statements: natural language → first-order logic (FOL) → Lean4.

## What it does

```
"All men are mortal."
        │
        │  (fine-tuned NL→FOL model, trained on Kaggle)
        ▼
"∀x (Man(x) → Mortal(x))"
        │
        │  (deterministic FOL→Lean compiler, no model)
        ▼
variable (U : Type)
variable (Man : U → Prop)
variable (Mortal : U → Prop)

theorem formalized : ∀ x, (Man x → Mortal x) := by sorry
```

The pipeline has two deliberately separate stages:

1. **NL → FOL** — a seq2seq model (`google/flan-t5-large`) fine-tuned on
   sentence/formula pairs from
   [FOLIO](https://huggingface.co/datasets/tasksource/folio) (expert-annotated
   logical/philosophical statements) and
   [MALLS](https://huggingface.co/datasets/yuan-yang/MALLS-v0) (34k synthetic
   pairs, for scale). This is the hard part — semantic understanding.
2. **FOL → Lean4** — *not* a model, a deterministic compiler
   (`src/fol_parser.py` + `src/lean_emit.py`, `lark` grammar). FOL syntax is
   regular, so a model would only hallucinate wrong parens/quantifiers where a
   hand-written parser is cheaper and more reliable — and, crucially,
   automatically checkable.

**Scope**: formalizing a single statement, not proving it — every generated
`theorem` ends in `:= by sorry`.

Stage 2 works *today*, with no trained model at all — see
[`examples/formalizations.md`](examples/formalizations.md) for a sample of
formalized philosophical statements.

## Argument Checker

A separate, newer capability: given **premises + a conclusion**, get a
**Lean-kernel-checked verdict** — not `sorry`, an actual proof or an actual
countermodel.

```
premises:    P → Q, P
conclusion:  Q
                │
                │  Python truth-table search decides VALID/INVALID (2^n, n = atoms)
                ▼
        VALID  →  Lean proof: exhaustive case-split (Classical.byCases per atom,
                  core Lean4 only, no Mathlib) closes every branch with simp_all
      INVALID  →  Lean proof: concrete existential witness — the exact
                  countermodel found, e.g. ⟨False, True⟩, closed by `decide`
                │
                ▼
        Lean actually compiles the certificate. If it doesn't, the verdict
        is ERROR, not a guess — Python's oracle is never trusted alone.
```

This is categorically different from NLP fallacy-classifiers: the output is
a kernel-checked proof term, not a model's opinion.

**Scope (Phase 1): propositional arguments only** — bare atoms (`P`, `Q`),
no `∀`/`∃`. Quantified FOL validity is undecidable in general, so a failed
proof attempt there wouldn't reliably mean "invalid" — that needs bounded
countermodel search, which is real follow-on work (see Roadmap). XOR (`⊕`)
is also rejected for now (would need Mathlib's `Xor'`, and Phase 1
deliberately has zero Mathlib dependency — see `src/verify/case_split.py`).

Input is FOL, not natural language, for the same reason as the "FOL → Lean"
tab above: the trained NL→FOL model only handles single statements, not
argument-level premise/conclusion decomposition (also on the Roadmap).

Code: `src/argument/` (parsing + scope guard) and `src/verify/` (the
decision procedure, Lean emission, verdict) — see Structure below. Golden-set
examples (modus ponens, disjunctive syllogism, affirming the consequent,
denying the antecedent) in `tests/test_verify_lean.py`.

**Requires a local Lean toolchain** (`elan` — https://github.com/leanprover/elan)
on `PATH`; without it the Argument Checker tab still works, it just can't
compile the certificate.

## Structure

```
logos-lean/
├── app/app.py              Gradio demo (3 tabs, see below)
├── src/
│   ├── fol_parser.py       FOL grammar (lark) → AST
│   ├── lean_emit.py        AST → Lean4 statement (single-formula, := by sorry)
│   ├── data.py              FOLIO + MALLS → unified {nl, fol} schema
│   ├── pipeline.py          formalize_fol (no model) + formalize_nl (with model)
│   ├── pipeline_argument.py check_argument_fol -- top-level Argument Checker entry
│   ├── lean_toolchain.py    subprocess wrapper around the real `lean` compiler
│   ├── train.py             fine-tuning on Kaggle (HF Trainer)
│   ├── evaluate.py          FOL exact-match + syntactic validity rate
│   ├── argument/            Argument model + propositional-scope guard
│   │   ├── model.py           Argument, assert_propositional
│   │   └── formalize.py       parse_argument: premises + conclusion -> Argument
│   └── verify/               the Argument Checker's core: decision + certificate
│       ├── case_split.py      truth-table oracle + case-split tactic generator
│       ├── emit_argument.py   Argument (+ verdict) -> Lean4 theorem source
│       └── verdict.py         orchestrates: decide, emit, compile, verdict
├── scripts/prepare_data.py  CLI: generates train/validation/test.jsonl
├── scripts/evaluate_fallacy_dataset.py  behavior probe on data/contrastive_dataset.csv
├── notebooks/kaggle_train.ipynb   thin Kaggle entry point
├── examples/formalizations.md     curated, verified examples
├── config/                 config.yaml (dev, CPU) / config.kaggle.yaml (GPU)
└── tests/                  unit tests (fast) + `lean`-marked tests (real compiles), run in CI
```

## Demo (Gradio)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app/app.py
```

Three tabs:
- **FOL → Lean** — works now, no model. Paste a FOL formula, get the Lean
  statement instantly.
- **NL → FOL → Lean** — needs a trained model (see below). Until
  `hf_model_repo` is configured, shows an explanatory message instead of
  crashing.
- **Argument Checker** — works now, no model, needs a local Lean toolchain
  (see below). Paste propositional premises + a conclusion, get a
  Lean-checked VALID/INVALID verdict plus the certificate proof.

## Training (on Kaggle)

The model (`flan-t5-large`) trains on Kaggle's free GPU (P100/T4, ~16GB VRAM)
— see `notebooks/kaggle_train.ipynb`, which clones the repo and runs:

```bash
python scripts/prepare_data.py
python src/train.py --config config/config.kaggle.yaml
python src/train.py --config config/config.kaggle.yaml --push-to-hub USER/logos-lean-flan-t5-large
```

`prepare_data.py` generates `data/{train,validation,test}.jsonl`; the first
`train.py` run fine-tunes locally; the second pushes the result to the HF
Hub.

After pushing, set `hf_model_repo: USER/logos-lean-flan-t5-large` in
`config/config.yaml` — the demo's "NL → FOL → Lean" tab activates
automatically.

Evaluation (FOL exact-match + syntactic validity rate, via
`src/fol_parser.py` — no Lean toolchain required):

```bash
python src/evaluate.py USER/logos-lean-flan-t5-large --test-path data/test.jsonl
```

### Behavior probe: does the model formalize valid arguments differently than fallacious ones?

`data/contrastive_dataset.csv` (not included in the repo — download from
[Kaggle](https://www.kaggle.com/datasets/navy007/logical-fallacy-counterfactual-dataset),
1406 short arguments, balanced `valid`/`fallacy` labels, informal fallacies
like ad hominem and hasty generalization) is a different kind of check than
`src/evaluate.py`: there's no gold FOL to score exact-match against, only a
label. The question isn't "did it translate correctly" but "does parse
success rate differ between valid and fallacious arguments" — informal
fallacies are outside what FOL can even represent, so this is a probe of the
pipeline's boundary, not a training signal.

```bash
python scripts/evaluate_fallacy_dataset.py USER/logos-lean-flan-t5-large
```

Prints parse-success rate per label and writes a per-example CSV (text,
label, parsed, generated FOL, error) to `results/fallacy_dataset_eval.csv`
for manual inspection.

## Development

```bash
pip install -r requirements-dev.txt
pytest -m "not lean"
pytest -m lean
ruff check .
black --check .
```

`pytest -m "not lean"` is the fast suite — no torch/transformers/Lean
needed. `pytest -m lean` runs the tests that actually invoke the Lean
compiler (marked `@pytest.mark.lean`, skip automatically if no toolchain is
found); it needs [elan](https://github.com/leanprover/elan) on `PATH`:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh
```

## Known limitations

- **Lean identifier collisions**: a FOL predicate named `Exists` or `True`
  would shadow Lean4's own core identifiers — `src/lean_emit.py` detects a
  (non-exhaustive) reserved-name list and appends `_`. See
  `examples/formalizations.md`.
- **⊕ (XOR)**: emitted as a prefix call to Mathlib's `Xor'`, not infix
  notation (Lean's `⊕` denotes the `Sum` type, not propositional XOR).
- **No real compile-check**: no Lean toolchain (`elan`/`lake`) is run here —
  generated statements haven't actually been compiled, only syntactically
  validated by the parser itself.
- **FOL grammar coverage**: empirically validated at 95.3% (FOLIO) / 99.9%
  (MALLS) against real dataset formulas — remaining cases are either dataset
  line-splitting artifacts or rare constructs (quoted strings, alphanumeric
  codes like "5G").

## Roadmap

- [ ] Deploy demo to HF Spaces
- [x] Real compile-check with `elan`/`lake` in CI (Argument Checker, `lean-tests` job)
- [x] Automated proof search for propositional arguments (Argument Checker, Phase 1)
- [ ] Argument Checker, Phase 2: quantified FOL (`∀`/`∃`) with bounded finite
      countermodel search — validity is undecidable in general, so this needs
      an honest "UNDETERMINED" verdict alongside VALID/INVALID, not just a
      tactic ladder
- [ ] Argument Checker: NL argument decomposition (split a paragraph into
      premises + conclusion) — the checker currently takes FOL input only
- [ ] Argument Checker: XOR (`⊕`) support (needs Mathlib's `Xor'`, currently
      rejected to keep Phase 1 dependency-free)
- [ ] Larger model (Mistral-7B + LoRA) as an alternative to Flan-T5-large

## License

MIT — see [LICENSE](LICENSE).
