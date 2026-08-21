import re

import requests

url = "https://chat-ai.academiccloud.de/v1/chat/completions"
api_key = '8333a36daa801574977831d75be754b1'
model = "gemma-4-31b-it"
EXIST_BATCH_SIZE = 5
RELATION_BATCH_SIZE = 2


with open("logicalKG/drs_to_kg/exist_prompt.txt", "r") as file:
    exist_prompt = file.read()

with open("logicalKG/drs_to_kg/relation_prompt.txt", "r") as file:
    relation_prompt = file.read()

SAMPLE_INDEX = 2
merged_output_path = f"logicalKG/drs_to_kg/sample_{SAMPLE_INDEX}_merged.ttl"

with open("logicalKG/sample/samples_STRICT_drs.txt", "r") as file:
    samples = {}
    current = None
    for line in file:
        if line.startswith("#Sample"):
            current = int(line.split(":")[0].replace("#Sample", ""))
            samples[current] = []
        elif current is not None:
            samples[current].append(line)
    sample_lines = [line.strip() for line in samples[SAMPLE_INDEX] if line.strip()]

exist_lines = [line for line in sample_lines if ",exist," in line]
relation_lines = [line for line in sample_lines if ",exist," not in line]


headers = {
    "Accept": "application/json",
    "Authorization": 'Bearer '+api_key,
    "Content-Type": "application/json",
    "inference-service": "saia-openai-gateway",
}

def rename_local_ids(ttl_text, sample_index, batch_type, batch_no):
    prefix = f"s{sample_index}{batch_type}{batch_no}"
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
    lines = []
    for line in ttl_text.splitlines():
        if re.fullmatch(r"-{3,}", line.strip()):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def run_batch(title, prompt, batch_sample, batch_type, batch_no):
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": batch_sample},
        ],
        "enable-tools": True,
        "arcana": {
            "id": "jihoo.chung01/lkg_ontology"
        },
        "temperature": 0.0,
        "top_p": 0.05,
    }

    response = None
    try:
        print(f"\n=== {title} ===")
        response = requests.post(url, headers=headers, json=data, timeout=300)
        response.raise_for_status()
        result = response.json()
        ttl_text = result["choices"][0]["message"]["content"].split("References:")[0].strip()
        ttl_text = clean_ttl_text(ttl_text)
        ttl_text = rename_local_ids(ttl_text, SAMPLE_INDEX, batch_type, batch_no)
        print(ttl_text)
        return ttl_text
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP Error: {http_err}")
        if response is not None:
            print(response.text)
    except Exception as err:
        print(f"Error: {err}")
    return None


merged_outputs = []

for start in range(0, len(exist_lines), EXIST_BATCH_SIZE):
    batch_lines = exist_lines[start:start + EXIST_BATCH_SIZE]
    batch_no = start // EXIST_BATCH_SIZE + 1
    total_batches = (len(exist_lines) + EXIST_BATCH_SIZE - 1) // EXIST_BATCH_SIZE
    ttl_text = run_batch(
        f"Exist Batch {batch_no}/{total_batches}",
        exist_prompt,
        "\n".join(batch_lines),
        "e",
        batch_no,
    )
    if ttl_text:
        merged_outputs.append(ttl_text)

for start in range(0, len(relation_lines), RELATION_BATCH_SIZE):
    batch_lines = relation_lines[start:start + RELATION_BATCH_SIZE]
    batch_no = start // RELATION_BATCH_SIZE + 1
    total_batches = (len(relation_lines) + RELATION_BATCH_SIZE - 1) // RELATION_BATCH_SIZE
    ttl_text = run_batch(
        f"Relation Batch {batch_no}/{total_batches}",
        relation_prompt,
        "\n".join(batch_lines),
        "r",
        batch_no,
    )
    if ttl_text:
        merged_outputs.append(ttl_text)

if merged_outputs:
    with open(merged_output_path, "w") as file:
        file.write("\n\n".join(merged_outputs))
    print(f"\nMerged TTL saved to: {merged_output_path}")