import re
from pathlib import Path

import pandas as pd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input_path", type=str, default="./data/ace/ace_gen_manual.txt")
parser.add_argument("--output_path", type=str, default="./data/ace/ace_list.csv")
parser.add_argument("--data_list_path", type=str, default="./data/data_list.csv")
args = parser.parse_args()

manual_path = Path(args.input_path)
text = manual_path.read_text(encoding="utf-8")

rows = []
current_id = None
current_lines = []

def saving_ace():
    if current_id is None:
        return
    n_entities = 0
    n_relations = 0
    for ln in current_lines:
        if not ln.strip():
            continue
        if ln.rstrip().endswith("exists ."):
            n_entities += 1
        else:
            n_relations += 1
    rows.append({
        "abstract_id": current_id,
        "ace": "\n".join(current_lines),
        "entities": n_entities,
        "relations": n_relations,
    })

for line in text.splitlines():
    header = re.match(r"#abstract(\d+)\s*$", line.strip())
    if header:
        saving_ace()
        current_id = int(header.group(1))
        current_lines = []
        continue

    if current_id is not None and line.strip():
        current_lines.append(line.rstrip())

saving_ace()

ace_df = pd.DataFrame(rows)[["abstract_id", "ace"]]
ace_df.to_csv(args.output_path, index=False)

data_df = pd.read_csv(args.data_list_path)
counts = pd.DataFrame(rows).set_index("abstract_id")[["entities", "relations"]]
data_df = data_df.set_index("abstract_id")
data_df.update(counts)
data_df = data_df.reset_index()
data_df.to_csv(args.data_list_path, index=False)
