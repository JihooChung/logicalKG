import re
import requests

#####TEXT NORMALIZATION##### - skipped since sample is already normalized
'''
#title & abstract
pmid = "35768803"
url = f"https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson?pmids={pmid}"

#full text
#pmcids = "8316912"
#url = f"https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/pmc_export/biocjson?pmcids=PMC{pmcids}"


response = requests.get(url)

if response.status_code == 200:

    data = response.json()["PubTator3"][0]

    for passage in data.get("passages", []):
        section_type = passage["infons"].get("type", "text")
        original_text = passage["text"]
        annotations = passage.get("annotations", [])
        annotations = sorted(annotations, key=lambda x: len(x.get("text", "")), reverse=True)

        masked_text = original_text

        for ann in annotations:
            mention_text = ann.get("text", "")

            entity_type = ann["infons"].get("type", "Entity")
            entity_id = ann["infons"].get("identifier", "UNKNOWN")

            clean_id = str(entity_id).replace(":", "_").replace(" ", "_")
            replacement = f"{entity_type}_{clean_id}"

            try:
                masked_text = re.sub(r'\b' + re.escape(mention_text) + r'\b', replacement, masked_text)
            except Exception:
                masked_text = masked_text.replace(mention_text, replacement)

        print(f"{section_type.upper()}")
        print(f"Original Text: {original_text}")
        print(f"After Text Normalization: {masked_text}\n")
else:
    print(f"Error: {response.status_code}")

with open("logicalKG/sample/sample_save_example.txt", "w") as file:
    file.write(masked_text)
'''
####PROMPTING####

url = "https://chat-ai.academiccloud.de/v1/chat/completions"
api_key = '8333a36daa801574977831d75be754b1'
model = "gemma-4-31b-it"
#model = "medgemma-27b-it"


with open("logicalKG/drs_to_kg/oneshot_STRICT_prompt.txt", "r") as file:
    prompt = file.read()

SAMPLE_INDEX = 1

with open("logicalKG/sample/samples_STRICT_drs.txt", "r") as file:
    samples = {}
    current = None
    for line in file:
        if line.startswith("#Sample"):
            current = int(line.split(":")[0].replace("#Sample", ""))
            samples[current] = []
        elif current is not None:
            samples[current].append(line)
    sample = "".join(samples[SAMPLE_INDEX]).strip()


headers = {
    "Accept": "application/json",
    "Authorization": 'Bearer '+api_key,
    "Content-Type": "application/json",
    "inference-service": "saia-openai-gateway",
}

data = {
    "model": model,
    "messages": [
        {"role": "system", "content": prompt},
        {"role": "user", "content": sample},
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
    print(result["choices"][0]["message"]["content"].split("References:")[0].strip())

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP Error: {http_err}")
    print(f"{response.text}")
except Exception as err:
    print(f"Error: {err}")