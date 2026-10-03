# Review findings: plan izh17y

- Subject-Id: izh17y
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-1001 (HIGH, fixed), PR-1002 (MEDIUM, fixed), PR-1003 (MEDIUM, fixed), PR-1004 (MEDIUM, fixed), PR-1005 (LOW, fixed), PR-1006 (LOW, fixed), PR-1007 (MEDIUM, fixed)

## Round 1

Reviewed at HEAD `7a9e4be3c` in an isolated review lane. The plan file was committed and byte-identical
to the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `{"outcome":"clean","exit":0,"findings":0}`
BEFORE semantic review; `--phase review-finalize --agent` reports `clean` after revision. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator child-row check does not apply.

BOTH DEFECTS REPRODUCE EXACTLY AND THE PRESCRIBED FIX IS PRECISELY RIGHT, which is worth stating first
because the findings below are all about reasoning and validation rather than about the change itself.
Driven at review: `set_from_backlog_line("- Status: to-review\n- From-Backlog:\n- Id: abc123\n",
"zzz999")` returns text with TWO `- From-Backlog:` lines, `set_blocks_release_line` does the same, and
`set_priority_line` and `set_from_spec_line` on the identical input shape each return ONE. F-03's
unrepairability reproduces in full: four successive writes leave the junk line present every time, and
clearing with `-` removes the GOOD line and leaves the junk one. The regex E-01 prescribes
(`(?m)^- Blocks-Release:[ \t]*[^\n]*$\n?`) is character-for-character the sibling shape modulo the field
name, matches the empty, whitespace-only, tab-only and valued cases, and provably cannot cross a newline.
The two setter defects reproduce on both surfaces: `aw ipd set to-review <plan> --from-backlog nosuch`
exits 0 and persists the dangling link, and `aw specs set <spec> --status draft --from-backlog nosuch`
does the same through the forked `specs.run_set`. F-02, F-04 (plan gets `IPD-M102`, spec gets nothing),
F-07, F-08 (zero corrupt artifacts), F-09 (zero writer coverage) and F-10 (verbatim at
`attention.py:816`) all hold, as does the `cli.py` fork citation and the whole `0ykozn` -> `71wqol` ->
this plan provenance chain, whose deferred rows name `71wqol` twice for exactly these two defects.

THE ONE SERIOUS FINDING IS PR-1001, AND IT IS A CASE OF A RIGHT ANSWER REACHED BY A WRONG ARGUMENT. F-05
and OQ-01 are the plan's load-bearing judgement: they decline the backlog item's request to loosen the
READER patterns alongside the writers. That conclusion is correct. The stated reason is not. Both
documents argue that "the duplicate ALWAYS sits SECOND, so a strict reader skips the junk line and a
tolerant one stops at the empty first line", and I measured both halves to be false. The ordering is not
invariant: `set_blocks_release_line("- Blocks-Release:\n- Status: to-review\n- Id: abc123\n", "next")`
puts the JUNK line FIRST, because the strip cannot see the empty line and the insert lands after the
`- Status:` anchor wherever that happens to be, so the junk-first order is reachable from an ordinary
tooled write. And on the junk-SECOND order a properly line-bounded tolerant reader returns the REAL
value, not `''`, so the stated mechanism does not even fire on the case F-05 calls universal. The `''`
figure F-05 reports came from a comparison pattern using `\s*`, which crosses newlines and actually
captures `'- Blocks-Release: next'`, a "value" containing a bullet; no reader would be written that way.
The audit's answer survives on the half of F-05 that needs no ordering assumption: `\S+` cannot match an
empty value at all, so a strict reader cannot be fooled into reporting ABSENT, whereas a tolerant one
captures `''` which `source_link_is_absent` then reports as absent, losing a real gate. That is the
argument the plan now carries, in F-05, F-11, OQ-01, the Goal section and the Deferred row. This matters
beyond tidiness: the ordering claim is exactly the kind of premise a later author would lean on when
deciding whether some third site may be loosened, and it would lead them wrong.

PR-1002 widens that same audit. The plan treats the reader population as two patterns in one module;
there are FOUR across two, because `production_checks.py` declares its own
`_ITEM_FROM_BACKLOG_RE = (?m)^-[ \t]*From-Backlog:[ \t]*(\S+)[ \t]*$` and uses it at four call sites. The
conclusion covers it unchanged, and that module correctly stays out of `- Scope-Paths:`, but a reader
checking "the readers are correct" needs to be able to find every reader, and V-01's
outright-failure clause needed to name it so a stray edit there is caught too.

