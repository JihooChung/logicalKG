## Archive
This folder contains earlier prompting drafts, sample conversions, and figures used in the main README. It is **not** part of the runnable pipeline (`data/` + `prompting/`).

We keep these files as a reference for **future work**: the FLEXIBLE prompts and samples show how the project could be scaled beyond the current ontology (more entity/relation types, freer ACE verbs). They are idea sketches, not the official experiment setup.

See the [project README](../readme.md) for how to run the current code.

## Contents

### `sample/`
One abstract taken through ACE → DRS → KG under the **FLEXIBLE** style (allowing to creat other types of entitied and relations besides the limited types from the current ontology).

- `abstract1_FLEXIBLE_ace.txt`
- `abstract1_FLEXIBLE_drs.txt`
- `abstract1_FLEXIBLE_kg.ttl`

### `nl_to_ace/` and `drs_to_kg/`
Early prompt wording and model outputs (FLEXIBLE / STRICT). Current prompts live in `prompting/nl_to_ace/` and `prompting/drs_to_kg/prompts/`.

### `visualization/`
Figures linked from the main README.

- `workflow.png` — pipeline overview
- `nltoace.png` — NL→ACE results (Table 1)
- `drstokg.png` — DRS→KG results (Table 2)
- `ontology_rule.png`, `entity_relation_counts.png` — extra plots

## Note
FLEXIBLE allowed `v:` verbs and `n:` nouns outside the ontology; STRICT kept only ontology predicates. The main experiments use the STRICT-style ACE/KG setup described in the project README.
