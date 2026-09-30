# Review findings: plan a21sr5

- Subject-Id: a21sr5
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5f678687` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` with ZERO findings BEFORE semantic review, and `--phase
review-finalize --agent` reports `conforming` with ZERO findings after the revisions, so nothing here
was structural. No pre-review snapshot was owed: the plan was committed and unmodified (`git status
--short` empty) and the lane-input copy under `.aw/state/lane-inputs/rev-6/` is byte-identical
(`diff -q` reports IDENTICAL). Bare suite on the clean tree at review HEAD: `3312 passed, 2 skipped,
3 warnings in 197.05s`.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW, and its value
rests entirely on EXECUTING the design rather than re-reading the prose. That is what it did, and
that is what found the blocker: the plan's own claims all hold, and the design it proposes
nonetheless breaks three passing tests.

WHAT THE REVIEW ACTUALLY DID, because the method is the finding. It built a throwaway scratch repo
under `tempfile` (never inside this checkout) with one plan carrying no `- Status:` (id6 `ab12cd`)
beside one well-formed plan (`ef34gh`), ran all eight surfaces capturing each exit code separately,
then STAGED THE E-02 CHANGE IN `agent_workflows/attention.py` and ran the whole suite. The staged
file was restored with `git restore` (not `git stash`, per the plan's own correct warning about this
shared checkout), and the restore was verified by an empty `git diff --stat` plus a re-run of the
three affected test files (`58 passed`).

EVERY ONE OF THE PLAN'S THIRTEEN FINDINGS REPRODUCES. F-01: `scan` does `drift.extend(rec_drift)`
then `if rec is None: continue`, and the per-tree branches return `(None, drift)`, exactly as
described. F-02 reproduces including its stronger-than-stated claim: `-id --all`, `--paths --all` and
`--filenames --all` each printed ZERO BYTES on stdout while exiting 1, so a caller piping the output
cannot distinguish "no such artifact" from "your artifact is broken". The board printed `0 artifacts
shown` under a `VIEW INVALID` header (exit 1); `--json` returned `"items": []` with `"valid": false`
and `schema_version` 4, naming the file only under `violations` (exit 1); `-s to-review --all`
narrowed to nothing (exit 1); `--check` named the file (exit 1). F-03: the cited test
`test_E03_a_token_naming_a_MALFORMED_artifact_is_matched_not_a_typo` appears in NO file under
`tests/`, and `git log -S` finds it added by `dcac396d` and removed by `19313eed`, while the behavior
still ships (the `drift_locations` rung is live in `selector_match_facts`, whose docstring describes
this very defect), so it is an unpinned live behavior exactly as the plan says. F-04: the enum is
exactly the five names, and `test_five_classes` asserts both the frozenset and
`set(ATTENTION_CLASS_ORDER) == ATTENTION_CLASSES` in one method. F-05's taxonomy is exact: the two
fatal status rules come from the six `_record_for` branches while `unreadable`, `duplicate-path` and
`unclassified-tree` are scan-level. F-06 reproduces end-to-end: the staged scan returned
`[('ef34gh','to-review','ready'), ('ab12cd','-','blocked')]` with the `attention.missing-status`
drift intact, the board gained `## blocked (1)` while KEEPING its `VIEW INVALID` header, the selector
`ab12cd` matched, and `render_json` listed both ids with `valid` still `false` and `schema_version`
still 4. F-07's dispatch property holds (below). F-08 holds and its live counts hold: 3 `blocked`
items, 0 gateless. F-09/F-11 boundaries confirmed. F-12 confirmed: `m867ox` is under `executed/`.
F-13 confirmed from `whatnext.md` Step 1.

