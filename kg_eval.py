from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDF

LKG = Namespace("http://example.org/lkg#")
DRSBOX = LKG.DRSBox
CONTAINS_ENTITY = LKG.containsEntity
CONTAINS_STATEMENT = LKG.containsStatement
SYMMETRIC_PREDICATES = {
    LKG.associate,
    LKG.negativeCorrelate,
    LKG.positiveCorrelate,
    LKG.compare,
    LKG.cotreat,
    LKG.interact,
    LKG.drugInteract,
}

def term_format(g, term):
    return g.qname(term) if isinstance(term, URIRef) else str(term)


def normalize_statement(subject, predicate, obj):
    if predicate in SYMMETRIC_PREDICATES:
        return (frozenset({subject, obj}), predicate)
    return (subject, predicate, obj)


def build_stmt_chunk(box, stmt, triples):
    subject = predicate = obj = None

    for t_subj, t_pred, t_obj in triples:
        if t_subj != stmt:
            continue
        if t_pred == RDF.subject:
            subject = t_obj
        elif t_pred == RDF.predicate:
            predicate = t_obj
        elif t_pred == RDF.object:
            obj = t_obj

    if subject is None or predicate is None or obj is None:
        return None

    entities = frozenset({subject, obj})
    stmt_triples = {
        (t_subj, t_pred, t_obj)
        for t_subj, t_pred, t_obj in triples
        if t_subj == stmt
    }
    return {
        "box": box,
        "stmt": stmt,
        "key": (
            "stmt",
            entities,
            normalize_statement(subject, predicate, obj),
        ),
        "entities": entities,
        "statement": (subject, predicate, obj),
        "stmt_triples": stmt_triples,
        "triples": {
            (box, RDF.type, DRSBOX),
            (box, CONTAINS_ENTITY, subject),
            (box, CONTAINS_ENTITY, obj),
            (box, CONTAINS_STATEMENT, stmt),
            *stmt_triples,
        },
    }


def extract_chunks(triples):
    boxes = {
        subj for subj, pred, obj in triples
        if pred == RDF.type and obj == DRSBOX
    }
    box_entities = {box: [] for box in boxes}
    box_statements = {box: [] for box in boxes}

    for subj, pred, obj in triples:
        if subj not in boxes:
            continue
        if pred == CONTAINS_ENTITY:
            box_entities[subj].append(obj)
        elif pred == CONTAINS_STATEMENT:
            box_statements[subj].append(obj)

    exist_chunks = []
    stmt_chunks = []

    for box in boxes:
        entities = box_entities[box]
        statements = box_statements[box]

        if len(entities) == 1 and len(statements) == 0:
            entity = entities[0]
            exist_chunks.append({
                "key": ("exist", entity),
                "triples": {
                    (box, RDF.type, DRSBOX),
                    (box, CONTAINS_ENTITY, entity),
                },
            })
        elif len(statements) >= 1:
            is_megabox = len(statements) > 1
            for stmt in statements:
                stmt_chunk = build_stmt_chunk(box, stmt, triples)
                if stmt_chunk is not None:
                    stmt_chunk["is_megabox"] = is_megabox
                    stmt_chunks.append(stmt_chunk)

    return exist_chunks, stmt_chunks


def match_exist_chunks(output_chunks, gt_chunks, tp_triples):
    gt_pool = list(gt_chunks)
    for out_chunk in output_chunks:
        for i, gt_chunk in enumerate(gt_pool):
            if out_chunk["key"] == gt_chunk["key"]:
                tp_triples.update(out_chunk["triples"])
                gt_pool.pop(i)
                break


def find_stmt_gt_match(out_chunk, gt_pool):
    for i, gt_chunk in enumerate(gt_pool):
        if out_chunk["key"] == gt_chunk["key"]:
            return i, True
        if out_chunk["entities"] == gt_chunk["entities"]:
            return i, False
    return None, None


def apply_stmt_match(out_chunk, gt_chunk, tp_triples, full_match, scored_triples=None):
    scored_triples = out_chunk["triples"] if scored_triples is None else scored_triples

    if full_match:
        tp_triples.update(scored_triples)
        return

    gt_subj, gt_pred, gt_obj = gt_chunk["statement"]
    out_subj, out_pred, out_obj = out_chunk["statement"]

    for triple in scored_triples:
        subj, pred, obj = triple
        if pred == RDF.predicate:
            if obj == gt_pred:
                tp_triples.add(triple)
        elif pred == RDF.subject:
            if obj == gt_subj or (
                gt_pred in SYMMETRIC_PREDICATES
                and obj == gt_obj
                and out_subj == gt_obj
                and out_obj == gt_subj
            ):
                tp_triples.add(triple)
        elif pred == RDF.object:
            if obj == gt_obj or (
                gt_pred in SYMMETRIC_PREDICATES
                and obj == gt_subj
                and out_subj == gt_obj
                and out_obj == gt_subj
            ):
                tp_triples.add(triple)
        elif subj == out_chunk["stmt"] and pred == RDF.type:
            tp_triples.add(triple)
        elif subj == out_chunk["box"]:
            tp_triples.add(triple)


