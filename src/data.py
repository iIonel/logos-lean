from datasets import Dataset, DatasetDict, concatenate_datasets, load_dataset


def load_folio(repo_id: str = "tasksource/folio") -> dict:
    raw = load_dataset(repo_id)
    return {
        split: ds.map(
            lambda row: {"nl": row["conclusion"], "fol": row["conclusion-FOL"].strip()},
            remove_columns=ds.column_names,
        )
        for split, ds in raw.items()
    }


def load_malls(repo_id: str = "yuan-yang/MALLS-v0") -> dict:
    raw = load_dataset(repo_id)
    return {
        split: ds.map(
            lambda row: {"nl": row["NL"], "fol": row["FOL"].strip()},
            remove_columns=ds.column_names,
        )
        for split, ds in raw.items()
    }


def build_unified_dataset(
    folio_repo: str = "tasksource/folio", malls_repo: str = "yuan-yang/MALLS-v0"
) -> DatasetDict:
    folio = load_folio(folio_repo)
    malls = load_malls(malls_repo)

    train: Dataset = concatenate_datasets([folio["train"], malls["train"]]).shuffle(seed=42)
    validation: Dataset = folio["validation"]
    test: Dataset = malls["test"]

    return DatasetDict({"train": train, "validation": validation, "test": test})