THE BLOCKER (F-14). Staging the change and running the suite took it from `3312 passed` to
`3 failed, 3309 passed`. The user-visible regression is in `aw search`: `cli.py` builds `item_map`
from `att.scan(repo_root)`, then does `file_status = item_map[resolved_p].native_status` and falls
back to reading the file only `if not file_status`. A degraded item supplies the TRUTHY string `-`,
so the fallback is PREEMPTED and the artifact is compared against the requested statuses as `-`,
matching none. `tests/test_cli_search.py::SearchOptionsTests::test_status_filter_comma_separated` and
`::test_status_filter_repeated_flags` both fail with `AssertionError: 2 != 4` and both pass on the
clean tree. The third failure, `tests/test_prompts_attention.py::PromptsScanTests::test_scan_prompts`
(`AssertionError: 7 != 6`), is a legitimate contract change rather than a defect: its fixture holds a
deliberately unbucketed prompt that emits `attention.missing-status` and therefore becomes a seventh
item, which is precisely what this plan wants, so the count must move to the new contract rather than
be loosened. The plan's own `## Required tests / validation` named `test_attention.py` and
`test_attention_contract.py` as the at-risk suites; review measured BOTH still green (`39 passed` for
the former), so the plan's risk assessment pointed away from every place the damage lands.

THE ROOT CAUSE OF THE BLOCKER IS A CENSUS FAILURE (F-15), which is why the fix is two E-items and
not one patch. The plan's safety argument rests entirely on `partition._is_runnable`, and that
argument is CORRECT and re-verified. But `attention.scan` has FIVE consumers, and F-07 analyzed one.
The other four: `cli.py`'s doctor/status metrics site (aggregates `attn_by_class`, so a degraded item
increments `blocked` by one, which is the intended feature); `cli.py`'s search verb (the regression);
`releases.py::release_blockers_for` (calls `attention.release_blockers`, so the plan's no-false-blocker
property arrives through a SECOND caller it did not know it was protecting; review verified
`release_blockers` returns `[]` because `it.blocks_release` is `None`); and `runner_shared.py`'s
run-start validity report (reads `drift` only, never `items`, so it is genuinely untouched). A change
that adds a row to a widely consumed list must enumerate its consumers.

WHAT THE PLAN GOT RIGHT AND I RE-VERIFIED RATHER THAN TRUSTED (F-16). `action_for_status("plan", st)`
returns `undetermined` for `"-"`, `""`, `None` and `"unknown"`; `runner_action("plan", "-")` returns
`undetermined` with and without `full_auto=True`; `_is_runnable` excludes both `ACTION_SKIP` and
`ACTION_UNDETERMINED`, so a degraded plan is unreachable for dispatch BY CONSTRUCTION rather than by
a guard the plan has to add. OQ-02's `re.Match` trap is real: both `parse_clustered` and
`parse_clustered_prefix` return a Match with no `.get`, and `m.group("id6")` yields `ab12cd`, so the
plan's insistence on `.group` rather than `.get` prevents a silently empty id that would have
reproduced the very failure being fixed. F-08's gateless property holds: every `.gate` consumer
guards on truthiness, and rendering a gateless `blocked` item through both real renderers raised
nothing. The `blocked` reuse is also right on the spec's own terms: Section 6 defines `blocked` as
work intended to continue that a gate prevents, and Section 8.4's gate MUST governs a `deferred`
artifact's FRONT MATTER, not a synthesized view row, so OQ-01's resolution is sound.

ONE MEASUREMENT WORTH RECORDING FOR THE EXECUTOR (F-17). This repository has ZERO fatal-status drift
today: `scan` over the checkout returns 1969 items and 0 drift. So the fix is unobservable on the real
tree and every test must build a fixture. The plan's F-08 quotes 1886 items, now 1969, which is
exactly why the plan's own convention forbids a live count as a bar; no E-item depends on it, so this
is drift and not a defect. Separately, and useful before writing fixtures: `backlog.parse_item`
terminates its metadata block at a leading `# ` H1, so a fixture whose first line is a title never
reaches its `- Status:` bullet, while real tracked records begin with the bullet block and parse
correctly. A fixture in the wrong shape pins a parser quirk instead of this plan's behavior.