PR-1003 is the finding most likely to cause a later wrong "fix". E-03/E-05 correctly copy the
`--from-spec` guard's empty-set skip, and I verified why that posture is right. But `check_from_backlog`
has NO such guard, and its own docstring says so at length, calling itself "the less safe" twin,
recording that on a tree with neither corpus it returns one FALSE finding where the spec-side checker
returns none, and instructing "Do NOT 'harmonize' that guard away ... the difference is a known gap
here, not a standard to spread." I reproduced both behaviors. So after this plan the setter will permit a
write the checker then reports at `error` on the same tree, and E-05's fail-safe test will be pinning
precisely that disagreement. Correct in both places, but it must be written into the guard's comment and
the test's docstring, or the next reader finds a mismatch and deletes the skip.

PR-1004: the suite is not green at base and the plan records no baseline at all. Bare `python3 -m pytest`
at review HEAD gives `1 failed, 3480 passed, 2 skipped`, the failure being a DATE BOMB in
`tests/test_backlog.py` (it asserts a `2026-09-30` history line against a setter now writing
`2026-10-01`). That module exercises the very setter path E-03 modifies, so an executor following
V-02/V-05's instruction to paste the summary line with no baseline to compare against would plausibly
attribute it to their own guard. The bar is now a failing-node-id SET re-derived before any edit. I also
measured `aw check plans` and `aw check backlog` both exiting 1 at base, so neither is a pass bar either.

