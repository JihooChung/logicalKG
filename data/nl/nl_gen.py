import re
import requests
import pandas as pd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input_path", type=str, default="./data/data_list.csv")
parser.add_argument("--output_path", type=str, default="./data/nl/nl_list.csv")
parser.add_argument("--entity_map_path", type=str, default="./data/nl/entity_dict.csv")
args = parser.parse_args()

def clean_entity_id(entity_type, identifier):
    identifier = str(identifier)

    if entity_type == "Variant":
        # Variant_GeneID_HGVS
        gene_id = re.search(r"CorrespondingGene:(\d+)", identifier)
        gene_id = gene_id.group(1)
        hgvs = re.search(r"HGVS:([^;]+)", identifier)
        hgvs = hgvs.group(1)
        return f"Variant_{gene_id}_{hgvs.replace('.', '')}"

    entity_id = identifier.replace(":", "_").replace(" ", "_")
    entity_id = entity_id.split("-")[0]
    if not entity_id:
        entity_id = "UNKNOWN"
    return f"{entity_type}_{entity_id}"

df = pd.read_csv(args.input_path)

nl_rows = []
entity_map_rows = []

for index, row in df.iterrows():

    pmid = row["pmid"]
    abstract_id = row["abstract_id"]
    entity_mentions = {}
    masked_nl = None

    url = f"https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson?pmids={pmid}"

    response = requests.get(url)

    if response.status_code == 200:

        data = response.json()["PubTator3"][0]

        for passage in data.get("passages", []):
            section_type = passage["infons"].get("type", "text")
            original_text = passage["text"]

            if section_type == "title":
                continue

            annotations = passage.get("annotations", [])
            annotations = sorted(annotations, key=lambda x: len(x.get("text", "")), reverse=True)

            masked_text = original_text

            for ann in annotations:
                mention_text = ann.get("text", "")
                entity_type = ann["infons"].get("type", "Entity")
                if entity_type == "Chromosome":
                    continue
                replacement = clean_entity_id(
                    entity_type, ann["infons"].get("identifier", "UNKNOWN")
                )

                if mention_text:
                    mentions = entity_mentions.setdefault(replacement, [])
                    if mention_text not in mentions:
                        mentions.append(mention_text)

                try:
                    masked_text = masked_text.replace(mention_text, replacement)

                except Exception:
                    masked_text = masked_text.replace(mention_text, replacement)

            if section_type == "abstract":
                masked_nl = masked_text

        nl_rows.append({
            "abstract_id": abstract_id,
            "nl": masked_nl,
        })

        for entity_id, mentions in entity_mentions.items():
            entity_map_rows.append({
                "abstract_id": abstract_id,
                "entity_id": entity_id,
                "mentions": "/".join(mentions),
            })

    else:
        print(f"Error: {response.status_code}")

pd.DataFrame(nl_rows).to_csv(args.output_path, index=False)
pd.DataFrame(entity_map_rows).to_csv(args.entity_map_path, index=False)