def match_stmt_chunks(output_chunks, gt_chunks, tp_triples):
    gt_pool = list(gt_chunks)
    normal_chunks = [chunk for chunk in output_chunks if not chunk["is_megabox"]]
    megabox_chunks = [chunk for chunk in output_chunks if chunk["is_megabox"]]

    for out_chunk in normal_chunks:
        matched_index, full_match = find_stmt_gt_match(out_chunk, gt_pool)
        if matched_index is None:
            continue
        gt_chunk = gt_pool.pop(matched_index)
        apply_stmt_match(out_chunk, gt_chunk, tp_triples, full_match)

    megabox_groups = {}
    for chunk in megabox_chunks:
        megabox_groups.setdefault(chunk["box"], []).append(chunk)

    for chunks in megabox_groups.values():
        chunks.sort(key=lambda chunk: str(chunk["stmt"]))
        box_winner = None

        for out_chunk in chunks:
            matched_index, full_match = find_stmt_gt_match(out_chunk, gt_pool)
            if matched_index is None:
                continue
            gt_chunk = gt_pool.pop(matched_index)
            apply_stmt_match(out_chunk, gt_chunk, tp_triples, full_match)
            box_winner = out_chunk
            break

        for out_chunk in chunks:
            if out_chunk is box_winner:
                continue
            matched_index, full_match = find_stmt_gt_match(out_chunk, gt_pool)
            if matched_index is None:
                continue
            gt_chunk = gt_pool.pop(matched_index)
            apply_stmt_match(
                out_chunk,
                gt_chunk,
                tp_triples,
                full_match,
                scored_triples=out_chunk["stmt_triples"],
            )

MODEL_NAME = "gemma-4-31b-it"
MODEL_NAME = "medgemma-27b-it"
PROMPT = "oneshot"
#PROMPT = "zeroshot" #currently not working
MED_ENTITY_TYPES = {"lkg:Disease", "lkg:Chemical", "lkg:Gene", "lkg:CellLine", "lkg:Variant", "lkg:Species"}

ontology_path = "logicalKG/ttl_files/ontology.ttl"
ground_truth_path = "logicalKG/sample/samples_STRICT_kg_each_sample.ttl"
output_path = "logicalKG/drs_to_kg/"+PROMPT+"_STRICT_results.txt"

with open(ontology_path, "r") as file:
    ontology = file.read()

with open(ground_truth_path, "r") as file:
    gt_samples = {}
    current = None
    for line in file:
        if line.strip() == "":
            continue
        if "SAMPLE" in line.upper():
            current = int(line.strip().split("SAMPLE")[-1])
            gt_samples[current] = []
        elif current is not None:
            gt_samples[current].append(line)


with open(output_path, "r") as file:
    output_samples = {}
    in_model = False
    current = None
    for line in file:
        stripped = line.strip()
        if stripped == "":
            continue
        if stripped.startswith("=") and MODEL_NAME in stripped:
            in_model = True
            current = None
            continue
        if in_model and stripped.startswith("="):
            break
        if not in_model:
            continue
        if "SAMPLE" in stripped.upper():
            current = int(stripped.split("SAMPLE")[-1])
            output_samples[current] = []
        elif current is not None:
            output_samples[current].append(line)


sample_results = []
total_tp = 0
total_gt = 0
total_output = 0

for i in range(3):
    SAMPLE_INDEX = i + 1

    gt_complete = ontology + "\n".join(gt_samples[SAMPLE_INDEX])
    output_complete = ontology + "\n".join(output_samples[SAMPLE_INDEX])

    ontology_graph = Graph()
    gt_graph = Graph()
    output_graph = Graph()

    ontology_graph.parse(data=ontology, format="turtle")
    gt_graph.parse(data=gt_complete, format="turtle")
    output_graph.parse(data=output_complete, format="turtle")

    gt_instance_triples = set(gt_graph) - set(ontology_graph)
    output_instance_triples = set(output_graph) - set(ontology_graph)

    tp_triples = set()

    output_exist_chunks, output_stmt_chunks = extract_chunks(output_instance_triples)
    gt_exist_chunks, gt_stmt_chunks = extract_chunks(gt_instance_triples)
    match_exist_chunks(output_exist_chunks, gt_exist_chunks, tp_triples)
    match_stmt_chunks(output_stmt_chunks, gt_stmt_chunks, tp_triples)

    for subj, pred, obj in output_instance_triples:
        if (subj, pred, obj) in tp_triples:
            continue
        if pred == RDF.type and term_format(output_graph, obj) in MED_ENTITY_TYPES:
            if (subj, pred, obj) in gt_instance_triples:
                tp_triples.add((subj, pred, obj))

    tp = len(tp_triples)
    gt_count = len(gt_instance_triples)
    output_count = len(output_instance_triples)
    fp = output_count - tp
    fn = gt_count - tp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    sample_results.append({
        "sample": SAMPLE_INDEX,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "gt": gt_count,
        "output": output_count,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    })

    total_tp += tp
    total_gt += gt_count
    total_output += output_count

    print(f"Sample{SAMPLE_INDEX} TP + FN: {gt_count}")
    print(f"Sample{SAMPLE_INDEX} TP + FP: {output_count}")
    print(f"Sample{SAMPLE_INDEX} TP: {tp} | FP: {fp} | FN: {fn}")
    print(f"Sample{SAMPLE_INDEX} Precision: {precision:.3f} | Recall: {recall:.3f} | F1: {f1:.3f}")

total_fp = total_output - total_tp
total_fn = total_gt - total_tp
overall_precision = total_tp / (total_tp + total_fp) if total_tp + total_fp else 0.0
overall_recall = total_tp / (total_tp + total_fn) if total_tp + total_fn else 0.0
overall_f1 = (
    2 * overall_precision * overall_recall / (overall_precision + overall_recall)
    if overall_precision + overall_recall else 0.0
)

print(f"\n[Overall] {MODEL_NAME} | {PROMPT}")
print(f"TP: {total_tp} | FP: {total_fp} | FN: {total_fn}")
print(f"GT triples: {total_gt} | Output triples: {total_output}")
print(f"Precision: {overall_precision:.3f}")
print(f"Recall: {overall_recall:.3f}")
print(f"F1: {overall_f1:.3f}")
