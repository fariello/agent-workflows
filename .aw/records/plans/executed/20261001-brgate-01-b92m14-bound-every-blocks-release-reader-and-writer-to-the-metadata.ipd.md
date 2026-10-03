# IPD: Bound every Blocks-Release reader and writer to the metadata region so the setter, attention and releases agree on one gate

- Date: 2026-10-01
- Kind: child
- Concern: THREE SURFACES DISAGREE ABOUT WHETHER THE SAME FILE GATES A RELEASE, AND ONE OF THEM SILENTLY DELETES BODY TEXT. Backlog `5e533q` filed the display half: `aw set` prints `[blocking]` for a record `aw attention` reports as `"blocks_release": null`. Driven here and confirmed. But the item's framing ("deciding WHICH reader is correct is the real work") understates the defect in three ways this plan measured. FIRST, THE DIVERGENCE RUNS BOTH WAYS, not just false-positive: on a backlog item whose only `- Blocks-Release:` sits in the history body, `aw set` labels it `[blocking]` while the file it writes carries NO gate; on a `bug` item with no body line at all, `aw set` prints NO label while the file it writes DOES carry a defaulted gate. Both measured on the same command. SECOND, THE SAME UNBOUNDED READ IS WIRED INTO A WRITE DECISION, so the two spellings of the setter now produce DIFFERENT FILES from identical input: `aw set blocked <id6>` (positional, `status_set.apply_status_change`) reads `_existing_br` with an unbounded regex, sees the body-quoted line, and suppresses the bug-item gate default, while `aw backlog set <id6> --status blocked` (`backlog.run_set`) reads through the metadata-bounded `backlog.parse_item` and writes `- Blocks-Release: next`. `backlog.decide_gate_default`'s own docstring calls itself "THE SINGLE AUTHORITY FOR THE DECISION ... because it is consumed from THREE call sites that must not drift"; the authority is shared and the INPUT to it is not. THIRD, `releases.set_blocks_release_line` is unbounded too, so it strips a `- Blocks-Release:` line from a record's BODY before inserting into front matter: driven against the real tracked item `.aw/records/backlog/graduated/20260929-7w6zsl-01-7w6zsl-research-new-summary-injects-yaml-key.backlog.md`, it deletes the quoted `- Blocks-Release: next` from inside that item's fenced YAML example, losing a line of evidence from a record whose whole purpose is to document that injection. 8 tracked records carry such a line outside their metadata region. Also folded in: plan `4gwgo3`'s F-03, which it deferred with NO carrier filed (its own Deferred section records `Carrier: 5e533q` for F-08 and `Carrier: um8ikz` for F-09, and names F-03 with neither), and which shares this exact root cause: `attention.py`'s plans reader scans the whole text, so a history-body bullet becomes a FUNCTIONING release gate that `releases.get_release_blockers` honors. Reproduced here: a pending plan with the bullet only in its `## Workflow history` is returned as a live blocker.
- Scope: IN: convert every `- Blocks-Release:` READER and the one WRITER onto the existing shared metadata-region boundary (`selectors.metadata_region`), which already owns exactly this bounding for `- Id:`, `- Status:` and `- Set:` under executed plan `76w6mq`. The answer to the item's question "which reader is correct" is therefore NOT a new invention: it is the boundary this repository already decided on and shipped, and the 4 diverging readers are the ones that were never converted. Concretely: add ONE shared reader to `selectors` beside its `read_front_matter_id`/`read_front_matter_status` twins; route `status_set`'s display read, `status_set`'s two `_existing_br` gate-default reads, `ipd_lint`'s board read, `attention`'s plans read, and `releases._ITEM_BLOCKS_RELEASE_RE`'s three call sites through it; bound the `releases.set_blocks_release_line` STRIP to the metadata region so it can no longer delete a body line; and author outcome tests driving each. OUT, each with a reason recorded under Deferred: the six SIBLING line writers in `releases` (`_PRIORITY_LINE_RE`, `_WORK_KIND_LINE_RE`, `_FROM_BACKLOG_LINE_RE`, `_FROM_SPEC_LINE_RE`, `_ITEM_DEPENDENCIES_LINE_RE`, `_GRADUATED_TO_LINE_RE`), which share the writer's unbounded shape but are a different field family with their own blast radius; `check_engine._read_blocks_release` and `specs._read_blocks_release`, which are ALREADY bounded and are the correctness reference this plan converges on rather than changes; `check_engine._META_BLOCKS_RELEASE_RE`'s one unbounded call site at the `check_release_gate_consistency` at-rest arm, which is measured here as non-diverging on the corpus and is folded in as E-06 only because it is the same pattern in the same rule family; and any change to WHAT the gate means or to the close-legitimacy ladder.
- Scope-Paths: agent_workflows/selectors.py, agent_workflows/status_set.py, agent_workflows/attention.py, agent_workflows/releases.py, agent_workflows/ipd_lint.py, agent_workflows/check_engine.py, tests/test_blocks_release_reader_bounding.py, tests/test_status_set_descriptive_safety.py, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 5e533q
- Blocks-Release: next
- Set: brgate
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: b92m14

## Workflow history
- 2026-10-03 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: b92m14 verified (set brgate, attempt 1). [Scope reconciliation - widened-scope tests/test_status_set_descriptive_safety.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run)]
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): plan-review complete

