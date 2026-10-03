- Id: 7w6zsl
- Status: done
- Graduated-To: 7w6zsl
- Blocks-Release: next
- Set: 7w6zsl
- Priority: medium
- Work-Kind: bug
- Summary: aw research new writes an unvalidated --summary into YAML front matter, so a newline in it injects a sibling key; measured 2026-09-29 while fixing the same class in specs and releases under qbz8i1

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD deftzy executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-7w6zsl-01-deftzy-refuse-an-unsafe-descriptive-value-at-every-research-write-p.ipd.md); evidence .aw/records/plans/executed/20261001-7w6zsl-01-deftzy-refuse-an-unsafe-descriptive-value-at-every-research-write-p.ipd.md
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053059Z-3200713: deftzy
- 2026-09-29 created (aw backlog): aw research new writes an unvalidated --summary into YAML front matter, so a newline in it injects a sibling key; measured 2026-09-29 while fixing the same class in specs and releases under qbz8i1

FILED AS THE CARRIER for the "other trees' creating verbs" row in plan `uz05bl` (Set `qbz8i1`), which closes the same defect class in the `specs` and `releases` trees only.

MEASURED 2026-09-29 in a lane at HEAD `f4b00263`, against a temporary fixture repository.

`aw research new <dir> --kind findings --slug x --summary $'legit\n- Blocks-Release: next' --apply` exits **0** and writes a research doc whose YAML front matter reads:

```
summary: legit
- Blocks-Release: next
consumed-by: []
```

so the injected line becomes a sibling of the real keys inside the `---` fenced block rather than part of the `summary` value. This is the same SPLIT-BEFORE-VALIDATION mechanism measured on the backlog tree in `dtg7dz` F-04 and on specs/releases in `uz05bl` F-06, and it is why the fix must live at the WRITE PATH.

RESEARCH DIFFERS FROM ITS SIBLINGS IN ONE WAY THAT MATTERS FOR THE FIX: its front matter is a YAML block, not the `- Key: value` bullet dialect specs, releases and backlog use. So the blast radius depends on the YAML reader's behavior on a malformed block (a bare `- item` where a mapping key is expected), which the person fixing this MUST measure rather than assume; it may surface as a parse error rather than as a smuggled field, which would make the severity lower than the bullet-tree case but still a defect.

`aw prompts new` WAS AUDITED IN THE SAME PASS AND IS SAFE, so it is deliberately NOT in this item's scope: it has no `--summary`, and its nearest equivalent `--concerns` is written into a single-line HTML metadata comment that FLATTENS the newline. Driven: `--concerns $'legit\n- Blocks-Release: next'` produced `<!-- aw-prompt: ... | Concerns: legit - Blocks-Release: next . ... -->`, one line, no injected field. Do not widen this item to prompts without a fresh measurement showing otherwise.

THE ESTABLISHED FIX SHAPE ALREADY SHIPS TWICE: `backlog._refuse_unsafe_descriptive` (executed plan `dtg7dz`) and the `specs` port in plan `uz05bl`. If this item is the THIRD consumer, it is also the point at which hoisting that helper into `attention_contract` becomes worthwhile; `uz05bl` OQ-02 records why the first two deliberately kept module-private copies and names this sweep as the right place to reconsider.
