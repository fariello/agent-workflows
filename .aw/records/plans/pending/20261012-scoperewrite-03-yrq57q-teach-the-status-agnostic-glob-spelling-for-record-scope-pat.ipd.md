# IPD: Teach the status-agnostic glob spelling for record Scope-Paths entries as optional author guidance

- Date: 2026-10-12
- Kind: child
- Concern: A plan that declares a `.aw/records/` artifact in `- Scope-Paths:` by its LITERAL status-directory path (for example `.aw/records/backlog/open/<name>.backlog.md`) goes stale the moment that record changes status, because a status transition relocates the record between disposition directories. `guti33` re-tiered the resulting `check.scope-path-target-stale` `moved` finding to `info`, and `5h3qyy` shipped an opt-in, default-OFF citation rewriter (D159). Backlog `ho7qjb` carries the ZERO-CODE alternative both of those plans recorded and declined to mandate: spell such an entry status-agnostically, `.aw/records/<type>/**/<exact-filename>`, so a status move cannot stale it. Authoring re-drove every behavioral claim in the item and all hold (F-01), measured that the widening trade-off is NARROWER than the item states (F-02), and found one cost the item does not state: the stale-target check is blind to a glob entry, so a mistyped glob is silent at `aw check` (F-03). The decision this plan records is to TEACH the spelling as OPTIONAL, RECOMMENDED guidance for record entries, NOT to mandate it, and NOT to add a `check` advisory nudging toward it (OQ-01, OQ-02).
- Scope: IN: (a) a behavior test module pinning the existing code behaviors the guidance relies on, so the guidance cannot silently become false; (b) one DECISIONS.md entry recording the ruling, the options, and the measured trade-offs; (c) one additive paragraph in the IPD structure spec Section 4.5 stating the recommended spelling and its trade-offs, plus an `aw specs note` history line; (d) one guidance subsection in this repo's plans README and the identical subsection in the shipped plans-README template that `engine` installs into managed repos; (e) one CHANGELOG line. OUT: any production code change (none is needed, F-01); a `check` advisory nudging literal record entries toward the glob (declined, OQ-02); making the glob form REQUIRED or lint-enforced (declined, OQ-01); teaching the looser id6-glob form `**/*-<id6>-*.<facet>.md` (deferred, see Deferred); rewriting any existing plan's literal entries (other parties' files, and `5h3qyy`'s opt-in rewriter already exists for that); changing the `5h3qyy` rewriter or its default (OQ-01 of that plan, a separate maintainer call).
- Scope-Paths: tests/test_scope_paths_status_agnostic.py, DECISIONS.md, .aw/records/specs/**/20260802-1904-01-ipd-structure-and-linting.spec.md, .aw/records/plans/README.md, .aw/system/workflows/templates/plans-README.md, .aw/system/managed-sections.json, CHANGELOG.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: ho7qjb
- Set: scoperewrite
- Order: 3
- Highest E allocated: 06
- Author: opencode/claude-opus
- Id: yrq57q