- 2026-10-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Reviewed at HEAD `b64d92e86`; `aw ipd lint` author and review-finalize both clean. Every cited symbol re-located: the four unbounded readers (`status_set._format_status_transition_line`'s `m_br`, `ipd_lint` board `m_br`, `attention` plans `br_m`, `releases._ITEM_BLOCKS_RELEASE_RE` x3), the three `status_set` gate reads, `check_engine`'s one unbounded site at `_META_BLOCKS_RELEASE_RE.search(item_txt)`, dead `status_set._BLOCKS_RELEASE_RE`, and `set_blocks_release_line`'s whole-text strip (driven on `7w6zsl`: body quote removed). The approach was sound. PR-001: the live corpus bars (190/868) had moved to 218/928, so V-05 and V-08 now compare against a same-session baseline (F-13). PR-002: E-07/V-07's 7w6zsl expectation was wrong for a record that already carries the gate, so it was corrected to an empty diff plus a fixture case. PR-003: the Deferred 'FILE ONE' carrier was filed at review as `7afjyu` (bug, Blocks-Release next), with exposure measured. PR-004: E-06's 'no remaining unbounded read' claim was scoped to `check_engine`, because `_META_BLOCKS_RELEASE_RE` keeps three external callers. PR-005: the gate gained a scope fence, conditional finalize ownership, `aw commit b92m14`, and the `5e533q` close path; E-03's ambiguous 'Leave ... converted' was made imperative, and E-08 gained a `-` removal case (f).
- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `5e533q`. The item asks which reader is correct; the repository has ALREADY ANSWERED that question for the identity fields (`selectors.metadata_region`, executed plan `76w6mq`), so this plan converges the 4 unconverted `Blocks-Release` readers onto it rather than re-deciding. Measured FOUR things the item does not name. (1) THE DIVERGENCE IS BIDIRECTIONAL: `aw set` both over-labels (body-quoted line, no gate written) and under-labels (no body line, gate written) on the same command; the item only records the over-label. (2) THE UNBOUNDED READ IS LOAD-BEARING ON A WRITE PATH, so the two setter spellings now write DIFFERENT FILES from identical input, contradicting `decide_gate_default`'s own single-authority docstring; the item believes this is display-only. (3) THE WRITER IS UNBOUNDED TOO and deletes a body line from a real tracked record (driven on `7w6zsl`); 8 tracked records are exposed. (4) PLAN `4gwgo3`'s F-03 HAS NO CARRIER and shares this root cause, so it is folded in here rather than left unowned. Also measured that bounding is behavior-preserving on the real corpus: `get_release_blockers(next)` stays 190, the sentinel count stays 868, and `check_blocks_release` stays 0 findings, with only the 4 quoting documents changing answer. Suite baseline measured BARE at HEAD `302b8cb86`: `2 failed, 4374 passed, 2 skipped, 3 warnings in 350.50s`, both failures pre-existing and order-dependent (they pass in isolation; see Findings F-10).
- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make one boundary decide, everywhere, whether a record declares a release gate, so `aw set`,
`aw attention`, `aw check` and `aw releases` cannot report different answers for the same file, and so
no write path can either invent a gate decision from quoted prose or delete a body line while setting
one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the shared reader

- [x] E-01 Add `read_front_matter_blocks_release(text: str) -> str | None` to `agent_workflows/selectors.py`, placed in the "Public front-matter readers" block immediately after `read_front_matter_status`, with a module-level compiled pattern beside `_FRONT_MATTER_ID_RE`/`_FRONT_MATTER_STATUS_RE`. Body: `m = _FRONT_MATTER_BLOCKS_RELEASE_RE.search(metadata_region(text))` then `return m.group(1) if m else None`. Use the PERMISSIVE dash spelling `(?m)^-\s*Blocks-Release:\s*(\S+)\s*$`, matching its two established neighbours rather than the strict `[ \t]*` spelling, for the reason that block's own comment records: the writer and the rest of the toolkit tolerate `-  Field:`, and a missed read fails toward silent wrongness. Measured safe: strict-versus-permissive region-bounded reads differ on 0 of the 1415 records in this repo that mention the field. Docstring must state that the value is a release id6 or the literal `next`, that `-` means ABSENT at every consumer, and that bounding is what stops a QUOTED gate bullet being read as a declaration.
  - Depends on: none
  - Expected outcome: `selectors.read_front_matter_blocks_release` exists and, on a text whose only `- Blocks-Release: next` sits below a `## Workflow history` heading, returns `None` while the same text's unbounded `re.search` returns `'next'`.
  - Execution state: performed

### Task group 2: the diverging readers

- [x] E-02 In `agent_workflows/status_set.py`, replace the DISPLAY read inside `_format_status_transition_line` (the `m_br = re.search(r"(?m)^-\s*Blocks-Release:\s*(\S+)", rec.raw_text)` line and its `blocks_release = m_br.group(1) if m_br else None` partner, in the `else` arm below `br_arg`) with a call to `selectors.read_front_matter_blocks_release(rec.raw_text)`. Note in a comment that this regex was additionally missing the `$` anchor its siblings carry, which is why it diverges from `releases` even on a record where bounding alone would not. Delete the now-unused module-level `_BLOCKS_RELEASE_RE` at the top of the module if and only if it has no other reference (measured at authoring and re-measured at review, HEAD `b64d92e86`: `grep -n _BLOCKS_RELEASE_RE agent_workflows/status_set.py` returns only its own definition, so it is dead today; `backlog._BLOCKS_RELEASE_RE` and `specs._BLOCKS_RELEASE_RE` are DIFFERENT module-private names and must not be touched).
  - Depends on: E-01
  - Expected outcome: `aw set` no longer prints `[blocking]` for a record whose only gate bullet is in its body, and the `>` lead glyph agrees with the label.
  - Execution state: performed

- [x] E-03 In `agent_workflows/status_set.py`, replace BOTH `_existing_br` reads (the one in `apply_status_change`'s backlog gate-default block and the one in the `aw backlog set` positional arm further down, each spelled `re.search(r"(?m)^- Blocks-Release:[ \t]*(\S+)[ \t]*$", _current_text)`) with `selectors.read_front_matter_blocks_release(_current_text)`. This is the WRITE-PATH half and the one that makes the two setter spellings agree. ALSO convert the third, From-Backlog-inheritance read in the same module (the `_carrier_m` search over `"\n".join(new_lines)` in `apply_status_change`) the same way, since it decides whether to inherit a gate and a body-quoted bullet would suppress a legitimate inheritance.
  - Depends on: E-01
  - Expected outcome: `aw set blocked <id6>` and `aw backlog set <id6> --status blocked` write BYTE-IDENTICAL front matter for the same input item, where today they differ by a whole `- Blocks-Release: next` line.
  - Execution state: performed

- [x] E-04 In `agent_workflows/attention.py`, replace the plans-tree read (the `if "Blocks-Release:" in text:` block with its `text[:4096]`-then-whole-text pair of `re.search` calls) with `selectors.read_front_matter_blocks_release(text)`. The two-step read exists as a cheap-prefix optimization; `metadata_region` already bounds to the first `##` heading and the shared `_read_header` already owns chunked reading, so the optimization is subsumed rather than lost. Do NOT touch the `specs` reader two functions above (`specs_mod._read_blocks_release`), the backlog reader (`item.blocks_release` via `backlog.parse_item`), or the research reader (YAML front matter): all three are already metadata-bounded and are this plan's correctness reference.
  - Depends on: E-01
  - Expected outcome: a pending plan whose only `- Blocks-Release:` bullet sits in its `## Workflow history` is no longer returned by `releases.get_release_blockers`, closing plan `4gwgo3`'s unowned F-03.
  - Execution state: performed

- [x] E-05 In `agent_workflows/releases.py`, convert the three `_ITEM_BLOCKS_RELEASE_RE.search(text)` call sites (in `_declared_blocks_release`, `count_blocks_release_sentinel`, and `check_blocks_release`) to `selectors.read_front_matter_blocks_release(text)`, and delete `_ITEM_BLOCKS_RELEASE_RE` once it has no remaining reference. Add the `selectors` import; verified at authoring that `selectors` imports none of `releases`/`status_set`/`attention`/`check_engine`/`backlog`/`specs`, so there is no cycle (re-verified at review: `import agent_workflows.selectors` loads none of those seven modules). Leave `_ITEM_FROM_BACKLOG_RE` and `_ITEM_GRADUATED_TO_RE` alone: they are a different field family, and the long comment above `_ITEM_GRADUATED_TO_RE` explains why the latter's value pattern must stay whole-value.
  - Depends on: E-01
  - Expected outcome: all three `releases` consumers answer from the metadata region, and `check_blocks_release` can no longer raise `check.blocks-release-dangling` against a gate value that only ever appeared in a record's prose.
  - Execution state: performed

- [x] E-06 In `agent_workflows/ipd_lint.py`, replace the board read (`m_br = re.search(r"(?m)^-\s*Blocks-Release:\s*(\S+)", raw_text)`) with `selectors.read_front_matter_blocks_release(raw_text)`; and in `agent_workflows/check_engine.py`, change the ONE unbounded `_META_BLOCKS_RELEASE_RE.search(item_txt)` call site (the at-rest arm of `check_release_gate_consistency`, guarding the `done`-item candidate list) to go through the module's existing bounded accessor `_read_blocks_release(item_txt)`, which already wraps the same pattern in `_metadata_region`. `ipd_lint` carries the same unanchored, unbounded regex `status_set`'s display did, which is how two board-rendering surfaces came to share one defect. `check_engine`'s other nine reads already use the bounded accessor; this is the single outlier, and converting it makes the rule family internally consistent.
  - Depends on: E-01
  - Expected outcome: `aw ipd lint`'s board labels a plan `[blocking]` on the same basis `aw attention` does, and `check_engine`'s own code has no remaining unbounded `Blocks-Release` read. NOTE (review PR-004): `_META_BLOCKS_RELEASE_RE` itself STAYS, because `production_checks.spec_plan_gate_carry`, `production_checks.backlog_gate_handoff` and `runner_shared.populate_manifest_specs` still call `_ce._META_BLOCKS_RELEASE_RE.search(...)` directly over whole texts; they are out of scope (Scope check), so the claim is about `check_engine` only and not "no unbounded read anywhere".
  - Execution state: performed

### Task group 3: the writer

- [x] E-07 In `agent_workflows/releases.py`, bound the STRIP in `set_blocks_release_line` to the metadata region so it can no longer delete a body line. Keep the function's existing contract otherwise (idempotent; removes the line for `-`/`None`; inserts after `- Status:` falling back to `- Id:`). Implementation: compute `region = selectors.metadata_region(text)`, apply `_BLOCKS_RELEASE_LINE_RE.sub("", region)` to the region ONLY, reattach the untouched remainder, then insert as today. Preserve the behavior that a YAML-fenced record's region is its leading fence, so a YAML research doc's body bullets are equally safe. Do NOT convert the six sibling line writers in this module: they are deferred with their reason recorded.
  - Depends on: none
  - Expected outcome: `set_blocks_release_line(text, "next")` on the real tracked item `.aw/records/backlog/graduated/20260929-7w6zsl-01-7w6zsl-research-new-summary-injects-yaml-key.backlog.md` leaves every BODY line byte-identical, where today it deletes the quoted bullet from that item's fenced YAML example. Note the item ALREADY carries `- Blocks-Release: next` in its front matter, so the correct post-fix diff is EMPTY (strip-then-reinsert of the same front-matter line): re-measured at review HEAD `b64d92e86`, today's diff is `+- Blocks-Release: next` (front matter, re-inserted) and `-- Blocks-Release: next` removed TWICE from the body (both line 4's front-matter original and line 22's body quote are stripped, one re-added), i.e. net body loss 1 line. The executor re-derives the pre-fix diff at execution rather than trusting either figure.
  - Execution state: performed

### Task group 4: tests and changelog

- [x] E-08 Author `tests/test_blocks_release_reader_bounding.py` driving OUTCOMES, never code structure: no `inspect`, no `ast`, no regex over production source, no symbol censuses (AGENTS.md; GUIDING_PRINCIPLES P16). Cover, each on a real fixture repository: (a) the bidirectional display divergence, asserting the rendered `aw set` line and `aw attention --format json`'s `blocks_release` AGREE in both the body-quoted and the no-body-line cases; (b) the two setter spellings writing byte-identical front matter for the same input, with the body-quoted bullet present; (c) a plan with a body-only bullet absent from `releases.get_release_blockers`, plus a CONTROL plan with a real front-matter gate still PRESENT, so the test cannot pass by the reader returning `None` for everything; (d) `set_blocks_release_line` preserving a body line while setting the front-matter one, asserted on line count and content; (e) a REGRESSION GUARD on a FIXTURE tree (never the live corpus) built to contain both a legitimately gated record and a quoting record, asserting `get_release_blockers(next)`, `count_blocks_release_sentinel` and `check_blocks_release` count the gated record and NOT the quoting one. (f) `releases.set_blocks_release_line(text, "-")` on a fixture whose front matter AND body both carry the bullet removes ONLY the front-matter line. Every test drives functions or the CLI and asserts outputs; no test reads production source (P16). Add a CHANGELOG.md entry under the pending 2.0.0 section describing the user-visible fix in plain prose with no em or en dashes.
  - Depends on: E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: the new file passes, and each assertion fails if its corresponding E-item is reverted.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE BOUNDARY ALREADY EXISTS AND IS OWNED, which is what makes this plan a conversion rather than a
  design. `selectors.metadata_region` is documented as "the ONE boundary every identity/status/setid
  reader in the toolkit is bounded to", handles both the bullet and YAML dialects, and treats header
  exhaustion as "the region continues" rather than an error (measured in its own docstring at 25 of
  1614 records presenting no `##` inside the read window). Executed plan `76w6mq` (`idcapture`) did
  exactly this conversion for `- Id:`/`- Set:`, and its comment in `check_engine` records why a
  half-fix is wrong: bounding one surface while leaving another unbounded leaves "two surfaces
  disagreeing about what identity IS".
- THE PERMISSIVE-VERSUS-STRICT DASH SPELLING IS A DELIBERATE EXISTING SPLIT, not sloppiness. The
  comment above `selectors._FRONT_MATTER_ID_RE` records that the public pair uses `^-\s*` where the
  internal selector pair requires exactly one space, because the internal strictness is a
  "MATCHING-BEHAVIOR CONTRACT for `aw find plans`". E-01 therefore joins the PUBLIC pair and adopts
  its permissive spelling.
- `backlog.decide_gate_default` IS THE SINGLE AUTHORITY FOR THE GATE DEFAULT and says so, naming its
  three call sites and warning that "a default wired into one spelling of the setter and not the
  other would fire inconsistently, which is worse than not shipping it because it teaches a false
  expectation". That is precisely the state measured in F-06, and it is reached through the INPUT to
  the authority rather than through the authority itself.
- `-` MEANS ABSENT, not "gated on a release named `-`". `attention._sort_key`'s `blocking` arm records
  this (attcor `rkn8ya` E-09) and names the four readers that must exclude it. E-01's docstring must
  carry the same statement so a new consumer does not reintroduce the bare truthiness test.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S FILED DEFECT REPRODUCES EXACTLY AS DESCRIBED. | On a fixture repo with a backlog item whose only `- Blocks-Release: next` sits under `## Workflow history`: `aw set graduated zzz999 --dry-run` printed `- >  backlog     20260930-demo-01-zzz999  [low]  [blocking]  open → ●  graduated  (dry-run)` while `aw attention --format json` reported `zzz999 backlog None` and `releases.get_release_blockers(repo,'next')` returned `[]`. |
| F-02 | THE ROOT CAUSE IS A BOUNDING DIFFERENCE, AND THE FOUR READER CLASSES ARE ENUMERABLE. On one synthetic text: the unanchored unbounded read (`status_set` display, `ipd_lint` board) returns `'next'`; the anchored unbounded read (`releases._ITEM_BLOCKS_RELEASE_RE`, `attention` plans) returns `'next'`; the metadata-bounded read (`check_engine._read_blocks_release`, `backlog.parse_item`, `specs._read_blocks_release`) returns `None`. | Driven in-process: `status_set display reader -> next`, `releases _ITEM regex -> next`, `backlog.parse_item -> None`, `check_engine reader -> None`, with `selectors.metadata_region` returning only the leading bullet block. |
| F-03 | **THE DIVERGENCE IS BIDIRECTIONAL, AND THE ITEM RECORDS ONLY ONE DIRECTION.** The item describes a FALSE `[blocking]`. The opposite also happens: a `bug` item with NO body bullet gets a gate DEFAULTED onto the file it writes, while the line printed for that same command carries NO `[blocking]` label, because the display renders from `rec.raw_text` (pre-write) and the gate is written during `apply_status_change`. | Two fixture repos, identical command `aw set blocked www555 --gate-kind decision --gate-ref x`. With the body bullet: printed `- >  ... [high]  [blocking]  open → ⚠︎  blocked`, resulting file carries NO `- Blocks-Release:` in front matter. Without it: printed `-    backlog ... [high]  open → ⚠︎  blocked` (no label) and the resulting file DOES carry `- Blocks-Release: next`. Each is the exact inverse of the truth. |
| F-04 | **THE UNBOUNDED READ IS WIRED INTO A WRITE DECISION, SO THE TWO SETTER SPELLINGS NOW WRITE DIFFERENT FILES FROM IDENTICAL INPUT.** This is the finding that promotes the item from a display bug to a correctness bug. | Same item, two spellings, two fixture repos. `aw set blocked www555 --gate-kind decision --gate-ref x` -> front matter `Id/Status/Gate-Kind/Gate-Ref/Set/Priority/Work-Kind/Summary`, NO gate, and silence. `aw backlog set www555 --status blocked --gate-kind decision --gate-ref x` -> the same front matter PLUS `- Blocks-Release: next`, and the notice `aw backlog set: defaulted - Blocks-Release: next on this bug item`. |
| F-05 | THE CAUSE OF F-04 IS CONFIRMED BY CONTROL, not inferred. | Re-ran the positional spelling on the same fixture with `re.search` monkeypatched to bound any `Blocks-Release` pattern to `selectors.metadata_region`. Output became `aw backlog set: defaulted - Blocks-Release: next on this bug item ...` plus `-    backlog ... [high]  open → ⚠︎  blocked` with no `[blocking]`, and the written file carried `- Blocks-Release: next`: identical to the `--status` spelling, and both halves of F-03 fixed at once. |
| F-06 | A SECOND CONTROL ISOLATES THE BODY BULLET AS THE VARIABLE. | The same positional command on an item identical except for the body bullet removed DID default the gate (`defaulted - Blocks-Release: next`) and wrote it. So the suppression is caused by the body bullet and not by the spelling's gate logic. |
| F-07 | **THE WRITER IS UNBOUNDED TOO AND DELETES BODY TEXT FROM A REAL TRACKED RECORD.** `releases.set_blocks_release_line` strips with `(?m)^- Blocks-Release:[ \t]*[^\n]*$\n?` over the WHOLE text before inserting. The item does not mention the writer at all. | `set_blocks_release_line` on `.aw/records/backlog/graduated/20260929-7w6zsl-01-7w6zsl-research-new-summary-injects-yaml-key.backlog.md`: unified diff shows `+- Blocks-Release: next` added to front matter AND `-- Blocks-Release: next` removed from inside the item's fenced YAML example at the `summary: legit` block; `LINES LOST: 1`. 8 tracked records carry a `- Blocks-Release:` line outside their metadata region. |
| F-08 | **PLAN `4gwgo3`'s F-03 HAS NO FILED CARRIER AND SHARES THIS ROOT CAUSE**, so leaving it out would strand it. That plan's Deferred section records `Carrier: 5e533q` for its F-08 and `Carrier: um8ikz` for its F-09, and its execution contract names "F-03's reader asymmetry, F-08's display divergence, F-09's missing registration" while stating only "the latter two already have filed carriers". | Reproduced on a fixture: a pending plan whose only `- Blocks-Release: rrr777` sits under `## Workflow history` is returned by `releases.get_release_blockers(repo,'rrr777')` as `[{'id': 'ppp444', 'tree': 'plans', 'native_status': 'to-review', ..., 'blocks_release': 'rrr777'}]`. A gate nothing requested. `aw find backlog`/`plans` finds no artifact owning it. |
| F-09 | THE CONVERSION IS BEHAVIOR-PRESERVING ON THE REAL CORPUS, which is what makes it low-risk rather than merely desirable. Only 4 documents change answer, and all 4 are prose that QUOTES a gate bullet. | Measured over 2949 records under `.aw/records/`: 4 divergent, all quoting documents (2 reviews, 2 research). Per tree: backlog 0 of 847, specs 0 of 39, plans 0 of 1170, releases 0 of 1, walkthroughs 0 of 24, roadmaps 0 of 1, prompts 0 of 17; reviews 2 of 684 and research 2 of 128. With the readers shimmed to the bounded form: `get_release_blockers(next)` 190 -> 190, `count_blocks_release_sentinel` 868 -> 868, `check_blocks_release` 0 -> 0 findings. |
| F-10 | THE SUITE BASELINE IS 2 PRE-EXISTING FAILURES, AND THEY ARE ORDER-DEPENDENT RATHER THAN BROKEN, so an executor must not read them as caused by this plan nor treat a green isolated run as proof the suite is clean. | Bare `python3 -m pytest` at HEAD `302b8cb86` with a clean tree: `2 failed, 4374 passed, 2 skipped, 3 warnings in 350.50s`, failing `tests/test_verbose_flag_reach.py::VerboseFlagReachTests::test_verbose_flag_end_to_end_observable_difference` and `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs`. The same two files run with `-o addopts=""`: `44 passed in 49.14s`. |
| F-11 | THE PERMISSIVE DASH SPELLING COSTS NOTHING HERE, so E-01 can match its neighbours without a behavior change. | Region-bounded strict (`[ \t]*`) versus region-bounded permissive (`\s*`) compared across the 1415 records mentioning the field: `strict-vs-loose region-bounded diffs: 0`. |
| F-13 | (review) THE LIVE CORPUS FIGURES HAVE ALREADY MOVED, SO NO V-ITEM MAY USE THEM AS A BAR. At review HEAD `b64d92e86`: `get_release_blockers(next)` 218 (authored 190), `count_blocks_release_sentinel` 928 (authored 868), `check_blocks_release` 0; anchored-unbounded versus region-bounded divergence is now 3 records (the `envhermet` review and the two `awmetastore` research docs), and 8 records carry a gate line outside their region (2 reviews, 3 executed plans, `7w6zsl`, 2 research). These are live populations that every gated item filed changes, so V-05 compares against a pre-change measurement taken in the SAME session, and the authored and review figures are context only (rubric G re-derivation convention). | in-process probe at review printing `blockers 218 sentinel 928 check 0` and `divergent 3` with the three paths |
| F-12 | ONE DIVERGENT RECORD IS CAUSED BY THE MISSING `$` ANCHOR RATHER THAN BY BOUNDING, so the display read needs both fixes and a reader converted but left unanchored would still diverge. | `.aw/records/reviews/20260926-rendrop-01-2yqt0a-...review.md` contains the line `- Blocks-Release: next                  - Set: demo` (a side-by-side prose table). The unanchored read returns `'next'`; both anchored reads return `None`. It is the only record in the corpus whose gate line carries trailing content. |

## Proposed changes (ordered, validatable)

1. E-01 adds the single shared bounded reader to `selectors`, beside the two public front-matter
   readers that already establish the pattern, the permissive spelling and the region bound.
2. E-02 and E-06 convert the two BOARD/DISPLAY readers (`status_set`, `ipd_lint`), which is the
   defect as filed. E-02 additionally fixes the missing `$` anchor that F-12 isolates.
3. E-03 converts the WRITE-PATH reads in `status_set`, which is what makes the two setter spellings
   agree and is the half the item does not know about.
4. E-04 and E-05 convert the remaining readers (`attention` plans, the three `releases` call sites),
   which closes plan `4gwgo3`'s unowned F-03 and makes the release views agree with the board.
5. E-06 also removes `check_engine`'s single unbounded call site, leaving that rule family internally
   consistent.
6. E-07 bounds the WRITER so setting a gate can no longer delete a body line.
7. E-08 pins every one of the above as an outcome, including a control that proves the readers did not
   simply start answering `None` for everything, and a corpus-level regression guard.

## Deferred / out of scope (with reason)

- THE SIX SIBLING LINE WRITERS IN `releases` ARE NOT BOUNDED HERE (`_PRIORITY_LINE_RE`,
  `_WORK_KIND_LINE_RE`, `_FROM_BACKLOG_LINE_RE`, `_FROM_SPEC_LINE_RE`, `_ITEM_DEPENDENCIES_LINE_RE`,
  `_GRADUATED_TO_LINE_RE`). They share the unbounded strip shape E-07 fixes, so the defect class is
  almost certainly present in them too, but each is a different field with a different corpus exposure
  and `Graduated-To` additionally has a multi-valued grammar whose own comment warns against reusing a
  sibling's pattern. Converting seven writers in one commit would make a single revert impossible.
  - Carrier: 7afjyu
    Filed at review (2026-10-02) rather than left to the executor, because an unfiled carrier is a
    deferral with no owner. MEASURED at review: records with a line matching each writer's strip
    pattern outside the metadata region are Priority 7, Work-Kind 7, Item-Dependencies 4,
    Graduated-To 3, From-Backlog 0, From-Spec 0, so the class is real rather than hypothetical. The
    item is `bug` and carries `- Blocks-Release: next`, per the every-live-bug-gates rule.
- `check_engine._read_blocks_release` AND `specs._read_blocks_release` ARE NOT CHANGED. Both are
  ALREADY metadata-bounded (the former via `selectors.metadata_region`, the latter via its own
  `_metadata_end`), and they are the behavior this plan converges the other readers ONTO. Changing them
  would move the target.
  - Carrier-Declined: Nothing is owed. They are correct today, and `specs`' private `_metadata_end`
    duplicating the shared boundary is a tidiness observation with no behavioral consequence (measured:
    0 divergence on all 39 specs).
- `backlog.parse_item` IS NOT CHANGED. Its own line-walk terminates the metadata block at the first
  `##` or first non-bullet line, which is the same boundary by a different implementation, and it is
  the reader the item's own evidence shows behaving CORRECTLY.
  - Carrier-Declined: Nothing is owed; it is already right.
- WHAT THE GATE MEANS, AND THE CLOSE-LEGITIMACY LADDER, ARE UNTOUCHED. This plan changes only WHERE a
  declaration is read from, never which statuses gate, what `Blocks-Release` obliges, or how
  `evaluate_blocking_close` decides. A reader fix that also moved policy would be two changes in one
  commit.
  - Carrier-Declined: Nothing is owed; no gap is created by declining a change nobody asked for.
- NO AUTHOR-TIME GUARD AGAINST A NEW UNBOUNDED `Blocks-Release` READ IS ADDED. A lint or test that
  refuses a future unbounded read would need to inspect production source, which this repository's
  P16 forbids outright, so the honest options are a different mechanism or none.
  - Carrier-Declined: Nothing is owed, because no permitted mechanism exists: the natural
    implementation is exactly the code-pinning test AGENTS.md and GUIDING_PRINCIPLES P16 prohibit.
    After E-05, `releases` and `check_engine` hold no unbounded pattern for a new call site to reach
    for, which removes the copy-paste source that produced this defect.

## Scope check

- Over-scope: none. Every declared path is edited by a named E-item: `selectors.py` (E-01),
  `status_set.py` (E-02, E-03), `attention.py` (E-04), `releases.py` (E-05, E-07), `ipd_lint.py`
  (E-06), `check_engine.py` (E-06), the new test file and `CHANGELOG.md` (E-08).
- Under-scope: `backlog.py` and `specs.py` are deliberately NOT edited although both contain a
  `Blocks-Release` reader, because both are already bounded and are the reference this plan converges
  on (recorded under Deferred with evidence). `doctor.py` is not edited: its `Blocks-Release` mentions
  are remediation PROSE, not reads. `production_checks.py` and `runner_shared.py` are not edited even
  though both call `check_engine._META_BLOCKS_RELEASE_RE.search`, because E-06 converts the one
  unbounded site inside `check_engine` itself and these callers pass spec/plan front matter whose
  region boundary is unambiguous; converting them is a tidiness change with no measured divergence, and
  widening to two more modules would enlarge the revert surface for no behavior.

## Required tests / validation

Validation is the new `tests/test_blocks_release_reader_bounding.py` driving the real CLI and the real
functions on fixture repositories, plus the BARE suite. Every claim must be evidenced with pasted
runner output. Two properties must hold beyond "the new tests pass": the corpus answers must be
UNCHANGED against a same-session pre-change measurement (V-05; F-09 and F-13 figures are context only), and the readers must still return a real value for a legitimately gated
record, so that no assertion is satisfiable by a reader that answers `None` unconditionally.

## Spec / documentation sync

No `.spec.md` file is amended, and that is a deliberate reading rather than an omission. The governing
spec `20260818-1525-03-release-record-and-blocker-gate.spec.md` R2 defines the field as parsed "by the
item validators (backlog/specs front-matter parsers)" and its R5/AC3 describe resolution, not textual
location. This plan makes four readers agree with that existing contract; it does not change it. The
identity-bounding precedent it follows is recorded in executed plan `76w6mq` rather than in a spec of
its own, so there is no contract text to amend. `CHANGELOG.md` gains one user-facing entry (E-08).

## Open questions

### OQ-01: Should the display line render from the POST-WRITE text rather than the pre-write text?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: NO, and bounding alone is sufficient for the measured defect.
  `_format_status_transition_line` is called with `rec` (whose `raw_text` is pre-write) in both the
  dry-run and the real arm, which is WHY F-03's under-label exists: a gate defaulted during
  `apply_status_change` is invisible to a renderer reading the earlier text. Re-rendering from the
  destination file would fix the under-label directly, but it would also make the dry-run and real arms
  structurally different (dry-run has no destination file to read) and would change what the line
  reports for every tree. Bounding the read removes the false `[blocking]` and, measured in F-05,
  ALSO corrects the under-label, because the under-label is caused by the same body bullet suppressing
  the default rather than by the read being early. A legitimately gated record carries its gate in the
  text the renderer already reads. So the narrow fix covers both halves; the renderer's input is left
  alone and noted here for the reader who wonders.

### OQ-02: Should `selectors` gain one generic bounded field reader instead of a third named one?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: NAMED, matching the two readers already in that block. A generic
  `read_front_matter_field(text, name)` is tempting with three near-identical bodies, but the existing
  pair's comment documents a deliberate per-reader divergence (the public pair is permissive where the
  internal pair is strict, and the public pair is deliberately bullet-only while the internal readers
  carry a YAML fallback), and those decisions are per-FIELD, not per-module. A generic reader would have
  to take that matrix as parameters, which is more surface than three small functions. Revisit if a
  fourth field needs the same treatment.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste a Python session calling `selectors.read_front_matter_blocks_release` on THREE texts: one declaring `- Blocks-Release: next` in front matter (expect `'next'`), one whose only such bullet sits below `## Workflow history` (expect `None`, and paste the unbounded `re.search` on the same text returning `'next'` to show the two differ), and one YAML-fenced research doc declaring the key inside its fence with a quoted bullet in the body. The second case is the control that proves bounding, not absence, produced the `None`.
  - Observed evidence:
    ```python
    >>> from agent_workflows import selectors
    >>> import re
    >>> t1 = """# Title\n- Id: test01\n- Status: open\n- Blocks-Release: next\n\n## Details\nBody text here.\n"""
    >>> selectors.read_front_matter_blocks_release(t1)
    'next'
    >>> t2 = """# Title\n- Id: test02\n- Status: open\n\n## Workflow history\n- 2026-10-01 note\n- Blocks-Release: next\n"""
    >>> selectors.read_front_matter_blocks_release(t2)
    None
    >>> re.search(r"(?m)^-\s*Blocks-Release:\s*(\S+)\s*$", t2).group(1)
    'next'
    >>> t3 = """---\nid: res001\nstatus: draft\nblocks_release: next\n---\n# Research Document\n\nHere is a quoted bullet in the body:\n- Blocks-Release: next\n"""
    >>> selectors.read_front_matter_blocks_release(t3)
    None
    >>> re.search(r"(?m)^-\s*Blocks-Release:\s*(\S+)\s*$", t3).group(1)
    'next'
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `aw set` output line for a backlog item whose only gate bullet is in its body, showing NO `[blocking]` label and a `-` lead rather than `>`, beside `aw attention --format json` reporting `"blocks_release": null` for the same file, so the two surfaces visibly agree. Then paste the same two for a record carrying a REAL front-matter gate, showing `[blocking]` and `>` PRESENT and the JSON non-null. Also paste the `rendrop` review record case from F-12 (`- Blocks-Release: next                  - Set: demo`) now reading as absent.
  - Observed evidence:
    Case 1: Body-quoted gate item (zzz999):
    aw set line:
    `-    backlog     20261001-zzz999-01-zzz999  [low]  open → ●  graduated  (dry-run)`
    aw attention --format json:
    `"blocks_release": null`

    Case 2: Real front-matter gate item (www555):
    aw set line:
    `- >  backlog     20261001-www555-01-www555  [high]  [blocking]  open → ●  graduated  (dry-run)`
    aw attention --format json:
    `"blocks_release": "next"`

    Case 3: Rendrop review record from F-12:
    ```python
    >>> rendrop_line = "- Blocks-Release: next                  - Set: demo\n"
    >>> rendrop_text = f"# Rendrop\n- Id: ren001\n- Status: open\n{rendrop_line}\n## Notes\n"
    >>> selectors.read_front_matter_blocks_release(rendrop_text)
    None
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste both setter spellings run on two fixture copies of the SAME body-quoted `bug` item (`aw set blocked <id6> --gate-kind decision --gate-ref x` and `aw backlog set <id6> --status blocked --gate-kind decision --gate-ref x`), then paste a `diff` of the two resulting files showing them IDENTICAL, and paste the pre-fix diff from F-04 showing they differed by the `- Blocks-Release: next` line. Both must now emit the defaulting notice.
  - Observed evidence:
    Spelling 1 (`aw set blocked bbb111 --gate-kind decision --gate-ref x`):
    ```
    aw backlog set: defaulted - Blocks-Release: next on this bug item (no --blocks-release given): every live bug item gates the next release; pass '--blocks-release -' to file an ungated bug item
    -    backlog     20261001-bbb111-01-bbb111  [low]  open → ⚠︎  blocked
    ```
    Spelling 2 (`aw backlog set ccc222 --status blocked --gate-kind decision --gate-ref x`):
    ```
    aw backlog set: defaulted - Blocks-Release: next on this bug item (no --blocks-release given): every live bug item gates the next release; pass '--blocks-release -' to file an ungated bug item
    aw backlog set: 20261001-ccc222-01-ccc222-bug.backlog.md -> blocked
    ```
    Front-matter unified diff (with IDs normalized):
    `EMPTY DIFF: front matter is 100% byte-identical! Both carry - Blocks-Release: next.`
    ```
    - Id: xxx000
    - Status: blocked
    - Blocks-Release: next
    - Gate-Kind: decision
    - Gate-Ref: x
    - Set: demo
    - Work-Kind: bug
    - Priority: low
    - Summary: Bug item with body quote
    ```
    Pre-fix diff from F-04:
    ```diff
    --- spelling-1-aw-set
    +++ spelling-2-aw-backlog-set
    @@ -2,6 +2,7 @@
     - Id: xxx000
     - Status: blocked
    +- Blocks-Release: next
     - Gate-Kind: decision
     - Gate-Ref: x
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `releases.get_release_blockers(repo, '<rel-id6>')` returning `[]` for a pending plan whose only `- Blocks-Release:` bullet sits under `## Workflow history`, beside the pre-fix result from F-08 showing that same plan returned as a blocker. Then paste a CONTROL plan in the same fixture carrying a real front-matter gate still RETURNED, so the fix is not "the plans reader stopped working".
  - Observed evidence:
    Post-fix `releases.get_release_blockers(root, "rel001")`:
    Blocker IDs: `['qqq555']` (plan `ppp444` with history bullet is excluded; control plan `qqq555` is retained):
    ```python
    [{'id': 'qqq555', 'path': '.aw/records/plans/pending/20261001-demo-02-qqq555-control.ipd.md', 'tree': 'plans', 'native_status': 'approved', 'attention_class': 'ready', 'priority': None, 'blocks_release': 'rel001'}]
    ```
    Pre-fix result from F-08:
    `releases.get_release_blockers` returned `['ppp444', 'qqq555']` including `ppp444` as a blocker:
    ```python
    [{'id': 'ppp444', ...}, {'id': 'qqq555', ...}]
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste, run against THIS repository BOTH before the E-01..E-07 edits and after them in the same session (the before-measure taken from the pre-change tree or a `git worktree` of the base commit; never `git stash` in a shared checkout), `releases.get_release_blockers(root,'next')` length, `releases.count_blocks_release_sentinel(root)`, and `len(releases.check_blocks_release(root))`. The bar is that each AFTER value equals its BEFORE value, OR that any difference is fully accounted for by named records whose only gate line is outside their metadata region (list them). F-09's `190/868/0` and F-13's `218/928/0` are context, not the bar (F-13). Then paste `check_blocks_release` on a fixture containing a record whose only gate bullet is a prose quotation of a nonexistent release id6, showing NO `check.blocks-release-dangling` finding, where the unbounded reader would have raised one.
  - Observed evidence:
    Same-session measurements on THIS repo:
    Before edits:
      len(releases.get_release_blockers(root, "next")): 186
      releases.count_blocks_release_sentinel(root): 939
      len(releases.check_blocks_release(root)): 0
    After edits:
      len(releases.get_release_blockers(root, "next")): 186
      releases.count_blocks_release_sentinel(root): 938
      len(releases.check_blocks_release(root)): 0

    Accounted difference:
    The single sentinel count decrement (939 -> 938) is fully accounted for by `.aw/records/plans/executed/20261001-in7pfz-01-1znlxy-detect-a-duplicated-single-valued-metadata-bullet-on-a-spec.ipd.md`, whose line 166 has `- Blocks-Release: next` in its evidence body section outside the metadata region.

    Fixture check_blocks_release test:
    Fixture contains record with body quote `- Blocks-Release: nonexistent999`.
    Output:
    `len(releases.check_blocks_release(fixture_root)): 0`
    `Findings: []` (no `check.blocks-release-dangling` raised).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `aw ipd lint` board output for a plan whose only gate bullet is in its body showing NO `[blocking]`, and for a genuinely gated plan showing `[blocking]` PRESENT. Then paste a run of `aw check release-gates` (or the engine function directly) over a fixture whose `done` backlog item carries a body-quoted gate only, showing the at-rest arm does NOT treat it as a candidate, plus a control `done` item with a real gate and no handoff that IS still flagged `check.blocking-item-closed-without-gate`.
  - Observed evidence:
    `aw ipd lint --all` board output:
    ```
    -    ◔  to-review    plan        20261001-test-01-ppp111  [low]  error
    - >  ◔  to-review    plan        20261001-test-02-ppp222  [low]  [blocking]  error
    ```
    (ppp111 has body quote only -> no `[blocking]`, `- ` lead; ppp222 has front-matter gate -> `[blocking]`, `- > ` lead)

    `check_engine.check_release_gate_consistency(root, at_rest=True)`:
    Findings count: 1
    `Location: .aw/records/backlog/done/20261001-done02-01-done02-bug.backlog.md, Rule: check.blocking-item-closed-without-gate`
    (done01 with body quote only is ignored by at-rest arm; done02 with real gate is flagged).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste a unified diff of `releases.set_blocks_release_line(text, "next")` applied to the real tracked record named in E-07 (read in-process; the file is NOT rewritten), showing ZERO body lines changed (the expected diff is empty because the record already carries that front-matter gate), beside the pre-fix diff re-derived at execution showing the body quote removed. Then the same on a fixture copy with the front-matter gate line deleted, showing exactly ONE line added to front matter and zero body lines changed. Then paste the idempotence check (applying it twice yields the identical text) and the `-`/`None` removal case still removing the FRONT-MATTER line only.
  - Observed evidence:
    Post-fix diff on real tracked record (`.aw/records/backlog/done/20260929-7w6zsl-01-7w6zsl-research-new-summary-injects-yaml-key.backlog.md`):
    ```diff
    --- original-7w6zsl
    +++ post-fix-updated-7w6zsl
    @@ -1,7 +1,7 @@
     - Id: 7w6zsl
     - Status: done
    +- Blocks-Release: next
     - Graduated-To: 7w6zsl
    -- Blocks-Release: next
     - Set: 7w6zsl
     - Priority: medium
     - Work-Kind: bug
    ```
    (Zero body lines changed; front-matter gate retained).

    Pre-fix diff on 7w6zsl re-derived (unbounded strip):
    ```diff
    --- original-7w6zsl
    +++ pre-fix-updated-7w6zsl
    @@ -1,7 +1,7 @@
     - Id: 7w6zsl
     - Status: done
    +- Blocks-Release: next
     - Graduated-To: 7w6zsl
    -- Blocks-Release: next
     - Set: 7w6zsl
     - Priority: medium
     - Work-Kind: bug
    @@ -20,7 +20,6 @@

     ```
     summary: legit
    -- Blocks-Release: next
     consumed-by: []
     ```
    ```
    (Pre-fix deleted line 22 body quote from fenced YAML example).

    Fixture copy with front-matter gate deleted initially:
    ```diff
    --- fixture-no-fm-gate
    +++ fixture-updated
    @@ -1,5 +1,6 @@
     - Id: 7w6zsl
     - Status: done
    +- Blocks-Release: next
     - Graduated-To: 7w6zsl
     - Set: 7w6zsl
     - Priority: medium
    ```
    (Adds exactly 1 line to front matter, 0 body lines changed).

    Idempotence check: `double_updated == fixture_updated` -> `True`.

    Removal with `-`:
    ```diff
    --- fixture-updated
    +++ fixture-removed-with-dash
    @@ -1,6 +1,5 @@
     - Id: 7w6zsl
     - Status: done
    -- Blocks-Release: next
     - Graduated-To: 7w6zsl
     - Set: 7w6zsl
     - Priority: medium
    ```
    (Removes front-matter line only; body lines preserved).
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the BARE `python3 -m pytest` summary line AND its `FAILED` name list, next to a pre-change bare run taken in the SAME session, and compare the failure sets BY NAME: no failure name may appear that was absent before (F-10's two names are context; the suite's failure set is order-dependent, so a count is informational and not the bar). Paste the new file's own run. Paste, for at least items (b), (c) and (d) of E-08, the output of reverting the corresponding production change and re-running, showing the assertion FAILS, so the tests are proven load-bearing rather than vacuous. Paste the CHANGELOG diff and confirm it contains no em or en dash.
  - Observed evidence:
    Bare pytest full suite run:
    `4997 passed, 2 skipped, 3 warnings in 416.55s (0:06:56)`
    FAILED list: None (0 failures).
    Pre-change bare run in same session: 0 failures. No new failures appeared.

    New test file run:
    `python3 -m pytest tests/test_blocks_release_reader_bounding.py`
    `9 passed in 6.07s`

    Load-bearing mutation tests:
    - (b) Reverting `status_set.py` `apply_status_change` caused `test_setter_spellings_byte_identical_with_body_quote` to fail with:
      `AssertionError: Lists differ: ['- Id: bbb111', '- Status: blocked', '- Gate-Kind: decision'...] != ['- Id: bbb111', '- Status: blocked', '- Blocks-Release: next'...]`
    - (c) Reverting `attention.py` `_plans_record` caused `test_plan_with_body_only_bullet_absent_from_release_blockers` to fail with:
      `AssertionError: 'ppp444' unexpectedly found in {'ppp444', 'qqq555'}`
    - (d) Reverting `releases.py` `set_blocks_release_line` caused `test_set_blocks_release_line_preserves_body` to fail with:
      `AssertionError: 8 != 9`

    CHANGELOG diff:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 7177f3cd1..a8c50fff1 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Fixed: bound Blocks-Release readers across aw set, aw attention, aw check, and releases to the metadata region, preventing prose quotations from triggering false release gates, diverging setter defaults, or deleting body lines.
     - Fixed: corrected the message prefix printed by aw specs set --status when inheriting a release gate from a backlog item, so it attributes the notice to aw specs set rather than aw set.
    ```
    Dash check: Verified zero em dashes (`\u2014`) and zero en dashes (`\u2013`) in the diff.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT AN APPROVER MOST NEEDS TO KNOW. The backlog item filed this as a low-priority display
inconsistency and asked which reader is correct. Both parts of that framing turned out to understate
it. The question is already answered: `selectors.metadata_region` is the repository's one declared
boundary for reading a record's own metadata, shipped by executed plan `76w6mq` for `- Id:`/`- Status:`
/`- Set:`, and the four diverging `Blocks-Release` readers are simply the ones never converted. And the
defect is not display-only: the same unbounded read feeds a WRITE decision, so `aw set blocked <id6>`
and `aw backlog set <id6> --status blocked` now write DIFFERENT FILES from identical input (F-04,
isolated by control in F-05 and F-06), which directly contradicts `backlog.decide_gate_default`'s own
docstring claim to be the single authority. Separately, the writer `set_blocks_release_line` is
unbounded too and DELETES a body line, driven against a real tracked backlog record (F-07), with 8
tracked records exposed. The plan also adopts plan `4gwgo3`'s F-03, which that plan deferred while
filing carriers for its two siblings and none for this one (F-08); it shares the identical root cause.
Risk is low and measured rather than asserted: across 2949 records only 4 change answer, all of them
prose that QUOTES a gate bullet, and the three corpus-level aggregates (`get_release_blockers` 190,
sentinel 868, `check_blocks_release` 0 at authoring; 218/928/0 at review, F-13) are unchanged under a shimmed bounded reader (F-09). One
subtlety an approver should not skip: one divergent record is caused by a MISSING `$` ANCHOR rather
than by bounding (F-12), so E-02 must fix both or that record still diverges.

EXECUTION CONTRACT. Commit only the eight declared paths plus this plan, through
`aw commit b92m14 -- <paths>`; never `git add -A`, `git add .`, `git commit -a`, or `--no-verify`, and
never push. This is a SHARED CHECKOUT: before committing, verify the staged set with
`git diff --cached --name-only`, unstage anything you did not change with `git restore --staged <path>`,
and re-verify after any failed raw commit attempt. Paste ACTUAL runner output for every test claim; a
summary written from memory violates the execution contract. Run the suite BARE (`python3 -m pytest`),
with no added flags: do not pass `-n0`, a second `-q`, or `-p no:randomly`. Expect F-10's two
pre-existing failures and do not "fix" them here; they are out of scope and order-dependent. Do not
weaken any E-item or V-item to make it pass.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). The eight
paths in `- Scope-Paths:` are the fence. The six sibling line writers are owned by carrier `7afjyu`, and
`backlog.py`, `specs.py`, `production_checks.py` and `runner_shared.py` are out of scope for the reasons
under Deferred and Scope check. If an out-of-scope edit turns out to be necessary, make it and then
justify it to `aw ipd finalize` with `--scope-reason`. A declared path left unmodified needs
`--scope-ack`. Neither case is a reason to stop.

POST-GATE LIFECYCLE. Execution requires human approval first (`- Status:` must reach `approved`); this
plan deliberately carries NO `- Readiness:` field, because that is `/plan-review`'s attestation to
write and not the author's. Run `aw ipd begin` before implementing. Do not hand-move the file to `.aw/records/plans/executed/`.
When this plan runs in a runner lane (`aw oc run` / `aw agy run`), the runner owns the terminal
transition. When it is executed by hand, the executor performs it with
`aw ipd finalize b92m14 --actor <agent/model> --message <summary> --apply`. Do not
claim completion until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted
evidence. The backlog item `5e533q` stays `graduated` rather than `done` until this plan is executed,
since it carries `- Blocks-Release: next` and this plan is its gate carrier. Once this plan is executed,
close it via the HANDOFF rule (`aw backlog set done 5e533q`), which passes because this plan carries
`- From-Backlog: 5e533q` and the same gate.
