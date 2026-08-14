#!/usr/bin/env python
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import FormalizationError, ModelNotAvailableError, formalize_nl  # noqa: E402


def load_dataset(csv_path: Path, limit: int = None) -> list:
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows


def evaluate(model_repo: str, rows: list) -> list:
    results = []
    for row in rows:
        text, label = row["text"], row["label"]
        try:
            formalized = formalize_nl(text, model_repo=model_repo)
            results.append(
                {"text": text, "label": label, "parsed": True, "fol": formalized.fol, "error": ""}
            )
        except FormalizationError as e:
            results.append(
                {"text": text, "label": label, "parsed": False, "fol": "", "error": str(e)}
            )
    return results


def summarize(results: list) -> dict:
    by_label = defaultdict(lambda: {"total": 0, "parsed": 0})
    for r in results:
        stats = by_label[r["label"]]
        stats["total"] += 1
        stats["parsed"] += r["parsed"]
    return by_label


def main():
    parser = argparse.ArgumentParser(
        description="Run the NL->FOL model against the Logical Fallacy Counterfactual "
        "Dataset and report parse-success rate by label (valid vs fallacy). "
        "This is a behavior/error-analysis probe, not a FOL exact-match eval -- "
        "the dataset has no gold FOL, only a valid/fallacy label."
    )
    parser.add_argument("model_repo")
    parser.add_argument("--csv-path", default="data/contrastive_dataset.csv")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", default="results/fallacy_dataset_eval.csv")
    args = parser.parse_args()

    rows = load_dataset(Path(args.csv_path), args.limit)

    try:
        results = evaluate(args.model_repo, rows)
    except ModelNotAvailableError as e:
        print(f"error: {e}")
        sys.exit(1)

    for label, stats in sorted(summarize(results).items()):
        rate = stats["parsed"] / stats["total"]
        print(f"{label}: {stats['parsed']}/{stats['total']} parsed ({rate:.1%})")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "parsed", "fol", "error"])
        writer.writeheader()
        writer.writerows(results)
    print(f"per-example results written to {out_path}")


if __name__ == "__main__":
    main()
