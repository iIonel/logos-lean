#!/usr/bin/env python
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data import build_unified_dataset  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data")
    parser.add_argument("--folio-repo", default="tasksource/folio")
    parser.add_argument("--malls-repo", default="yuan-yang/MALLS-v0")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset = build_unified_dataset(args.folio_repo, args.malls_repo)

    for split, ds in dataset.items():
        path = out_dir / f"{split}.jsonl"
        with path.open("w") as f:
            for row in ds:
                f.write(json.dumps({"nl": row["nl"], "fol": row["fol"]}, ensure_ascii=False) + "\n")
        print(f"{split}: {len(ds)} rows -> {path}")


if __name__ == "__main__":
    main()
