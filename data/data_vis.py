import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input_path", type=str, default="./data/data_list.csv")
parser.add_argument("--output_path", type=str, default="./data/entity_relation_counts.png")
args = parser.parse_args()

df = pd.read_csv(args.input_path)

x = df["abstract_id"].astype(str)
width = 0.36
idx = range(len(df))

entity_color = "#2F6FED"
relation_color = "#7EB6FF"

fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor("#F7F9FC")
ax.set_facecolor("#F7F9FC")

ax.bar(
    [i - width / 2 for i in idx],
    df["entities"],
    width=width,
    label="entities",
    color=entity_color,
    edgecolor="white",
    linewidth=0.8,
)
ax.bar(
    [i + width / 2 for i in idx],
    df["relations"],
    width=width,
    label="relations",
    color=relation_color,
    edgecolor="white",
    linewidth=0.8,
)

ax.set_xticks(list(idx))
ax.set_xticklabels(x, fontsize=12)
ax.set_xlabel("abstract_id", fontsize=13)
ax.set_ylabel("count", fontsize=13)
ax.set_title("Medical entities and relations per abstract", fontsize=15)
ax.tick_params(axis="y", labelsize=12)
ax.legend(frameon=False, fontsize=12)
ax.set_ylim(bottom=0)
ax.yaxis.grid(True, linestyle="--", alpha=0.35)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

out_path = Path(args.output_path)
fig.tight_layout()
fig.savefig(out_path, dpi=150)
plt.show()
print(f"Saved to {out_path}")
