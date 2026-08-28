import re
import pandas as pd

PREDICATE_MAP = {
    "associate_with": "associate",
    "be_compared_with": "compare",
    "cotreat_with": "cotreat",
    "interact_with": "interact",
    "interact_as_drug_with": "drugInteract",
    "cause": "cause",
    "inhibit": "inhibit",
    "treat": "treat",
    "stimulate": "stimulate",
    "prevent": "prevent",
}

def kg_gen_exist(entity, box):
    entity_type = entity.split("_")[0]
    return (
            f"lkg:{entity} rdf:type lkg:{entity_type} .\n"
            f"lkg:box_{box} rdf:type lkg:DRSBox ;\n"
            f"lkg:containsEntity lkg:{entity} ."
        )

def kg_gen_medrelation(entity1, entity2, medrelation, box):
    return (
            f"lkg:box_{box} rdf:type lkg:DRSBox ;\n"
            f"lkg:containsEntity lkg:{entity1} , lkg:{entity2} ;\n"
            f"lkg:containsStatement lkg:stmt_{box} .\n"
            f"lkg:stmt_{box} rdf:type rdf:Statement ;\n"
            f"rdf:subject lkg:{entity1} ;\n"
            f"rdf:predicate lkg:{medrelation} ;\n"
            f"rdf:object lkg:{entity2} ."
        )

def kg_gen_per_drs(drs_line, box_id):
    named_ids = re.findall(r"named\(([^)]+)\)", drs_line)
    pred_match = re.search(r"predicate\([^,]+,([^,]+),", drs_line)
    box = f"{box_id:03d}"

    if not pred_match:
        return f"No Matching: {drs_line}"

    pred = pred_match.group(1)

    if pred == "exist":
        return kg_gen_exist(named_ids[0], box)

    if pred == "correlate_with":
        if "positively" in drs_line:
            medrelation = "positiveCorrelate"
        elif "negatively" in drs_line:
            medrelation = "negativeCorrelate"
        else:
            return f"No Matching: {drs_line}"
        return kg_gen_medrelation(named_ids[0], named_ids[1], medrelation, box)

    medrelation = PREDICATE_MAP.get(pred)
    if medrelation is None:
        return f"No Matching: {drs_line}"
    return kg_gen_medrelation(named_ids[0], named_ids[1], medrelation, box)

df = pd.read_csv("./data/drs/drs_list.csv")

kg_rows = []

for index, row in df.iterrows():
    abstract_id = row["abstract_id"]
    drs = row["drs"]
    kg = []

    box_id = 0
    for line in drs.splitlines():
        if not line.strip():
            continue
        box_id += 1
        kg.append(kg_gen_per_drs(line, box_id))
    
    kg_rows.append({
        "abstract_id": abstract_id,
        "kg": "\n".join(kg),
    })

pd.DataFrame(kg_rows).to_csv("./data/kg/kg_list.csv", index=False)