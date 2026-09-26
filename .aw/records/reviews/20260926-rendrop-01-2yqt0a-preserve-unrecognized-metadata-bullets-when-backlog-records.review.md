# Review findings: plan 2yqt0a

- Subject-Id: 2yqt0a
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5316357f`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before revision; `--phase review-finalize` conforms after. No pre-review
snapshot was needed: the plan was committed at `2c7068ca` and unmodified, and the lane-input copy is
byte-identical to the tracked file.

EVERY AUTHORED FINDING REPRODUCED. F-1: `_render_item` emits exactly the six template fields plus the
two gate fields when blocked. F-3: both `elif` preservation branches are present. F-4: `close_on_answer`
calls `_render_item(item, body)` with no re-apply, and it has no caller. F-2 and F-5 I drove live on two
identical scratch repos, and the result is exactly what the plan claims, including the part most reviews
would have taken on trust:

```text
----- A (--status parked)              ----- B (positional parked)
- Id: aaa111                           - Id: aaa111
- Status: parked                       - Status: parked
- Graduated-To: foo                    - Blocks-Release: next
- Blocks-Release: next                  - Set: demo
- Set: demo                            - Custom-Field: keepme
- Priority: medium                     - Priority: medium
- Work-Kind: chore                     - Work-Kind: chore
- Summary: demo item                   - Graduated-To: foo
                                       - Summary: demo item
```

`Custom-Field` is GONE on the left, and `Graduated-To`/`Blocks-Release` have been relocated under
`Status` even though they survived. So F-5's central design claim is right: appending unknowns after the
template would not make the two blocks equal, and only a source-order walk does. The plan's diagnosis and
its chosen shape are both correct, and its line numbers are accurate.

**THE PLAN FIXES THE SMALLER HALF OF ITS OWN CONCERN.** This is the finding that changes what the plan is
worth. `_strip_metadata_and_history` returns only the text AFTER the history block, so prose written
between the metadata bullets and `## Workflow history` is DELETED by every `--status` write. That is the
same defect as the dropped field (a fixed-template rebuild discarding what it does not own), it is the
concern the plan's own `- Concern:` line describes, and it is measurably far larger. Six of 620 live items
carry such prose. On the one that is still `open`:

```text
original length: 3063
body extracted length: 0
re-rendered length: 443
```

2620 bytes of a live bug report, deleted, exit 0, no warning, while the positional spelling preserves it
(measured on the same item in a second scratch repo). Had this plan shipped as authored, it would have
declared the renderer's preservation property fixed and left the bigger loss in place, with a passing
test suite asserting the two spellings now agree on metadata. Added as E-07 and F-9, with V-07 requiring
the reproduction re-run on a COPY of that real item.

**E-03 AS AUTHORED OPENS A RELEASE-GATE HOLE RATHER THAN CLOSING ONE.** The plan sells E-03 as fixing "a
SILENT RELEASE-GATE DROP if it were ever called on a gated item". Preserving `Blocks-Release` through a
transition to `done` does not preserve a gate, it manufactures the exact state
`check_engine.evaluate_blocking_close` exists to refuse, and I measured that no shipped check can see it:

```text
evaluate_blocking_close(...) -> legitimate=False, severity='error',
  "backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate"
check_release_gates(root)            -> 0 findings
check_release_gate_consistency(root) -> []
```

The reason is structural and deliberate: rule 1 iterates `_staged_backlog_done_items`, so it examines only
a close STAGED in the current commit, and `close_on_answer` never stages. Today the field is dropped,
which is a DIFFERENT bug; E-03 would replace a visible loss with an invisible policy violation. Added as
E-08 (refuse at the writer, via the same shared predicate `backlog.run_set` already calls) and F-11, with
V-08 requiring the raise plus proof the file was not written.