NO SPEC AMENDMENT IS OWED, and I checked this rather than accepting the plan's word. The
`attention-registry-and-cross-tree-status` spec fixes the vocabulary at five in decision 2, G1,
Section 6 and F1; this plan adds no class, so all four stay true. Section 8.3's JSON shape is
unchanged (a new row in an existing array, `schema_version` still 4, verified by execution). Section
8.6's fail-closed rule is strengthened rather than weakened, since the artifact is now ALSO a row.
`grep` over `docs/*.md` for `attention_class` matches nothing, so no user doc pins the item shape.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | D. Anti-regression / E. Testing | `agent_workflows/cli.py` search verb (`item_map` from `att.scan`, then `file_status = item_map[...].native_status` with the fallback guarded by `if not file_status`); `tests/test_cli_search.py::SearchOptionsTests::test_status_filter_comma_separated` and `::test_status_filter_repeated_flags`; `tests/test_prompts_attention.py::PromptsScanTests::test_scan_prompts` | The design as written BREAKS THREE PASSING TESTS, measured by staging E-02 and running the suite (`3312 passed` -> `3 failed, 3309 passed`). `aw search -s <status>` reads the scan's `native_status`; a degraded `-` is truthy and preempts the read-the-file fallback, so the artifact matches no requested status. The plan's own at-risk suite list named `test_attention.py`/`test_attention_contract.py`, both of which stay green, so its risk assessment pointed away from the damage. | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | Added E-06 (fix the search site so a degraded item carries no status FOR FILTERING, without weakening E-02 or making `native_status` falsy) and E-07 (re-pin the prompts test to the new contract, count 6 -> 7 plus an explicit `-`/`blocked` assertion, and census every consumer). Added `agent_workflows/cli.py` and `tests/test_prompts_attention.py` to `- Scope-Paths:`; added V-06/V-07 demanding before/after failure evidence; raised `- Highest E allocated:` to 07; warned E-05 to expect the three failures before E-06/E-07 land. |
| PR-002 | HIGH | UNDER-SCOPE | C. Architecture and operability | `grep -rn "attention\.scan\|att\.scan\|_att\.scan" agent_workflows/*.py` -> `partition.py`, `cli.py` x2, `releases.py`, `runner_shared.py` | F-07's safety argument analyzed `partition.py` ALONE while `attention.scan` has FIVE consumers. The dispatch conclusion is correct and re-verified, but it was never the whole safety question, and the omitted consumer is where PR-001 lives. `releases.py` also reaches the no-false-blocker property through a second caller the plan did not know it was protecting. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-07 requires a five-row consumer census with each effect classified BY EXECUTION and evidence pasted. F-07 amended in place to record that it analyzed one consumer of five. F-15 added. |
| PR-003 | MEDIUM | IN-SCOPE | G. Plan executability (evidence accuracy) | plan F-10 versus `.aw/records/plans/pending/20260929-qbfor9-01-r61br4-*.ipd.md:9` `- Scope-Paths:`; plan F-08's `1886 items`; plan `## Scope check` over-scope claim | Three evidence inaccuracies, none changing a conclusion but each capable of misleading the executor. F-10 omits `agent_workflows/runner_shared.py` from `r61br4`'s declared paths. F-08's `1886 items` has drifted to 1969 (the plan's own convention forbids a live count as a bar, and no item depends on it). The Scope check claimed "no existing test is edited, weakened or deleted", which PR-001's fix makes false. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 corrected in place with the missing path and a note that the boundary conclusion is unchanged (verified: `r61br4` touches neither `_record_for` nor the drop site). F-17 records the 1969 measurement as drift, not defect. Scope check now states honestly that exactly one existing test is RE-PINNED to an intended behavior change. |
| PR-004 | MEDIUM | IN-SCOPE | G. Plan executability (contract conformance) | spec `ipd-structure-and-linting` Section 5.3 (`For every E-NN, exactly one V-NN MUST exist`, matching numeric suffixes are the canonical mapping) | The two review-added items were first drafted as `E-02a`/`E-02b`, a suffixed form the spec's strict `E-NN`/`V-NN` bijection does not admit. Recorded because it was caught and corrected inside this review rather than shipped. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Renumbered to `E-06`/`E-07`, relocated into a new Task group 4 so E-ids follow document order, and given matching `V-06`/`V-07`. `aw ipd lint --phase review-finalize` conforms with 7 E-items and 7 V-items. |

