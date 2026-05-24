import json
import re
import requests

#title & abstract
pmid = "34366606"
url = f"https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson?pmids={pmid}"
response = requests.get(url)

#full text
pmcids = "8316912"
url = f"https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/pmc_export/biocjson?pmcids=PMC{pmcids}"
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