**THREE WAYS E-01's WALK WOULD HAVE PRODUCED A MALFORMED ITEM, none of which any validator catches.**
I tested each rather than reasoning about it. (1) An item carrying BOTH `- Kind: chore` and
`- Work-Kind: bug` is legal at HEAD (`parse_item` dual-reads, canonical wins) and `validate_item` returns
`[]`; E-01's in-place substitution as written emits `- Work-Kind: bug` twice, and `validate_item` returns
`[]` on that too. (2) `- Gate-Summary:` is not template-owned and not on `BacklogItem.__slots__`, yet
`aw set blocked <item> --gate-summary ...` writes one onto a backlog item (measured, exit 0, because
`_GATE_STATUS_BY_TYPE` maps `backlog`), so a verbatim walk preserves a stale gate summary onto a `done`
item and `validate_item` again returns `[]`. (3) The bullet-block boundary `parse_item` uses ENDS at an
indented sub-bullet (measured: a `  - indented sub bullet` stopped the scan and a later `- Custom-Field:`
was never parsed), so a walk that assumes every bullet matches `- Key: value` becomes a second silent-drop
path. E-01 now carries four numbered rules covering these plus the non-reordering property, and V-01
requires one pasted render per rule. Added as F-7, F-8, F-10.

**ONE TEST ITEM COULD HAVE SELF-COMMITTED INTO ITS OWN FIXTURE.** E-04's spelling A omitted
`--no-commit`, and `_add_commit_flags(p_backlog_set)` plus `_offer_records_commit`'s
`assume_yes` mean `--yes` (and `--commit`) is read as commit consent. In a scratch repo with no initial
commit it merely warned ("cannot resolve HEAD"), which is why the omission looks harmless; in a fixture
that does commit it would commit. Every `cli.main` call in E-04 and E-09 now passes `--no-commit`
(F-12).