### Decisions

ID | Question | Chosen | Alternatives considered | Basis | Reversible
D-1 | The design regresses `aw search -s`. Fix it at the producer (withhold the item or make `native_status` falsy) or at the consumer (`cli.py`)? | At the CONSUMER. E-06 makes the search site treat a degraded item as carrying no status for filtering, falling through to `_artifact_status` exactly as it does today for a file the scan never produced. | (a) Withhold the degraded item from the scan when any consumer might misread it, rejected because it deletes the entire deliverable; (b) make `native_status` empty rather than `-`, rejected because `-` is what the board must render and an empty value would silently change every other surface's display; (c) REPLAN the plan as unsound, rejected because the defect, the design and the safety properties are all verified correct and the regression is one consumer's truthiness assumption, which is a bounded edit. | Measured: `cli.py`'s `file_status = item_map[resolved_p].native_status` followed by `if not file_status: file_status = _artifact_status(p, text)`; staged suite run `3 failed, 3309 passed` versus clean `3312 passed` | yes
D-2 | `tests/test_prompts_attention.py` asserts 6 prompt items and the change makes 7. Loosen the assertion, delete it, or re-pin it? | RE-PIN: move the count to 7 AND add an assertion that the new item carries `native_status == "-"` and class `blocked`. | (a) Loosen to an inequality, rejected because a count that no longer states an intent is worse than the failure; (b) delete the test, rejected as destroying coverage to make a change pass; (c) treat the failure as a defect and suppress degraded items for the prompts tree, rejected because an unbucketed prompt is exactly the malformed artifact this plan exists to surface. | `tests/test_prompts_attention.py::PromptsScanTests::test_scan_prompts` fixture item 7 (`20260920-no-bucket.prompt.md`) and its `assertEqual(len(prompt_items), 6)`; the plan's own Goal | yes
D-3 | `cli.py` is now in scope and pending `r61br4` also declares it. Declare an `- Item-Dependencies:` edge? | No edge. Fence the edit to the search verb's status-filter site instead, and say so in the scope fence. | (a) `Item-Dependencies: executed:r61br4`, rejected because the two edit different functions in the file (that plan works in the attention Run-column row renderers, verified by search that it touches neither `_record_for` nor the drop site), and a false ordering edge would delay this release-blocking bug fix behind unrelated work; (b) leave the overlap unmentioned, rejected because a future executor needs to know which half of `cli.py` is not theirs. | `.aw/records/plans/pending/20260929-qbfor9-01-r61br4-*.ipd.md:9` `- Scope-Paths:` and its E-items; searched that plan for `_record_for`/`drift.extend`/`if rec is None` -> no matches | yes
D-4 | Is `blocked` genuinely correct for an unparseable artifact, given Section 8.4's "a `deferred` artifact MUST carry a gate"? | Yes, `blocked` with `gate=None`. OQ-01's resolution stands. | Adding a sixth `invalid` class, rejected on measured cost: it edits `attention_contract.py` (declared by two live pending plans), breaks `test_five_classes`' two assertions, needs a palette entry, and falsifies an `implemented` spec that says "five" in four places including a `[Must]` goal, converting a narrow release-blocking bug fix into a contract change. | spec Section 6 table (`blocked` = work intended to continue but a named GATE prevents progress); Section 8.4's MUST is scoped to a `deferred` artifact's front matter; verified all nine `.gate` consumers in `attention.py` guard on truthiness and that both real renderers accept a gateless item | yes
