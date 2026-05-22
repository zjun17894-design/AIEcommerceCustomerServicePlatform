"""LoRA 微调 Qwen2.5-1.5B-Instruct — 用户偏好预测
依赖: pip install transformers peft datasets accelerate torch
"""

import json
import torch
from pathlib import Path
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)
from peft import LoraConfig, TaskType, get_peft_model


MODEL_PATH = "Qwen/Qwen2.5-1.5B-Instruct"
TRAIN_FILE = "data/training/train.jsonl"
OUTPUT_DIR = "output/lora-preference"


def load_jsonl(path: str) -> list[dict]:
    samples = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    return samples


def format_prompt(sample: dict) -> str:
    """构造 Qwen chat 格式 prompt"""
    return (
        f"<|im_start|>system\n"
        f"{sample['instruction']}<|im_end|>\n"
        f"<|im_start|>user\n"
        f"{sample['input']}<|im_end|>\n"
        f"<|im_start|>assistant\n"
        f"{sample['output']}<|im_end|>"
    )


def main():
    if not Path(TRAIN_FILE).exists():
        raise FileNotFoundError(f"Training data not found: {TRAIN_FILE}")

    samples = load_jsonl(TRAIN_FILE)
    print(f"Loaded {len(samples)} training samples")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )

    # LoRA 配置
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # 构造 dataset
    def tokenize_fn(examples):
        texts = [format_prompt(s) for s in examples["samples"]]
        return tokenizer(texts, truncation=True, max_length=1024, padding="max_length")

    raw_data = [{"samples": s} for s in samples]
    dataset = Dataset.from_list(raw_data)
    tokenized = dataset.map(
        lambda x: tokenize_fn(x),
        batched=True,
        remove_columns=dataset.column_names,
    )

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=5e-5,
        num_train_epochs=3,
        logging_steps=10,
        save_steps=100,
        lr_scheduler_type="cosine",
        bf16=torch.cuda.is_available(),
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True),
    )

    trainer.train()
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Model saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
