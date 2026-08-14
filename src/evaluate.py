#!/usr/bin/env python
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from src.fol_parser import parse_fol


def evaluate(model_repo: str, test_path: Path, limit: int = None) -> dict:
    tokenizer = AutoTokenizer.from_pretrained(model_repo)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_repo)

    rows = [json.loads(line) for line in test_path.open()]
    if limit:
        rows = rows[:limit]

    exact = 0
    valid = 0
    for row in rows:
        inputs = tokenizer(row["nl"], return_tensors="pt", truncation=True)
        output_ids = model.generate(**inputs, max_new_tokens=256)
        pred = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
        if pred == row["fol"].strip():
            exact += 1
        try:
            parse_fol(pred)
            valid += 1
        except Exception:
            pass

    n = len(rows)
    return {"n": n, "exact_match": exact / n, "parses_ok": valid / n}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model_repo")
    parser.add_argument("--test-path", default="data/test.jsonl")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    metrics = evaluate(args.model_repo, Path(args.test_path), args.limit)
    for key, value in metrics.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
