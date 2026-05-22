"""LoRA 微调模型评估 — 对比基座模型 Zero-shot vs LoRA 微调"""

import json
import time
import sys
from pathlib import Path

TEST_DATA = Path("data/training/test.jsonl")
MODEL_PATH = "Qwen/Qwen2.5-1.5B-Instruct"
LORA_PATH = "output/lora-preference"


def load_test_data(path: Path) -> list[dict]:
    samples = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    return samples


def evaluate_model(model, tokenizer, samples: list[dict], model_name: str) -> dict:
    import torch

    correct = 0
    total = 0
    true_accept = 0
    pred_accept_true = 0
    pred_accept_all = 0
    total_time = 0.0

    for sample in samples:
        prompt = f"{sample['instruction']}\n\n{sample['input']}"
        expected = sample["output"].strip().lower()

        inputs = tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        t0 = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=10,
                temperature=0.1,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        elapsed = time.time() - t0
        total_time += elapsed

        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        ).strip().lower()

        predicted = "reject"
        if "accept" in response:
            predicted = "accept"

        total += 1
        if predicted == expected:
            correct += 1

        if expected == "accept":
            true_accept += 1
        if predicted == "accept":
            pred_accept_all += 1
            if expected == "accept":
                pred_accept_true += 1

    accuracy = correct / total * 100
    precision = pred_accept_true / pred_accept_all * 100 if pred_accept_all > 0 else 0.0
    recall = pred_accept_true / true_accept * 100 if true_accept > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    avg_latency = total_time / total * 1000

    return {
        "model": model_name,
        "total": total,
        "accuracy": round(accuracy, 1),
        "precision": round(precision, 1),
        "recall": round(recall, 1),
        "f1": round(f1, 1),
        "avg_latency_ms": round(avg_latency, 1),
    }


def main():
    if not TEST_DATA.exists():
        print(f"ERROR: Test data not found at {TEST_DATA}")
        sys.exit(1)

    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    samples = load_test_data(TEST_DATA)
    print(f"Loaded {len(samples)} test samples")
    print(f"  accept: {sum(1 for s in samples if s['output']=='accept')}")
    print(f"  reject: {sum(1 for s in samples if s['output']=='reject')}")
    print()

    # ---------- 基线: 基座模型 Zero-shot ----------
    print("=== Baseline: Base Model (Zero-shot) ===")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
    )
    baseline_result = evaluate_model(model, tokenizer, samples, "Qwen2.5-1.5B (Zero-shot)")
    print(f"  Accuracy: {baseline_result['accuracy']}%")
    print(f"  F1: {baseline_result['f1']}%")
    print(f"  Avg Latency: {baseline_result['avg_latency_ms']}ms")

    del model
    import torch
    torch.cuda.empty_cache()

    # ---------- LoRA 微调 ----------
    print()
    print("=== LoRA Fine-tuned Model ===")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
    )
    lora_model = PeftModel.from_pretrained(base_model, LORA_PATH)
    lora_result = evaluate_model(lora_model, tokenizer, samples, "Qwen2.5-1.5B (LoRA)")
    print(f"  Accuracy: {lora_result['accuracy']}%")
    print(f"  F1: {lora_result['f1']}%")
    print(f"  Avg Latency: {lora_result['avg_latency_ms']}ms")

    # ---------- 汇总对比 ----------
    print()
    print("=" * 55)
    print(f"{'指标':<20} {'基线 (Zero-shot)':<18} {'LoRA 微调':<18} {'变化'}")
    print("-" * 55)
    acc_diff = lora_result['accuracy'] - baseline_result['accuracy']
    f1_diff = lora_result['f1'] - baseline_result['f1']
    print(f"{'Accuracy':<20} {baseline_result['accuracy']:<18}% {lora_result['accuracy']:<18}% +{acc_diff:.1f}pp")
    print(f"{'F1':<20} {baseline_result['f1']:<18}% {lora_result['f1']:<18}% +{f1_diff:.1f}pp")
    print(f"{'Avg Latency':<20} {baseline_result['avg_latency_ms']:<18}ms {lora_result['avg_latency_ms']:<18}ms")
    print("=" * 55)


if __name__ == "__main__":
    main()
