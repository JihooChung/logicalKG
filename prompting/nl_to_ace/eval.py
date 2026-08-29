from collections import Counter
from pathlib import Path
import re

import pandas as pd

gt_path = Path("./data/ace/ace_list.csv")
model = "gemma-4-31b-it" # gemma-4-31b-it, qwen3-30b-a3b-instruct-2507
prompt_type = "oneshot" # zeroshot, oneshot

pred_path = Path(f"./prompting/nl_to_ace/results/{prompt_type}_{model}.csv")
out_path = Path(f"./prompting/nl_to_ace/results/{prompt_type}_{model}_eval.csv")

# Symmetric ACE relations: A pred B == B pred A
SYMMETRIC = {
    "v:associate_with",
    "negatively v:correlate_with",
    "positively v:correlate_with",
    "v:be_compared_with",
    "v:cotreat_with",
    "v:interact_with",
    "v:interact_as_drug_with",
}

REL_RE = re.compile(
    r"^(p:\S+)\s+((?:(?:positively|negatively)\s+)?v:\S+)\s+(p:\S+)\s*\.\s*$"
)


def ace_lines(text):
    return [ln.strip() for ln in str(text).splitlines() if ln.strip()]


def normalize_line(line):
    m = REL_RE.match(line)
    if not m:
        return line
    left, pred, right = m.group(1), m.group(2), m.group(3)
    if pred not in SYMMETRIC:
        return line
    a, b = sorted([left, right])
    return f"{a} {pred} {b} ."


def score(gt_lines, pred_lines):
    gt_counts = Counter(normalize_line(line) for line in gt_lines)
    pred_counts = Counter(normalize_line(line) for line in pred_lines)
    tp = sum(min(gt_counts[line], pred_counts[line]) for line in gt_counts)
    fp = sum(pred_counts.values()) - tp
    fn = sum(gt_counts.values()) - tp
    return tp, fp, fn


def metrics(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    hallucination = fp / (tp + fp) if (tp + fp) else 0.0  # 1 - precision
    omission = fn / (tp + fn) if (tp + fn) else 0.0        # 1 - recall
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "hallucination": round(hallucination, 3),
        "omission": round(omission, 3),
    }


gt_df = pd.read_csv(gt_path)
pred_df = pd.read_csv(pred_path).set_index("abstract_id")

rows = []
for _, row in gt_df.iterrows():
    abstract_id = row["abstract_id"]
    gt_lines = ace_lines(row["ace"])
    pred_text = pred_df.loc[abstract_id, "ace"] if abstract_id in pred_df.index else ""
    pred_lines = ace_lines(pred_text)
    tp, fp, fn = score(gt_lines, pred_lines)
    rows.append({
        "abstract_id": abstract_id,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        **metrics(tp, fp, fn),
    })

total_tp = sum(r["tp"] for r in rows)
total_fp = sum(r["fp"] for r in rows)
total_fn = sum(r["fn"] for r in rows)
rows.append({
    "abstract_id": 0,
    "tp": total_tp,
    "fp": total_fp,
    "fn": total_fn,
    **metrics(total_tp, total_fp, total_fn),
})

pd.DataFrame(rows).to_csv(out_path, index=False)
print(f"Saved to {out_path}")
