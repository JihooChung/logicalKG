import requests
import re
import pandas as pd
from pathlib import Path

url = "https://chat-ai.academiccloud.de/v1/chat/completions"

api_key_path = "./prompting/api_key.txt"
nl_list_path = "./data/nl/nl_list.csv"

model = "gemma-4-31b-it" # gemma-4-31b-it, qwen3-30b-a3b-instruct-2507
prompt_type = "oneshot" # zeroshot, oneshot
prompt_path = f"./prompting/nl_to_ace/{prompt_type}_prompt.txt"

out_path = Path(f"./prompting/nl_to_ace/results/{prompt_type}_{model}.csv")


df = pd.read_csv(nl_list_path)

with open(api_key_path, "r") as file:
    api_key = file.read().strip()

with open(prompt_path, "r") as file:
    prompt = file.read()

headers = {
        "Accept": "application/json",
        "Authorization": 'Bearer '+api_key,
        "Content-Type": "application/json",
        "inference-service": "saia-openai-gateway",
    }

def clean_ace_text(ace_text):
    ref_start = re.search(r"-{3,}", ace_text)
    if ref_start:
        ace_text = ace_text[:ref_start.start()]
    return ace_text.strip()

def run_convert(prompt, nl, abstract_id, results):
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": nl},
        ],
        "enable-tools": True,
        "arcana": {
            "id": "jihoo.chung01/ace_nutshell"
        },
        "temperature": 0.0,
        "top_p": 0.05,
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        clean_ace = clean_ace_text(result["choices"][0]["message"]["content"])

        results.append({
            "abstract_id": abstract_id,
            "ace": clean_ace,
        })
        return results

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP Error: {http_err}")
        print(f"{response.text}")

    except Exception as err:
        print(f"Error: {err}")
    return results
    

results = []

for index, row in df.iterrows():
    abstract_id = row["abstract_id"]

    nl = row["nl"]
    print(f"\n########## abstract_id={abstract_id} ##########")
    print("--------------------------------")

    if "\n" in nl: # for too long input, manual combination is required
        nl_list = nl.split("\n")
        for nl_item in nl_list:
            print("--------------------------------") 
            results = run_convert(prompt, nl_item, abstract_id, results)
        
    else:
        results = run_convert(prompt, nl, abstract_id, results)

pd.DataFrame(results).to_csv(out_path, index=False)