from pathlib import Path

import pandas as pd
import requests
import re

url = "https://chat-ai.academiccloud.de/v1/chat/completions"

with open("./prompting/api_key.txt", "r") as file:
    api_key = file.read().strip()

EXIST_BATCH_SIZE = 5
RELATION_BATCH_SIZE = 2

df = pd.read_csv("./data/drs/drs_list.csv")

model = "gemma-4-31b-it"
prompt_type = "oneshot" # oneshot, zeroshot
out_path = Path(f"./prompting/drs_to_kg/results/{prompt_type}_{model}.csv")

with open(f"./prompting/drs_to_kg/{prompt_type}_exist_prompt.txt", "r") as file:
    exist_prompt = file.read()

with open(f"./prompting/drs_to_kg/{prompt_type}_relation_prompt.txt", "r") as file:
    relation_prompt = file.read()

headers = {
    "Accept": "application/json",
    "Authorization": "Bearer " + api_key,
    "Content-Type": "application/json",
    "inference-service": "saia-openai-gateway",
}

def rename_local_ids(ttl_text, abstract_id, batch_type, batch_no):
    prefix = f"a{abstract_id}{batch_type}{batch_no}"
    ttl_text = re.sub(
        r"\blkg:DRS_([A-Za-z0-9]+)\b",
        rf"lkg:DRS_{prefix}_\1",
        ttl_text,
    )
    ttl_text = re.sub(
        r"\blkg:STMT_([A-Za-z0-9]+)\b",
        rf"lkg:STMT_{prefix}_\1",
        ttl_text,
    )
    return ttl_text

def clean_ttl_text(ttl_text):
    ref_start = re.search(r"-{3,}", ttl_text)
    if ref_start:
        ttl_text = ttl_text[:ref_start.start()]
    return ttl_text.strip()

def run_batch(prompt, batch_sample, abstract_id, batch_type, batch_no):
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": batch_sample},
        ],
        "enable-tools": True,
        "arcana": {
            "id": "jihoo.chung01/lkg_ontology",
        },
        "temperature": 0.0,
        "top_p": 0.05,
    }

    response = None
    try:
        response = requests.post(url, headers=headers, json=data, timeout=300)
        response.raise_for_status()
        result = response.json()
        ttl_text = clean_ttl_text(result["choices"][0]["message"]["content"])
        ttl_text = rename_local_ids(ttl_text, abstract_id, batch_type, batch_no)
        return ttl_text
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP Error: {http_err}")
        if response is not None:
            print(response.text)
    except Exception as err:
        print(f"Error: {err}")
    return None

results = []

for index, row in df.iterrows():
    abstract_id = row["abstract_id"]
    drs_lines = [line.strip() for line in str(row["drs"]).splitlines() if line.strip()]
    exist_lines = [line for line in drs_lines if ",exist," in line]
    relation_lines = [line for line in drs_lines if ",exist," not in line]

    print(f"\n########## abstract_id={abstract_id} ##########")
    print("--------------------------------")

    merged_outputs = []

    for start in range(0, len(exist_lines), EXIST_BATCH_SIZE):
        batch_no = start // EXIST_BATCH_SIZE + 1
        total_batches = (len(exist_lines) + EXIST_BATCH_SIZE - 1) // EXIST_BATCH_SIZE
        print(f"Running exist batch {batch_no} of {total_batches}")
        batch_lines = exist_lines[start:start + EXIST_BATCH_SIZE]
        ttl_text = run_batch(exist_prompt, "\n".join(batch_lines), abstract_id, "e", batch_no)
        if ttl_text:
            merged_outputs.append(ttl_text)

    for start in range(0, len(relation_lines), RELATION_BATCH_SIZE):
        batch_no = start // RELATION_BATCH_SIZE + 1
        total_batches = (len(relation_lines) + RELATION_BATCH_SIZE - 1) // RELATION_BATCH_SIZE
        print(f"Running relation batch {batch_no} of {total_batches}")
        batch_lines = relation_lines[start:start + RELATION_BATCH_SIZE]
        ttl_text = run_batch(relation_prompt, "\n".join(batch_lines), abstract_id, "r", batch_no)
        if ttl_text:
            merged_outputs.append(ttl_text)

    results.append({
        "abstract_id": abstract_id,
        "kg": "\n\n".join(merged_outputs),
    })


pd.DataFrame(results).to_csv(out_path, index=False)