PR-1007 is small but would have cost real time: E-04 says to use "the same resolution as E-03", and
`existing_backlog_ids` takes a `repo_root` that `specs.run_set` does not have. That function derives one
per use with its own `_repo_root_of(path)`, which its existing `from_backlog_arg` block already calls. An
executor copying E-03 literally would reach for `Path.cwd()` or a fresh `find_project_root`, either of
which can make the guard consult a different tree than the write three lines below it. Named explicitly
now. PR-1005 (a spec-sync proof citing `tests/test_run_flag_surface.py`, which does not exist) and
PR-1006 (E-01 calling the no-anchor fallback "correct" when it silently drops the caller's value) are the
two LOW rows; both conclusions survive, only their statements needed correcting.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1001 | HIGH | IN-SCOPE | D. Anti-regression / evidence accuracy (a correct conclusion resting on a false premise) | `releases.set_blocks_release_line("- Blocks-Release:\n- Status: to-review\n- Id: abc123\n", "next")` -> `'- Blocks-Release:\n- Status: to-review\n- Blocks-Release: next\n- Id: abc123\n'`, i.e. junk line FIRST. On the junk-SECOND text, a line-bounded tolerant pattern `[ \t]*([^\n]*?)[ \t]*$` captures `'next'`, not `''`. The `''` in F-05 comes from a `\s*` variant that crosses newlines and captures `'- Blocks-Release: next'` | **F-05 and OQ-01 justify the plan's central judgement (leave the readers alone) with the claim that "the duplicate always sits SECOND", and BOTH halves of that claim are false:** the ordering is not invariant (junk-first is reachable from an ordinary tooled write, measured), and on the junk-second order the tolerant reader returns the real value, so the stated mechanism never fires on the case called universal. The conclusion is right; the reasoning a later author would rely on to judge a third site is wrong | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-05, OQ-01, the Goal section and the Deferred row all re-argued on the ordering-INDEPENDENT ground that holds: `\S+` cannot match an empty value, so a strict reader cannot be fooled into reporting ABSENT, while a tolerant one captures `''` which `source_link_is_absent` reports as absent, losing a real gate. The withdrawn ordering claim and the bogus `\s*` comparison are both recorded as withdrawn in new finding row F-11 rather than silently deleted |
| PR-1002 | MEDIUM | UNDER-SCOPE | G. Plan executability (an audit whose population is incomplete) | `production_checks.py:27` declares `_ITEM_FROM_BACKLOG_RE = re.compile(r"(?m)^-[ \t]*From-Backlog:[ \t]*(\S+)[ \t]*$")`, used at `:168`, `:329`, `:342-343` and `:349`. The plan names only `releases._ITEM_BLOCKS_RELEASE_RE` and `releases._ITEM_FROM_BACKLOG_RE` | The backlog item asks for "the readers" to be audited in the same pass and the plan answers for two of FOUR patterns across two modules. The conclusion covers the fourth unchanged (it is a reader, and it is more tightly bounded than its cousins), but an audit that does not enumerate its population cannot be checked, and a later author finding an unmentioned copy would reasonably conclude the audit was partial | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New conventions bullet enumerates all four readers with the `production_checks` copy's exact pattern and call-site count, states the conclusion covers it, and records that the module deliberately stays out of `- Scope-Paths:`; the Deferred row and the Scope-check under-scope limit both restated over the full population; V-01's outright-failure clause now names the third pattern too |
| PR-1003 | MEDIUM | IN-SCOPE | C. Architecture (a deliberate divergence left unstated, inviting its deletion) | `releases.check_from_backlog` docstring: "THE TWO BACK-LINK TWINS DISAGREE ON FAIL-SAFETY, AND THIS ONE IS THE LESS SAFE ... Do NOT 'harmonize' that guard away to match this function; the difference is a known gap here, not a standard to spread." Reproduced on a scratch repo with a plan carrying both links and neither tree: `check_from_backlog` -> 1 finding, `check_from_spec_dangling` -> 0 | E-03/E-04 correctly copy the `--from-spec` empty-set skip, so after this plan the SETTER permits a write on a backlog-tree-less repo while `aw check` reports it dangling at `error`, and E-05's fail-safe test pins exactly that disagreement. The trade is right in both places, but with neither the guard's comment nor the test's docstring saying so, the next reader who notices the mismatch is invited to delete the skip, reintroducing the false-refusal mode the skip exists to prevent | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires the divergence be written into the guard's comment citing `check_from_backlog`'s own docstring, and forbids both adding the guard to the checker and dropping the skip; E-05 requires the fail-safe test's docstring to record it and forbids asserting on `aw check` there; V-03 fails the item if the comment is silent; new finding row F-12 records the reproduction and the `known_spec_ids`-union precedent for why the skip is load-bearing |
| PR-1004 | MEDIUM | IN-SCOPE | E. Testing and verification (no baseline against a non-green suite) | Bare `python3 -m pytest` at HEAD `7a9e4be3c`: `1 failed, 3480 passed, 2 skipped, 3 warnings in 87.54s`; the failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, asserting a `2026-09-30` history line against a setter writing `2026-10-01`. `aw check plans` -> 1, `aw check backlog` -> 1 | **The plan tells the executor to run the suite bare and paste the summary line but never says what the base looks like, and the base is not green.** The one live failure is a date bomb in a module that exercises the setter path E-03 modifies, which is the worst possible coincidence: an executor would attribute it to their own change. The prescribed `aw check` runs are likewise already red for unrelated reasons | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | A BASELINE FIRST paragraph added to Required tests, naming the node id and its date-bomb cause and requiring the failing-node-id SET be re-derived before any edit; V-02 and V-05 both now require pasting the failing set and comparing as a SET, never as a count, with an explicit warning against attributing the `tests/test_backlog.py` failure to this plan; both `aw check` exit codes recorded as non-bars; the execution gate carries the obligation; new finding row F-13 |
| PR-1005 | LOW | IN-SCOPE | Evidence accuracy (a spec-sync proof citing a nonexistent file) | `tests/test_run_flag_surface.py` does not exist. The nearest real module, `tests/test_flag_surface_uniformity.py`, tests presentation and interactivity flag acceptance behaviorally and contains no `25kzda`, no `spec.md` and no section reference | The Spec/documentation sync section exists precisely to show a VERIFIED conclusion rather than an omission, and one of its three verifications names a file that is not there. The conclusion holds (E-03/E-04 add no flag, and the real module reads no spec), but an unverifiable proof defeats the section's purpose | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The paragraph now names the real module, states that it pins no spec file and reads no `.spec.md`, and records the corrected citation explicitly rather than quietly swapping it; new finding row F-14 |
| PR-1006 | LOW | IN-SCOPE | Evidence accuracy (a behavior called "correct" that silently drops data) | `releases.set_blocks_release_line("Some prose with no bullets at all.\n", "next")` returns its input unchanged, discarding the caller's value. `set_blocks_release_line("- Id: aaa111\n", "next")` does insert | E-01 lists "the returned-unchanged final fallback" among things that are "all correct". It is not correct, it is a silent data loss on a text with neither `- Status:` nor `- Id:`. The instruction to leave it alone is right, so nothing about the diff changes, but calling a silent drop correct could license an executor to rely on it or a later author to cite this plan as having blessed it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 reworded to call the fallback OUT OF SCOPE rather than correct, with the measured silent-drop behavior stated, the note that it is unreachable from any real record (every record type requires `- Id:`), and an explicit prohibition on "improving" it in passing since that would change a shipped writer's contract for every caller; recorded as the fourth under-scope limit in the Scope check |
| PR-1007 | MEDIUM | IN-SCOPE | G. Plan executability (an instruction that cannot be followed literally) | `specs.run_set(args)` holds no `repo_root`; it derives one per use with `specs._repo_root_of(path)` ("Walk up from a spec file to the repo root ... falling back to cwd"), and its existing `from_backlog_arg` block calls `blocks_release_of_item(_repo_root_of(path), from_backlog_arg)`. `backlog.existing_backlog_ids(repo_root)` requires a root | E-04 says to use "the same `backlog.existing_backlog_ids` resolution" as E-03, but E-03's surface has `repo_root` in hand and this one does not, so the instruction cannot be followed literally. The likely improvisations (`Path.cwd()`, or a second `find_project_root` call) each let the guard consult a different tree than the gate-inheritance lookup three lines below it, which is a silent wrong answer rather than a visible failure, and the second also violates P8 | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now names `_repo_root_of(path)` explicitly, states that the adjacent inheritance lookup already uses it, and says why a second derivation is a silent wrong-answer shape; it also specifies placing the refusal before the in-memory `set_from_backlog_line` write so V-04's byte-identical assertion is meaningful rather than incidental; V-04 fails the item if the guard resolves against a different root; new finding row F-15 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | F-05's conclusion (leave the readers strict) is right but its reasoning is false. Correct the reasoning in place, or mark the plan REPLAN because its central judgement was unsound? | Correct the reasoning in place and record the withdrawal as a new finding row | REPLAN. REJECTED: the CONCLUSION is independently correct on a premise the plan already contains (a tolerant reader captures `''` and `source_link_is_absent('')` is `True`), so the judgement stands and only its justification needed repair, which is a bounded edit. Silently swapping the argument. REJECTED: the ordering claim appears in four places and a later author may already have read it, so the withdrawal must be visible and dated, which is what F-11 is for. Loosening the readers after all, since the stated reason failed. REJECTED on measurement: the ordering-independent argument shows a tolerant reader turns a malformed line into a confident ABSENT, which is a real regression path through `check.blocking-item-closed-without-gate` | The junk-first measurement; the line-bounded tolerant reader returning `'next'` on junk-second text; `ipd_schema.source_link_is_absent("")` -> `True`; `_ITEM_BLOCKS_RELEASE_RE.search` -> `None` on a lone empty-valued line | yes |
| D-2 | The setter's empty-set skip will disagree with `check_from_backlog`, which has no such guard. Add the guard to the checker too, drop the skip, or keep both and document? | Keep both and document the divergence at the guard and in the fail-safe test | Adding the empty-set guard to `check_from_backlog`. REJECTED on an explicit in-code instruction: that docstring records the gap and says "Do NOT 'harmonize' that guard away ... not a standard to spread", and `releases.check_from_backlog` is not in `- Scope-Paths:`, so the change would be both out of scope and contrary to a recorded decision. Dropping the setter's skip to match the checker. REJECTED: that reintroduces the false-refusal mode on any redirected or backlog-less layout, which is the one way this plan could break an unrelated project | `check_from_backlog`'s docstring; the reproduced 1-finding versus 0-finding asymmetry on a scratch repo; `check_engine.known_spec_ids`'s docstring measuring that a single authority returns EMPTY under an externally-redirected layout while the artifact plainly exists | yes |
| D-3 | Should this review file a backlog item for the fourth reader copy in `production_checks.py`, or for the checker-side empty-set gap? | Neither. Record both in the plan (F-11's companion bullet and F-12) and file nothing | Filing an item for the `production_checks` copy. REJECTED: it is a READER and the audit's conclusion is that readers are correctly strict, so there is no defect to carry; an item would assert one. Filing an item for the checker's missing empty-set guard. REJECTED: the code already records that gap deliberately and forbids harmonizing it, so it is a known accepted asymmetry rather than undiscovered debt, and a review must not create work it was not asked for | The four `production_checks` call sites all being read paths; `check_from_backlog`'s docstring explicitly declining the guard; plan-review Step 2.4 (fix in the owning plan, cross-reference elsewhere) | yes |
| D-4 | The base suite carries one pre-existing failure caused by a hardcoded date. Should this review fix it? | No. Record it as the baseline the executor must re-derive, and change no test | Fixing `test_release_exempt_setter_roundtrip_and_parity`. REJECTED: this workflow reviews planning documents only and must not change code or tests; the file is also outside this plan's `- Scope-Paths:`. Ignoring it. REJECTED: it sits in a module E-03's path exercises, so an executor would misattribute it, which is precisely PR-1004 | plan-review's opening constraint (review planning documents only); the reproduced failure and its `2026-09-30` versus `2026-10-01` diff; `tests/test_backlog.py` exercising the `status_set` path | yes |