## Workflow history
- 2026-10-12 reviewed (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005. Record: .aw/records/reviews/20261012-scoperewrite-03-yrq57q-teach-the-status-agnostic-glob-spelling-for-record-scope-pat.review.md

- 2026-10-12 to-review (opencode/claude-opus): graduated from backlog `ho7qjb`. Re-drove every behavioral claim in the item at HEAD `649280be1` (all hold, F-01); measured that the widening loss applies only when the glob entry itself is ADDED mid-execution, not to a plan that declares it at authoring (F-02); found the stale-target check is blind to a mistyped glob (F-03). Recommends optional guidance, no mandate, no check advisory (OQ-01, OQ-02). This plan's own spec entry dogfoods the spelling.
- 2026-10-12 draft (opencode/claude-opus): created.

## Goal

Record the maintainer-facing decision on the status-agnostic `Scope-Paths` spelling and, as recommended, teach it as optional author guidance for `.aw/records/` entries, with its trade-offs stated honestly, so fewer plans are authored with entries that a routine status move will stale. Pin the code behaviors the guidance depends on with outcome tests so the guidance stays true.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure the base

- [ ] E-01 Re-drive the F-01, F-02 and F-03 probes at execution HEAD with a `python3 -c`/heredoc script against the real modules (no source reading): for the entry `.aw/records/backlog/**/<name>.backlog.md`, (a) `ipd_schema._scope_path_entry_error` returns `None` and `ipd_schema.parse_scope_paths` returns it intact and non-grandfathered; (b) `ipd_lifecycle._scope_match` is True for that name under `open/`, `graduated/` and `done/` and False for a different name in the same directory; (c) `ipd_lifecycle.scope_entry_is_literal_file` returns False for it; (d) in a scratch repo under the system temp dir, `check_engine.stale_record_scope_paths` reports a literal `open/` entry whose record sits in `graduated/` as `moved`, returns `[]` for the glob form of the same record, and ALSO returns `[]` for a glob naming a record that does not exist; (e) `ipd_lifecycle.frozen_region_comparison` on a receipt built from a plan declaring the glob at authoring accepts (`widening_is_acceptable` True) a later ADDED literal entry, and refuses (eligible False, reason naming "DIRECTORY or GLOB") a later ADDED glob entry; (f) with the record in `backlog/done/`, the literal `open/` entry is classified `moved-terminal` and the glob form returns `[]` (F-06). Append a dated re-measurement line to Findings with each result. If (a), (b), (e) or (f) disagrees with Findings, mark this item `blocked`, because the guidance would then be false.
  - Depends on: none
  - Expected outcome: a dated re-measurement line in Findings; no source file modified.
  - Execution state: pending

### Task group 2: Pin the behavior the guidance relies on

- [ ] E-02 Add `tests/test_scope_paths_status_agnostic.py` (stdlib `unittest`, scratch repos under `tempfile.TemporaryDirectory`, following the fixture style of `tests/test_scope_path_target_stale.py`), calling the real functions and asserting only on their return values (GUIDING_PRINCIPLES P16: no source reading, no caller counts, no docstring pins). Pin (each a separately named test): (a) the glob form is a legal `Scope-Paths` entry (`_scope_path_entry_error` is `None`, `parse_scope_paths` keeps it, not grandfathered); (b) `_scope_match` matches the exact basename under every backlog status directory and under every spec status directory, and does NOT match a different basename in the same directory or a basename with a suffix appended; (c) `stale_record_scope_paths` reports the literal form `moved` after a relocation and reports nothing for the glob form; (d) the KNOWN BLIND SPOT: `stale_record_scope_paths` also reports nothing for a glob that matches no file (pinned as current behavior, with a test docstring citing F-03 so a future change to it is a deliberate decision); (e) the widening asymmetry from F-02: a receipt frozen over a glob-bearing scope accepts an added literal entry and refuses an added glob entry; (f) the runner-facing half of F-06 at the predicate level: with the record in a TERMINAL directory (`backlog/done/`), the literal `open/` entry is classified `check_engine.SCOPE_STALE_MOVED_TERMINAL` (one of the two classifications the dispatch gate refuses) while the glob form returns `[]`. Pin (f) at the `stale_record_scope_paths` return value only; do not drive the runner (the dispatch gate's consumption of that classification is already covered by `tests/test_scope_path_target_stale.py`).
  - Depends on: E-01
  - Expected outcome: a new passing test module pinning (a) through (f).
  - Execution state: pending

### Task group 3: Record the decision

- [ ] E-03 Append ONE `### D<n>` entry to `DECISIONS.md`, re-deriving `<n>` as one more than the highest existing `### D` heading at execution time (D162 was highest at authoring; do not trust that figure), in the house shape (`- **Context:**`, `- **Decision:**` with rejected alternatives and trade-off inside it, `- **Applied:**`). It states: the question from backlog `ho7qjb`; the three options (mandate the glob; teach it as optional guidance; do nothing and rely on `guti33`'s `info` tier plus `5h3qyy`'s opt-in rewriter); the chosen posture (optional, recommended guidance; no lint requirement; no `check` advisory); the trade-offs F-02 and F-03 measured; and that it composes with D159 rather than replacing it. Append only; modify no existing entry.
  - Depends on: E-01
  - Expected outcome: an append-only diff adding exactly one decision entry.
  - Execution state: pending

### Task group 4: Teach it

- [ ] E-04 Amend Section 4.5 ("The `Scope-Paths` allowlist") of the IPD structure spec (`20260802-1904-01-ipd-structure-and-linting.spec.md`, currently under `.aw/records/specs/implemented/`; resolve its live directory at execution) with ONE added paragraph placed after the "Implicit lifecycle-artifact allowances." paragraph, headed "Status-agnostic record entries (recommended, optional)." It states: a `.aw/records/` artifact SHOULD be declared as `.aw/records/<type>/**/<exact-filename>` so a status move does not stale it; the form is legal under the existing grammar and matches only that basename; the two costs (an entry ADDED in that form mid-execution is not widening-eligible, while one declared at authoring is frozen in the receipt and needs no widening; and neither `check.scope-path-target-stale` nor the runner's dispatch-time stale-target refusal examines glob entries, so a mistyped one is neither reported nor refused and surfaces only at finalize as declared-but-unmodified, which a runner auto-acknowledges (F-03, F-06)); and that the literal form stays valid. Cite the E-03 decision number. Change no other text and do not change the spec's `- Status:`. Then run `aw specs note <spec> --message "Section 4.5 amended (scoperewrite yrq57q E-04): recommend optional status-agnostic glob spelling for .aw/records/ Scope-Paths entries (D<n>)"`.
  - Depends on: E-03
  - Expected outcome: a one-paragraph additive diff in Section 4.5 plus one workflow-history line; no other spec change.
  - Execution state: pending

- [ ] E-05 Add a `## Declaring records in Scope-Paths` subsection to `.aw/records/plans/README.md`, placed immediately before `## Execution contract in every plan's gate`, and add the IDENTICAL subsection text at the corresponding position (immediately before `## Execution contract in every plan's gate`) in `.aw/system/workflows/templates/plans-README.md`, the template `engine` installs as a managed repo's plans README. The text is short (at most about 12 lines): one worked example contrasting `.aw/records/backlog/open/<name>.backlog.md` with `.aw/records/backlog/**/<name>.backlog.md`; that the glob form survives a status move and is RECOMMENDED but OPTIONAL; the two costs from E-04 in one sentence each (the second naming both `aw check` and the runner's dispatch refusal); that it applies only to `.aw/records/` artifacts, never to source paths, where a literal entry is what keeps the fence tight; and a pointer to spec Section 4.5. Do not reword any other text in either file. Then set the `sha256` of the `".aw/system/workflows/templates/plans-README.md"` entry in `.aw/system/managed-sections.json` to the template's new `sha256sum` (F-07; precedent `15df1952f`), changing no other entry.
  - Depends on: E-04
  - Expected outcome: one new subsection in each of the two files, byte-identical between them; the manifest entry equals the template's new sha256; no other change.
  - Execution state: pending

- [ ] E-06 Add one CHANGELOG bullet under the existing `## 2.0.0 (pending)` heading, prefixed `Changed:`, stating that the plans README and the IPD spec now recommend spelling a records entry in `Scope-Paths` as `.aw/records/<type>/**/<filename>` so it survives a status move, and that the literal form remains valid. No new heading; do not reword neighbouring bullets; no em or en dashes (user-facing prose).
  - Depends on: E-05
  - Expected outcome: exactly one new CHANGELOG bullet.
  - Execution state: pending

## Project conventions discovered (Step 0)

- NO CODE IS NEEDED. The backlog item's own measurements and F-01 show the spelling works today end to end; this plan changes guidance, records a decision, and pins existing behavior.
- TWO PLANS READMEs. `.aw/records/plans/README.md` is this repo's own copy; `.aw/system/workflows/templates/plans-README.md` is the template `engine` maps to `<plans>/README.md` when installing a managed repo (the `(f"{dirs['plans']}/README.md", "plans-README.md")` target). They have diverged in other sections, so E-05 adds the same subsection to each without attempting to re-sync them. The guidance is toolkit-generic, so it belongs in the shipped template too.
- `tests/test_ipd_lint.py` asserts on substrings of the template (`"finalize transaction"`, `"IPD-S406"` and others); E-05 is additive, so those still hold, and the bare suite run confirms it.
- `DECISIONS.md` is the durable decision home (D159 is the precedent for this Set), append-only, `### D<n>.` headings with Context / Decision / Applied bullets.
- A plan that edits a spec declares it in `- Scope-Paths:`; `runner_shared.declared_spec_paths` recognizes a spec by its `.spec.md` facet, so the glob entry this plan uses for its own spec is still announced (driven: it returns the glob string verbatim).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Where | Finding and evidence |
|---|---|---|---|
| F-01 | MEDIUM | `ipd_schema._scope_path_entry_error`, `ipd_schema.parse_scope_paths`, `ipd_lifecycle._scope_match`, `check_engine.stale_record_scope_paths` | **EVERY CLAIM IN THE ITEM HOLDS, DRIVEN at HEAD `649280be1`.** For `.aw/records/backlog/**/20261002-scoperewrite-01-ho7qjb-x.backlog.md`: `entry_error: None`; `parse: ([...the entry...], False, [])`; `_scope_match` True under `open/`, `graduated/`, `done/`; False for `.aw/records/backlog/open/20261002-scoperewrite-01-abcdef-y.backlog.md`; `scope_entry_is_literal_file` False. In a scratch repo with the record in `graduated/`: literal `open/` entry -> `[StaleScopePath(path='.aw/records/backlog/open/...', classification='moved', resolved=('.aw/records/backlog/graduated/...',))]`; glob entry -> `[]`. Same for specs: `_scope_match('.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md', '.aw/records/specs/**/20260802-1904-01-ipd-structure-and-linting.spec.md')` True, and False for the same path with `x` appended. Also matches a sharded `executed/202610/` plan path. |
| F-02 | MEDIUM | `ipd_lifecycle.frozen_region_comparison`, `widening_is_acceptable` | **THE WIDENING COST IS NARROWER THAN THE ITEM STATES.** Eligibility is judged only over ADDED entries (`for entry in added: if not scope_entry_is_literal_file(entry)`). Driven with a receipt frozen over `a.py, <glob>`: adding literal `b.py` -> `eligible= True accept= True`; adding a second glob -> `eligible= False accept= False added Scope-Paths entry would widen the fence to a DIRECTORY or GLOB rather than a literal`. So a plan that declares the glob AT AUTHORING loses nothing at finalize; only an author who ADDS a glob entry mid-execution loses widening-eligibility, and that is the existing anti-neutering rule working as designed. |
| F-03 | MEDIUM | `check_engine.stale_record_scope_paths` | **A MISTYPED GLOB IS SILENT AT `aw check`.** The predicate skips any entry containing `*`, `?` or `[` before examining it, so a glob that matches no file at all also returns `[]` (driven: `.aw/records/backlog/**/20261002-zz-01-zzzzzz-nope.backlog.md` -> `[]`). The literal form would be reported `vanished`. The backstop is finalize's two-way reconciliation: a declared entry nothing modified is listed as in-scope-unmodified and needs a `--scope-ack`. This is a real cost of the spelling and is why the guidance must state it and why it stays optional (OQ-01). |
| F-04 | LOW | `.aw/records/plans/pending/` | Live adoption is near zero: of 39 `.aw/records/` entries across 69 pending plans' `Scope-Paths` lines at authoring, 1 uses a glob; `stale_record_scope_paths` reports 0 stale entries across pending plans today (the population turns over daily, so this is context, not a target). |
| F-06 | MEDIUM | `runner_shared.execute_item_core` (planstale `6h8j1r` E-04 dispatch refusal) | **THE BLIND SPOT ALSO REACHES THE RUNNER, NOT ONLY `aw check`** (found at review). The runner refuses to DISPATCH an execute item whose `stale_record_scope_paths` result contains a `moved-terminal` or `vanished` entry (`item["status"] = "fail-gate"`, `scope_target_refusal`). Re-measured at review in a scratch repo with the record in `done/`: literal `open/` entry -> `[StaleScopePath(..., classification='moved-terminal', ...)]` (refused at dispatch); glob form -> `[]` (dispatched). That is the DESIRED outcome for a record that merely moved, but a glob naming a record that does not exist (typo, or a record later deleted) also returns `[]` and so dispatches, where the literal form would be refused `vanished` before a turn is spent. The backstop is still finalize's declared-but-unmodified reconciliation, which under a runner is AUTO-acknowledged (`runner_shared.compute_scope_reconciliation`: `"declared-but-unmodified (auto-acknowledged by ...)"`), so under `aw oc run`/`aw agy run` a mistyped glob surfaces only as an auto-ack line in the finalize record. The guidance must say so plainly. |
| F-07 | MEDIUM | `.aw/system/managed-sections.json` | **EDITING THE SHIPPED TEMPLATE MOVES ITS RECORDED HASH** (found at review). The manifest records `".aw/system/workflows/templates/plans-README.md": {"kind": "file", "sha256": "a51a115c..."}` while the file on disk at review HEAD already hashes `b782b27e...` (it drifted when `2d6247e41` and `e490e228c` edited the template without touching the manifest). Precedent for refreshing a manifest hash in the same change as the edit: `15df1952f` (`dalmk4`). The manifest drives install consent and drift (`engine` "Per-section consent/drift via the IPD-01 manifest"), so E-05 must leave the entry equal to the file's new sha256. |
| F-05 | LOW | `runner_shared.declared_spec_paths` | A glob spec entry is still announced as a declared spec edit (driven: returns `['.aw/records/specs/**/20260802-1904-01-ipd-structure-and-linting.spec.md']`), printed as the pattern rather than a resolved path. Cosmetic; not worth a code change in a guidance-only plan. |

## Proposed changes (ordered, validatable)

1. Re-drive the probes at execution HEAD (E-01).
2. Pin the relied-on behavior, including the known blind spot, in a new test module (E-02).
3. Record the ruling in DECISIONS.md (E-03).
4. Amend spec Section 4.5 and note it in the spec history (E-04).
5. Add the guidance subsection to both plans READMEs (E-05).
6. Add the CHANGELOG line (E-06).

## Deferred / out of scope (with reason)

- **A `check` advisory nudging literal record entries toward the glob.** Declined; see OQ-02.
  - Carrier-Declined: the existing `check.scope-path-target-stale` already reports the moment a literal entry actually goes stale, at `info`, which is the actionable signal; a pre-emptive nudge on every correct literal entry would be noise and would steer authors toward a form with the F-03 blind spot.
- **Teaching the looser id6 form `.aw/records/<type>/**/*-<id6>-*.<facet>.md`, which also survives a regroup or re-slug.** Not taught here: it matches by id6 rather than exact name, which is a looser fence and a further convention for authors to learn, and the regroup hazard is being addressed for in-flight plans by `69pxm5`.
  - Carrier-Declined: no one has asked for it; the exact-basename form covers the measured problem (status moves), and a later maintainer request can extend the same spec paragraph.
- **Closing the F-03/F-06 blind spot by teaching `stale_record_scope_paths` to report a glob matching nothing** (which would also restore the dispatch refusal, since the runner consumes the same predicate). A code change outside this guidance plan's purpose.
  - Carrier-Declined: finalize's declared-but-unmodified reconciliation already backstops it, and adoption is optional and near zero (F-04); if adoption grows, the pinned test from E-02 marks exactly where to change it.

## Scope check

- Over-scope: none. Each declared path is written by a named E-item: the test module (E-02), `DECISIONS.md` (E-03), the IPD structure spec (E-04, declared in the status-agnostic form this plan teaches), both plans READMEs and the shipped template's manifest hash (E-05), `CHANGELOG.md` (E-06).
- Under-scope: none known. No production module is declared because no code changes (F-01). `.aw/records/plans/README.md` is under the implicit plans allowance anyway but is declared explicitly because it is deliberately edited content, not a lifecycle artifact.

## Required tests / validation

- `python3 -m pytest tests/test_scope_paths_status_agnostic.py tests/test_scope_path_target_stale.py tests/test_ipd_schema.py tests/test_ipd_lint.py` for the new and directly adjacent surfaces.
- `python3 -m pytest` run BARE (configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`), with the actual `N passed` summary line pasted; no added flags.
- `aw specs check` on the amended spec and `aw ipd lint` on this plan, each reporting conforming.

## Spec / documentation sync

AMENDS the IPD structure spec (`20260802-1904-01-ipd-structure-and-linting.spec.md`) Section 4.5 (E-04), declared in `- Scope-Paths:` in the status-agnostic form so both runners announce the spec edit (F-05). WHY: Section 4.5 is the canonical home of the `Scope-Paths` grammar and match semantics, and the recommendation plus its trade-offs are statements about that grammar; putting them only in a README would let the spec and the guidance drift. The amendment adds one paragraph and removes nothing. User-facing docs: the plans README and its shipped template (E-05) and the CHANGELOG (E-06).

## Open questions

### OQ-01: Mandate the status-agnostic spelling, teach it as optional guidance, or do nothing?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED as a recommendation for the maintainer to ratify by approving this plan: teach as OPTIONAL, RECOMMENDED guidance. MANDATING it is rejected on repo evidence: `guti33` and `5h3qyy` (D159 option 3) both declined it as a convention change for every author, and F-03/F-06 show a real cost (a mistyped glob is silent at `aw check` AND skips the runner's dispatch-time `vanished` refusal) that a mandate would impose on everyone. DOING NOTHING is rejected because F-01 and F-02 show the spelling prevents the stale-target finding at the source at near-zero cost when declared at authoring, and teaching it costs no code. The choice is reversible (guidance text and one decision entry) and composes with D159's opt-in rewriter. If the maintainer prefers a mandate or no guidance, `/plan-review` revises E-03 through E-06 before approval.

### OQ-02: Add a `check` advisory nudging literal records entries toward the glob form?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: no. The backlog item names it only as "possibly". A literal entry is valid and fences tighter on duplicate-name edge cases, so an advisory on every such entry would fire on correct plans; the actionable moment (the entry actually going stale) is already reported by `check.scope-path-target-stale` at `info`. Recorded in Deferred with `Carrier-Declined`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted dated re-measurement line in Findings plus the actual printed output of the probe script for each of (a) through (f), including the `StaleScopePath(... classification='moved' ...)` line for the literal entry, the two `[]` results, the two `eligible=`/`accept=` lines, and the (f) `moved-terminal` line beside its glob `[]`. The observation is produced by the E-01 script itself. A statement that it "was re-measured" is not evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted targeted run of `tests/test_scope_paths_status_agnostic.py` showing it passing, with behaviors (a) through (f) each mapped to a named passing test (names non-binding); quoted assertions showing the tests assert only on return values of the called functions and never read production source (P16); and the pasted BARE `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff DECISIONS.md` showing additions only, exactly one new `### D<n>` entry with Context, Decision (three options, rejected alternatives, trade-off citing F-02 and F-03) and Applied bullets, citing D159 and backlog `ho7qjb`; plus pasted evidence of the highest `### D` heading before the edit showing no number collision.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff` of the IPD structure spec showing exactly one added paragraph in Section 4.5 (after "Implicit lifecycle-artifact allowances.") naming both costs (including that the dispatch refusal is skipped, F-06) and citing the E-03 decision number, one added workflow-history line, no removed lines, and an unchanged `- Status:` line; plus pasted `aw specs check` output for that spec.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `git diff` of both plans READMEs showing one added `## Declaring records in Scope-Paths` subsection in each immediately before `## Execution contract in every plan's gate`, no other change; and a pasted comparison (for example `diff` of the extracted subsection from each file) showing the two subsections are byte-identical; and a pasted check that the added text contains no em or en dash; and pasted `sha256sum .aw/system/workflows/templates/plans-README.md` beside `git diff .aw/system/managed-sections.json` showing exactly that one `sha256` value changed to match.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `git diff CHANGELOG.md` showing exactly one added `Changed:` bullet under the existing `## 2.0.0 (pending)` heading, no other change, and no em or en dash in the added line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires `/plan-review` and explicit human approval before execution. Approving it also ratifies OQ-01's recommendation (optional guidance, no mandate, no check advisory).

Execution contract: commit only the files named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE and paste the actual runner output; never claim a test result that was not produced. Mark an `E-*` item `performed` only after performing it, and a `V-*` item `pass` only after inspecting the evidence in a separate pass. Do not claim done until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item carries concrete pasted evidence with `Result: pass`. Ownership of the transition is conditional: in a managed runner lane (`AW_EXECUTION_ROLE=worker`) the RUNNER owns `aw ipd begin`/`aw ipd finalize`, so the executor commits its work and leaves the move to the runner; executing BY HAND, run `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal move. Never hand-edit the status or `git mv` the file. SCOPE FENCE: `- Scope-Paths:` is a declaration the finalize reconciliation compares against; if the work genuinely requires a file outside it, make the edit and JUSTIFY it with `--scope-reason <path>=<why>` (and `--scope-ack` for a declared path left unmodified), never silently. Open questions: OQ-01 and OQ-02 resolved, none blocking.

A NOTE ON THIS PLAN'S OWN EXECUTION: E-01 and the tests build scratch repositories under the system temp directory, never inside the checkout.
