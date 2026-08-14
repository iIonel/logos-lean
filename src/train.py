#!/usr/bin/env python
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
from datasets import load_dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)


def _hf_token_from_dotenv() -> str:
    try:
        from dotenv import load_dotenv

        load_dotenv()
        return os.environ.get("HF_TOKEN")
    except ImportError:
        return None


def _hf_token_from_kaggle_secrets() -> str:
    try:
        from kaggle_secrets import UserSecretsClient

        return UserSecretsClient().get_secret("HF_TOKEN")
    except Exception:
        return None


def login_to_hf_hub() -> None:
    token = _hf_token_from_dotenv() or _hf_token_from_kaggle_secrets()
    if token:
        from huggingface_hub import login

        login(token=token)


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_split(data_dir: Path, split: str, subset_size):
    ds = load_dataset("json", data_files=str(data_dir / f"{split}.jsonl"))["train"]
    if subset_size:
        ds = ds.select(range(min(subset_size, len(ds))))
    return ds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--push-to-hub", default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    data_dir = Path(args.data_dir)

    tokenizer = AutoTokenizer.from_pretrained(config["model_name"])
    model = AutoModelForSeq2SeqLM.from_pretrained(config["model_name"])

    def preprocess(batch):
        inputs = tokenizer(batch["nl"], max_length=config["max_source_length"], truncation=True)
        labels = tokenizer(
            text_target=batch["fol"], max_length=config["max_target_length"], truncation=True
        )
        inputs["labels"] = labels["input_ids"]
        return inputs

    train_ds = load_split(data_dir, "train", config.get("train_subset_size"))
    eval_ds = load_split(data_dir, "validation", config.get("eval_subset_size"))

    train_ds = train_ds.map(preprocess, batched=True, remove_columns=train_ds.column_names)
    eval_ds = eval_ds.map(preprocess, batched=True, remove_columns=eval_ds.column_names)

    training_args = Seq2SeqTrainingArguments(
        output_dir=config["output_dir"],
        per_device_train_batch_size=config["per_device_train_batch_size"],
        per_device_eval_batch_size=config["per_device_eval_batch_size"],
        gradient_accumulation_steps=config.get("gradient_accumulation_steps", 1),
        num_train_epochs=config["num_train_epochs"],
        learning_rate=config["learning_rate"],
        logging_steps=config["logging_steps"],
        save_strategy=config.get("save_strategy", "epoch"),
        eval_strategy=config.get("eval_strategy", "epoch"),
        fp16=config.get("fp16", False),
        predict_with_generate=True,
        report_to=[],
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        processing_class=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
    )

    trainer.train()
    trainer.save_model(config["output_dir"])
    tokenizer.save_pretrained(config["output_dir"])

    if args.push_to_hub:
        login_to_hf_hub()
        model.push_to_hub(args.push_to_hub)
        tokenizer.push_to_hub(args.push_to_hub)
        print(f"Pushed to https://huggingface.co/{args.push_to_hub}")
        print(f"Set hf_model_repo: {args.push_to_hub} in config/config.yaml to activate the demo.")


if __name__ == "__main__":
    main()
