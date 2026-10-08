- Id: cvxbbu
- Status: done
- Graduated-To: cvxbbu
- Blocks-Release: next
- Set: cvxbbu
- Priority: medium
- Work-Kind: bug
- Summary: The research tree has no checker rule for an unsafe descriptive front-matter field, so a hand-edited or legacy over-bound or ANSI-bearing summary passes aw check research and reaches a terminal raw; three committed summaries already exceed the 300-char bound

## Workflow history
- 2026-10-08 done (aw backlog): closed by aw agy run: IPD xnogdl executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-cvxbbu-01-xnogdl-give-the-research-checker-the-unsafe-descriptive-field-rule.ipd.md); evidence .aw/records/plans/executed/20261002-cvxbbu-01-xnogdl-give-the-research-checker-the-unsafe-descriptive-field-rule.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: xnogdl
- 2026-10-01 created (aw backlog): The research tree has no checker rule for an unsafe descriptive front-matter field, so a hand-edited or legacy over-bound or ANSI-bearing summary passes aw check research and reaches a terminal raw; three committed summaries already exceed the 300-char bound

FILED AS THE CARRIER for the checker-half row in plan `deftzy` (Set `7w6zsl`), which closes the research WRITE paths only. This is the research-tree twin of `ynhst5`, which does the same for specs and releases.

MEASURED 2026-10-01 in a lane at HEAD `9e813570a`, against temporary fixture repositories.

`research_contract.validate_frontmatter` applies NO output-safety predicate to any field. It checks `id` against an id6 shape, `created` against `YYYYMMDD`, `order` against `NN`, `topic`/`consumed-by` for list-ness, and `model`/`kind`/`status`/`outcome`/`priority` against their vocabularies, and judges `summary` for nothing at all beyond presence. So an over-length or control-character-bearing descriptive field is unchecked at BOTH the checker and (until `deftzy` lands) the write path.

DRIVEN: a research doc whose `summary:` is `red<ESC>[31mINJECTED<ESC>[0m` passes `validate_frontmatter` (`[]`), passes `aw check research --agent` (`"outcome":"conforms"`, its one finding the unrelated pre-existing `check.collisions-not-checked`), and passes `aw research index --check` (exit 0). The raw bytes then reach a human three ways: `aw attention --details --no-color` prints `summary: red<ESC>[31mINJECTED<ESC>[0m`, `aw attention --format json` emits `"detail_text": "red\u001b[31mINJECTED\u001b[0m"` while reporting no violation for it, and `aw research index` WRITES THOSE BYTES INTO THE COMMITTED `INDEX.md` (2 ESC bytes in the generated file). A 900-character summary likewise passes every gate. Spec `attention-registry-and-cross-tree-status` Section 8.8 says "the renderers never emit raw control characters", so this is a live violation of an implemented contract.

THE EXISTING POPULATION CONSTRAINS THE FIX AND NEEDS A GRANDFATHERING DECISION. Measured over every parsable `summary:` in `.aw/records/research/**/*.md`: n=124, **3 exceed the 300-character bound** (320 in `20260905-awmetastore-06-g5f3zq-...gemini31prodeepthink.research-report.md`, 351 in `20260905-awmetastore-05-6mye7n-...reconciliation-report.md`, 395 in `20260905-hostskill-04-6asl6q-...reconciliation-report.md`), all three control-char-free; median 108. Every `topic` token is within bound (max 25) and every `consumed-by` token is (max 6). So the choice is to repair three records or to add a grandfather tier, which is a decision this item's eventual plan must make explicitly; `ynhst5` chose repair for its two specs-tree equivalents and that precedent is worth following unless a reason not to appears.

NOTE PRECISELY WHAT A CHECKER RULE CANNOT DO, so this item is not mistaken for a superset of `deftzy`: it closes over-length and control characters, and it CANNOT close the NEWLINE vector, because `parse_frontmatter` splits the value into separate lines BEFORE any validation runs, so the checker is handed only the safe half (driven: on an injected fixture `validate_frontmatter` saw `summary='legit'`, not the injected string, and returned `[]`). The newline half is closeable only at the write path, which is `deftzy`'s work.

THE RULE ID PROBABLY NEEDS NO MINTING. `attention.unsafe-field` is already in the closed `attention_contract.RULE_IDS` catalog and is already used by `specs.validate_spec` for `Gate-Summary`, so widening it to this tree is extending an existing rule's field coverage rather than new policy. It is NOT in `check_engine.RULE_REGISTRY`, so it currently inherits the default `error` severity; `ynhst5` is registering it, and whichever of the two lands second should reuse rather than re-decide that registration.