**WHAT I DID NOT CHANGE.** OQ-01's resolution (preserve in the renderer rather than route through
`apply_status_change`) is correct and I re-verified its basis: the positional path reaches neither
`evaluate_blocking_close` nor `decide_gate_default` nor `--evidence`. The three Carrier-Declined
deferrals stand, and I re-ran the audit behind the first one (`grep -n "_render_item(" agent_workflows/*.py`):
`close_on_answer` really is the only other re-render of an existing record, `run_new` and
`promote_question_to_backlog` render new ones, and `specs.run_set` edits lines surgically. The
outcome-tests-only posture, the `source_text=None` default that keeps the new-record paths byte-identical,
and the `- Item-Dependencies: executed:wd6npl` edge are all sound. Right-sizing: the plan is now 9
E-items, all inside one module pair and one defect class, which is well under the 18-leaf threshold and
does not warrant splitting; E-07 and E-08 are each one focused pass with one test surface.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. correctness and data integrity (silent destruction of a live record's content) | `backlog._strip_metadata_and_history` ("Return only the free prose body (after the `## Workflow history` section)"); measured on `.aw/records/backlog/open/20260919-a3ugp1-01-a3ugp1-approval-gate-refuses-askme-resolved-plans.backlog.md`: 3063 bytes in, body extracted 0, re-rendered 443; 6 of 620 live items carry pre-history prose | **THE PLAN FIXES THE SMALLER HALF OF ITS OWN CONCERN: PROSE WRITTEN BEFORE `## Workflow history` IS DELETED BY EVERY `--status` WRITE.** Same root (a fixed-template rebuild discarding unowned source content), same verb, strictly larger loss (2620 bytes of a live bug report versus one dropped field line), and the positional spelling preserves it. Shipping as authored would have declared the renderer's preservation property fixed with this still broken and a green suite asserting the two spellings agree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-07 (capture and re-emit the source's pre-history region inside `_render_item`'s `source_text` walk) with F-9, V-07 (reproduction on a COPY of the real item, before/after `wc -c` plus an empty `diff` of the region, cross-checked against the positional spelling), a second CHANGELOG line in E-05, a test in E-09(a), and the `- Concern:`/`- Scope:`/approval paragraph updated to name it. Explicitly forbids "widen `_strip_metadata_and_history`" instead, because `_reattach_history` reassembles head + history + trailing body and would RELOCATE the prose after the history block rather than preserve it. |
| PR-002 | HIGH | IN-SCOPE | B. security-adjacent / D. domain invariants (a release gate rendered unenforceable) | `evaluate_blocking_close` on a `done` item carrying `Blocks-Release: next` with no carrier -> `legitimate=False, severity='error'`; `check_release_gates` and `check_release_gate_consistency` on the same tree -> 0 findings; `check_release_gate_consistency` rule 1 iterates `_staged_backlog_done_items` ("only a backlog item whose close-to-`done` is STAGED in THIS commit is examined") | **E-03's PRESERVATION MANUFACTURES A `done` ITEM CARRYING A LIVE RELEASE GATE, AND NO SHIPPED CHECK CAN SEE IT.** The plan frames E-03 as preventing a silent gate drop. Preserving the field through a close to `done` instead creates precisely the state the shared close predicate refuses, and because the backstop is commit-staged-scoped by design and `close_on_answer` never stages, the result is invisible. Today's drop is a different, visible bug; E-03 alone would trade it for an invisible policy violation. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | Added E-08: call the SAME shared predicate `backlog.run_set` already calls, on the rendered text, before `atomic_write`, and raise `ValueError` with the verdict's reason and fixes on an error verdict. Raising (not an exit code) matches this function's sibling `promote_question_to_backlog`, which already raises on a validation failure; the function has no CLI. Added F-11, V-08 (the raise plus an untouched source file plus the permitted handed-off case), a test in E-09(d), and adjusted E-03's V-03 and E-04(d) fixtures to carry a `From-Backlog` carrier so they exercise a LEGITIMATE close. Widening the staged scope of `check.blocking-item-closed-without-gate` is deferred with its reason. |
| PR-003 | HIGH | IN-SCOPE | A. correctness (an under-specified algorithm that silently produces malformed records) | measured: `- Kind: chore` + `- Work-Kind: bug` parses to `kind='bug'` with `validate_item` -> `[]`, and a doubled `- Work-Kind: bug` also -> `[]`; `aw set blocked <item> --gate-summary ...` wrote `- Gate-Summary:` onto a backlog item (exit 0) though it is absent from `BacklogItem.__slots__`, and a `done` item carrying it -> `validate_item` `[]`; `parse_item`'s boundary ends the block at an indented sub-bullet (measured) | **E-01's WALK AS SPECIFIED PRODUCES A DUPLICATE `Work-Kind` LINE, PRESERVES A STALE `Gate-Summary` ONTO A NON-BLOCKED ITEM, AND MAY DROP AN UNPARSEABLE BULLET, AND `validate_item` CATCHES NONE OF THE THREE.** "Substitute template-owned values in place" is ambiguous for an item carrying both kind spellings (both lines are template-owned and both would be substituted); `Gate-Summary` is a real field on this record type that the template does not own and the gate-drop rule as written does not mention; and the bullet walk assumes a shape the shared boundary does not guarantee. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now carries four numbered rules: (1) emit each template-owned key at most once, substituting a legacy `- Kind:` only when no `- Work-Kind:` was already emitted and otherwise dropping it; (2) treat `Gate-Summary` as a gate field for the drop rule, using the shared `attention_contract.GATE_SUMMARY_RE`; (3) pass a non-`Key: value` bullet through verbatim; (4) never reorder a key present in the source. V-01 requires one pasted render per rule; E-09(b) and E-09(c) pin (1) and (2) as tests. Added F-7, F-8, F-10. New `validate_item` rules for either malformed shape are deferred with their reason (neither state exists in the live tree: measured). |
| PR-004 | MEDIUM | UNDER-SCOPE | E. testing (a test that can mutate its own fixture repo) | `cli._add_commit_flags(p_backlog_set)`; `cli._offer_records_commit`'s `assume_yes = bool(getattr(args, "commit", False) or (getattr(args, "yes", False) and not is_agent_or_json))`; measured: spelling A in a scratch repo skipped the commit only because HEAD was unresolvable ("cannot resolve HEAD") | **E-04's SPELLING A OMITS `--no-commit` WHILE SPELLING B PASSES IT, SO THE TEST CAN SELF-COMMIT.** `--yes` is read as commit consent on this parser. In a fixture that commits (the shape `tests/test_specs_status_dirs.py` uses) the command would create a commit inside the test repo, which is both a side effect the test does not intend and a source of nondeterminism. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now passes `--no-commit` on every `cli.main` call and states why, with the measurement; E-09 carries the same requirement. Added F-12. |
| PR-005 | MEDIUM | IN-SCOPE | G. plan executability (a validation step that mutates tracked state) | V-07 as I first drafted it names a real tracked backlog item as its fixture; `- Scope-Paths:` does not include `.aw/records/backlog/` | **THE REPRODUCTION V-07 NEEDS USES A REAL TRACKED ITEM, WHICH AN EXECUTOR COULD MUTATE IN PLACE.** The only items exhibiting the PR-001 defect are live records; a validation that runs the setter against one directly would rewrite a tracked file outside the plan's declared scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-07 requires COPYING the item into a scratch repo, and the gate carries an explicit "DO NOT MUTATE A TRACKED BACKLOG ITEM WHILE VALIDATING" paragraph naming the scope-path reason. |
| PR-006 | LOW | IN-SCOPE | G. plan executability (stale counts and an under-described approval) | `- Highest E allocated: 06` against 9 E-items after revision; "four outcome tests, one CHANGELOG line" in the approval paragraph; "Under-scope: none known" | **THE WATERMARK, THE COUNTS, AND THE APPROVAL PARAGRAPH NO LONGER DESCRIBE THE PLAN, AND THE SCOPE CHECK CLAIMED NO UNDER-SCOPE WHILE PR-001 WAS UNDER-SCOPE.** A human approving from the summary would not learn that prose deletion and a release-gate refusal are part of what they are approving. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Watermark 06 -> 09; the approval paragraph rewritten into three numbered parts with the measured byte figure; `- Concern:`, `- Scope:`, `## Proposed changes`, `## Required tests / validation`, `## Scope check`, `## Spec / documentation sync`, and the cohesion rationale all updated; the Over-scope note now justifies why E-07 and E-08 are inside this plan's cohesion rather than scope creep. `aw ipd lint --phase review-finalize` conforms. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's `- Concern:` is about a template rebuild discarding unowned content. Review only the FIELD loss it enumerates, or test whether the same rebuild discards anything else? | TEST, and it discards far more: pre-history prose, 2620 of 3063 bytes on a live item. Fix it in the same plan (E-07). | (a) Review only the enumerated loss: rejected, it would approve a plan that declares this renderer's preservation property fixed while the larger loss remains, with a green suite as cover. (b) File it as a separate backlog item and let this plan ship: rejected, it is the SAME function, the SAME write, and the SAME concern sentence, so splitting would mean touching `_render_item`'s source walk twice and reviewing it twice; the second plan would also have to re-derive the walk this one is building. | `_strip_metadata_and_history` read in full; measured re-render of the real item (3063 -> 443) and a live-tree scan finding 6 of 620 items affected. | yes |
| D-2 | E-03 preserves `Blocks-Release` through a close to `done`. Accept it as the stated gate-drop fix, or check what state it produces? | CHECK, and it produces a `done` item with a live gate that no shipped check sees; add E-08 to refuse at the writer. | (a) Accept E-03 as written: rejected, measured that `evaluate_blocking_close` calls the state an error while `check_release_gates` reports zero findings on it, so E-03 alone converts a visible loss into an invisible policy violation. (b) Widen `check.blocking-item-closed-without-gate` beyond staged items instead: rejected, that scope is deliberate (its own comment states the grandfathering rationale) and changing it has a corpus-wide blast radius unrelated to this defect. (c) Drop E-03 entirely: rejected, the drop is real and the plan is right to fix it; refusing the illegitimate close is what makes the fix safe. | `evaluate_blocking_close` verdict, `check_release_gates` and `check_release_gate_consistency` results all measured on one scratch tree; rule 1's `_staged_backlog_done_items` scoping read in `check_engine`; `promote_question_to_backlog`'s existing `raise ValueError` as the established refusal shape for this module. | yes |
| D-3 | E-08 must refuse somehow. Raise, or return a sentinel / write a warning? | RAISE `ValueError` carrying the verdict's reason and fixes, writing nothing. | (a) Warn and write anyway: rejected, that is the invisible violation the finding is about. (b) Return None or a sentinel path: rejected, the function's signature returns a `Path` and every caller would have to learn a new contract; there are no callers today, so a raise costs nothing and fails closed. (c) Return an exit code: rejected, this function has no CLI and no exit-code contract. | `set_records.promote_question_to_backlog` already raises `ValueError` on a validation failure ("promoted backlog item failed validation"); `grep -rn close_on_answer agent_workflows tests` finds no caller. | yes |
| D-4 | `- Gate-Summary:` is not on `BacklogItem.__slots__`. Treat it as an unknown field to preserve verbatim, or as a gate field to drop? | DROP IT when the item is not `blocked`, treating it as a gate field. | (a) Preserve verbatim as an unknown field: rejected, measured that `aw set blocked --gate-summary` really writes it onto backlog items and that `validate_item` does NOT flag one on a `done` item, so preserving it would leave a stale "why this is blocked" line on a closed item with nothing to catch it. (b) Add it to `BacklogItem` and the template: rejected as scope creep; the field has no backlog-side reader and no live item carries one (measured: zero across 620). | The `--gate-summary` flag on `aw set`; `status_set._GATE_STATUS_BY_TYPE` mapping `"backlog": "blocked"`; the gate-write branch emitting `- Gate-Summary:`; `BacklogItem.__slots__`; `validate_item`'s gate check reading only `gate_kind`/`gate_ref`; a field census over the live tree. | yes |
| D-5 | A duplicate metadata bullet and a stale `Gate-Summary` are both invisible to `validate_item`. Add validator rules here, or only stop this renderer producing them? | ONLY STOP THIS RENDERER (E-01 rules 1 and 2); defer the validator rules with the reason recorded. | (a) Add both validator rules here: rejected, a new rule flags whatever pre-existing items carry those shapes and turns a scoped bug fix into a corpus question; the plan declares four files and neither rule belongs to them. (b) Say nothing about the gap: rejected, it is the reason the two defects are dangerous and a future reader needs it recorded. | Both states measured to produce zero drift; `aw check backlog --agent` conforms on the live tree today and the field census shows no item carrying either shape. | yes |

### Deferred and open

- (none). All six findings were FIXED in place, four of them by adding executable work (E-07, E-08, E-09,
  and E-01's four rules) rather than by rewording the plan. No open question needed the human: OQ-01 was
  already resolved and I re-verified its basis rather than re-asking, and every decision above is
  reversible by editing the plan before it executes.

Two deferrals are recorded in the PLAN's `## Deferred / out of scope` section rather than here, because
they are scope decisions about OTHER artifacts and not unfixed findings: new `validate_item` rules for a
duplicate bullet or a stale `Gate-Summary` (D-5), and widening the commit-staged scope of
`check.blocking-item-closed-without-gate` (D-2 alternative b). The first should be filed as a backlog
item when this plan executes; neither gates it.

HONEST LIMITS, stated because they bound what this round proves. I verified the DEFECTS, not the fixes:
I did not implement `source_text`, so that the walk's four rules compose correctly and that a new record
still renders byte-identically remains E-01's work and V-01's evidence. I did not run the bare suite
against a patched tree, so E-06 is a real obligation and not a formality. My live-tree measurement of
PR-001 covers the 6 items I found by scanning for a non-bullet line before the history heading; an item
whose pre-history prose begins with a `- ` bullet would not have been counted, so 6 is a floor rather
than an exact population. For PR-002 I measured one fixture and read the backstop's scoping; I did not
audit whether any real item has ever been closed through `close_on_answer`, and since it has no caller
the honest statement is that the hole is prospective rather than realized. Finally, E-09's `-k`
expressions name tests that do not exist yet, so the executor must adjust them to the real test names;
V-09 says so.
