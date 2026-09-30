# Review findings: plan 9m4ujh

- Subject-Id: 9m4ujh
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-601 (HIGH, fixed), PR-602 (HIGH, fixed), PR-603 (HIGH, fixed), PR-604 (MEDIUM, fixed), PR-605 (MEDIUM, fixed), PR-606 (LOW, fixed), PR-607 (LOW, fixed)

## Round 1

Reviewed at HEAD `4ba158fc` in an isolated review lane. The plan file was tracked, unmodified, and
byte-identical to the lane input (`diff` reported no difference), so no pre-review snapshot was needed.
Structural preflight `aw ipd lint --phase author --agent` reported `outcome: clean`, exit 0, ZERO findings
and no `IPD-Z602` density advisory BEFORE semantic review; `--phase review-finalize` reports `conforming`
after revision, including after the `- Item-Dependencies:` change.

I RE-RAN THIS PLAN'S WORK RATHER THAN READING ITS NUMBERS, AND ITS CENTRAL MEASUREMENTS ARE EXCELLENT.
F-01 reproduced verbatim on a real lane with a real begin receipt: `aw commit abc123 --
agent_workflows/demo.py` refuses exit 1 with `refusing - 1 finding(s) on
20260824-demo-01-abc123-demo.ipd.md` / `check.scope-drift: 1 changed path is outside the plan's declared
Scope-Paths: 'agent_workflows/render.py'`, with `_staged_paths(lane)` returning `[]`. F-04, the plan's
decisive argument, reproduced KEY FOR KEY with `ygb3nk`'s routing staged in memory: `run_commit` exit 0
printing the advisory, then `attribution_source: commit-cohesion`, `out_of_scope_paths: []`,
`disregarded_unowned_paths: ['agent_workflows/render.py']`, `committed_paths: ['agent_workflows/demo.py',
'agent_workflows/render.py']`. F-06 reproduced (`find_undeclared_leaves` returns `set()` before AND after
adding the flag to the built `commit` leaf; no test asserts `legacy_flags` completeness). F-07 reproduced
on all four argv shapes, including both broken orders returning the selector `'a/b.py=why'`. F-08
reproduced exactly, including the 12-key receipt set, the additive key surviving `read_receipt`,
`receipt_is_current` True and `finalize_precheck` exit 0. F-09's gitignore claim reproduced to the line
(`.aw/.gitignore:62:/state/`). F-02, F-03, F-05, F-10, F-11, F-12 and F-14 all resolve by symbol and
quoted content. So the defect is real, the store choice is sound, and the two falsifications of the
sibling plan's stated costs are correct.

WHAT REVIEW FOUND IS THAT THE PLAN MISREADS ITS OWN F-01 TRANSCRIPT, AND THE CONSEQUENCE IS AN EXECUTION
ORDER (PR-601). F-01's refusal wording is `refusing - N finding(s) on <plan>`, which is the ENGINE gate
(R2, `_validate_plan_via_engine`), not `run_commit`'s own `refusing - out-of-scope change(s) present`
(R1) which E-03 edits. `ygb3nk` F-02 had already drawn exactly this distinction and said so in as many
words ("F-01's measured refusal is R2's text, not R1's"). The plan nonetheless concluded the two refusals
are "independent sites" and that "either may execute first", and carried `- Item-Dependencies: none`. I
staged E-03's exemption in memory (patching `work_cmd._in_scope` so the reasoned path counts as in scope,
the minimal shape of the edit) with the partition untouched, and the same command STILL exits 1 on the
engine gate. The two branches are consecutive in `run_commit`; passing R1 lands on R2. So this plan
executed alone ships a flag that is accepted, recorded, and then overridden, with no user-visible escape.
`- Item-Dependencies:` is now `executed:ygb3nk`, which the linter accepts and which `ygb3nk`'s `approved`
status makes immediately satisfiable.

THE SECOND CORRECTION INVERTS A SAFETY CLAIM (PR-602). E-05, the Scope check, V-05 and the scope fence all
tell a reviewer that `_reconcile_scope` is "the shared arbiter for the CLI, `status_set`, and the runner's
`compute_scope_reconciliation`", and that feeding it a fuller map at finalize's one call site therefore
changes nothing for the other two. Measured, the census is TWO hits, both in `ipd_lifecycle.py`: the `def`
and ONE call inside `finalize`. `status_set` reaches it only by calling `finalize`
(`_delegate_plan_executed_to_finalize` -> `_life.finalize(..., scope_reasons=scope_reasons)`), and
`runner_shared.compute_scope_reconciliation` never calls it at all; it calls `finalize_precheck` to BUILD
a map the driver hands to `finalize`. So the edit is felt by all three, and the ONLY thing preserving the
runner is the merge order F-11 correctly identifies. That matters practically: a reviewer told the other
consumers are untouched will not scrutinise the merge order, which is the sole protection.

THE THIRD IS AN INSTRUCTION THAT CANNOT BE FOLLOWED AS WRITTEN (PR-603). E-03 says
"`_parse_scope_reason_flags` already rejects a malformed token; surface its error as a usage refusal (exit
2)". It rejects nothing: the body `continue`s past a token with no `=` and skips one whose path or why is
empty, returning `{}` silently. I measured `['noequals']`, `['=why']`, `['a/b.py=']` and `['a/b.py=  ']`
all returning `{}` with no exception. There is no error to surface, so the malformed case E-06(d) and
V-03(c) both demand would simply not exist, while E-03 also forbids writing a second parser. Resolved by
naming the actual mechanism: a token-count versus map-size comparison at the call site, parser still
reused.

THE FOURTH IS A FIXTURE TRAP I FELL INTO MYSELF, WHICH IS HOW I FOUND IT (PR-604). The plan rightly
insists every fixture needs a real lane, because `_plan_execution_tree` returns None without one and the
rule then reports nothing. What it never says is that the lane is resolved by `inspect_lane(repo_root,
plan_id)`, so the lane id must BE the plan's id6. My first F-01 probe allocated `cs-f01-lane` and measured
a FALSE GREEN: `_plan_execution_tree` None from every tree, `check_scope_drift` 0 findings, and the commit
that must refuse succeeding at exit 0, indistinguishable from a fixed defect. Renaming the lane to
`abc123` reproduced the refusal exactly. Every fixture in E-06 and E-07 would have hit this, and the
plan's own V-06(c) would have passed while measuring nothing. The fix is to assert the lane RESOLVES
rather than that one was created. I also hit `begin()` taking a plan PATH and having no `env` keyword,
which a fixture written from the plan's prose would get wrong.

WHAT I DELIBERATELY DID NOT FLAG. The plan's shape is right and its evidence discipline is unusually good:
it stages every mutation in memory rather than editing shared files, verifies `git status --short` empty
after each probe, states the no-lane false-green hazard as a convention, flags the `AGENTS.md` managed-block
question for the reviewer instead of silently omitting it, and its gate enumerates four silent-failure
shapes with the V-item that catches each. I left all three open questions resolved: OQ-01's store choice is
correct and I reproduced the measurement it rests on, OQ-02's refusal to mint a receipt from a commit verb
is the right call for the right reason, and OQ-03's conclusion (keep them separate) survives my correction
to its ordering clause. I did not flag the seven-item structure; each item has one deliverable, and the
linter raised no density advisory on any of them. I did not flag the absence of `- Readiness:`, which is
correct at `to-review` and which the plan explicitly explains.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | IN-SCOPE | C (sequencing); D (evidence reading) | plan `- Item-Dependencies: none`, Deferred row 1 ("the two refusals are independent sites"), OQ-03 ("either may execute first"); review probe staging E-03's exemption with the partition untouched -> exit 1 `refusing - 1 finding(s) on 20260824-demo-01-abc123-demo.ipd.md`; `ygb3nk` F-02 ("F-01's measured refusal is R2's text, not R1's") | **THE PLAN MISREADS ITS OWN F-01 TRANSCRIPT AND THEREFORE DECLARES NO DEPENDENCY IT ACTUALLY HAS.** F-01's refusal is the ENGINE gate's wording, not the `run_commit` branch E-03 edits. The two are consecutive, so passing R1 lands on R2, and E-03's exemption alone leaves the escape refused. Executed before `ygb3nk` this plan ships a flag with no user-visible effect, and an executor following V-03(b) would report a failure that is not this plan's defect | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-15 with the probe output. `- Item-Dependencies:` changed to `executed:ygb3nk` (linter still conforming). F-01 annotated to say which gate its wording names; E-03, the Deferred row, the Scope check under-scope note, OQ-03 and the gate's "why this exists alongside" paragraph all reconciled; V-03(b) now tells the executor what to paste when `ygb3nk` has not yet landed and forbids reaching for `_validate_plan_via_engine` to force it green |
| PR-602 | HIGH | IN-SCOPE | C (architecture); D (evidence accuracy) | plan E-05 / Scope check / V-05 / scope fence ("shared arbiter for the CLI, `status_set`, and the runner's `compute_scope_reconciliation`"); review census: `_reconcile_scope(` returns 2 hits, both in `ipd_lifecycle.py`; `status_set.py:1566` `result = _life.finalize(`; `runner_shared.compute_scope_reconciliation` calling `finalize_precheck` | **THE SAFETY CLAIM IS INVERTED: THE ONE CALL SITE IS THE ONLY CALL SITE, SO EDITING IT AFFECTS ALL THREE CONSUMERS.** `status_set` and the runner reach `_reconcile_scope` THROUGH `finalize`, so there is no untouched path. The merge order is the sole protection, and a reviewer told otherwise will not check it | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-16 with the census. E-05 now states what the call-site choice does and does not protect and names the merge order as the whole protection; the Scope check and the scope fence's fourth constraint reconciled; V-05(a) now requires the merge expression quoted and the winning side named, rather than a claim about which function was edited |
| PR-603 | HIGH | IN-SCOPE | E (testing); G (executability) | plan E-03 ("`_parse_scope_reason_flags` already rejects a malformed token; surface its error as a usage refusal (exit 2)"); the function's body (`if "=" not in raw: continue`, `if path and why:`) with no `raise`; review probe: `['noequals'] -> {}`, `['=why'] -> {}`, `['a/b.py='] -> {}`, `['a/b.py=  '] -> {}` | **THE MALFORMED-TOKEN REFUSAL CANNOT BE INHERITED FROM THE PARSER, WHICH SILENTLY RETURNS `{}`.** E-06(d) and V-03(c) both require an exit-2 refusal naming the malformation, while E-03 forbids a second parser and asserts an error that does not exist. As written the executor either cannot satisfy V-03(c) or writes the parser E-03 forbids | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-17 with the six measured inputs. E-03 now states the mechanism: compare the supplied token count against the parsed map size and refuse exit 2 naming the offending token, parser still REUSED for parsing. V-03(e) now requires the diff show the count comparison and explicitly warns that a diff claiming to "surface the parser's error" has misread it |
| PR-604 | MEDIUM | UNDER-SCOPE | E (testing); fixture correctness | plan Step 0 convention 3 and V-06(c) (require a lane, never say which name); `check_engine._plan_execution_tree` calling `_lease.inspect_lane(Path(repo_root), plan_id)`; review probe run twice: lane `cs-f01-lane` -> `_plan_execution_tree` None, 0 findings, `run_commit` rc 0; lane `abc123` -> the F-01 refusal at rc 1 | **THE LANE MUST BE NAMED FOR THE PLAN ID AND THE PLAN NEVER SAYS SO, SO EVERY FIXTURE HITS THE EXACT FALSE GREEN THE PLAN WARNS ABOUT.** A lane under any other name resolves to None, the rule reports nothing, and the commit that must refuse exits 0. V-06(c) as written ("build a REAL lane") would pass while measuring nothing. Review hit this on its own first probe | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-18 with both probe runs. E-06 and E-07 now require `allocate_worktree(root, <plan id6>)` and an assertion that the lane RESOLVES; V-06(c) requires `_plan_execution_tree(...)` pasted as non-None rather than a claim that a worktree exists; E-07 and V-06(d) also record `begin`'s real signature (plan PATH, no `env` keyword), which review hit as a `TypeError` writing the probe from the plan's prose |
| PR-605 | MEDIUM | IN-SCOPE | E (testing); live-artifact convention | plan F-13 and Required tests and Step 0 (`3246 passed, 2 skipped, 3 warnings in 50.69s` at HEAD `0d30004c`); review bare run at HEAD `4ba158fc`: `3322 passed, 2 skipped, 3 warnings in 103.05s`; `pyproject.toml` `addopts` reading `-m 'not slow and not livecorpus'` | **THE BASELINE MOVED 76 PASSES IN A DAY AND THE QUOTED `addopts` IS INCOMPLETE.** The plan already instructs re-derivation (correctly and repeatedly), but a reader comparing against the single transcribed figure would report a spurious delta; the Step 0 convention also quotes the marker expression as `-m 'not slow'`, omitting `not livecorpus` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both baselines recorded side by side with their HEADs in F-13, Step 0 and Required tests, with the 76-pass movement stated as the measured basis for the re-derivation instruction rather than a caution; V-01(c) now names both figures as non-bars; the `addopts` quote corrected to the full configured value |
| PR-606 | LOW | IN-SCOPE | G (records accuracy) | plan OQ-03 ("`ygb3nk` is already `reviewed` with `go-pending-approval`"); `ygb3nk` front matter: `- Status: approved`, `- Readiness: go-pending-approval` | **THE SIBLING'S LIFECYCLE STATE IS UNDERSTATED: IT IS `approved`, NOT `reviewed`.** This matters to the argument OQ-03 is making, since the cost of merging is now discarding a human approval as well as a review, and it is also what makes PR-601's new dependency edge immediately satisfiable rather than a stall | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-03 corrected with the re-read front matter and the date, noting the stronger consequence (a completed review AND a human approval would be discarded); the Deferred row and the gate paragraph both now note that `approved` makes the ordering edge satisfiable |
| PR-607 | LOW | IN-SCOPE | G (reproducibility) | plan Step 0 convention 4 (probes "under the gitignored `.aw/state/probe/`"); `git check-ignore -v tmp/cs/f01.py` -> `.gitignore:42:tmp/` | **THE PROBE-LOCATION CONVENTION NAMES ONE GITIGNORED DIRECTORY AS IF IT WERE THE ONLY ONE, AND DOES NOT NAME THE PREFERABLE PATCH SPELLING.** Both `.aw/state/` and the repo-root `tmp/` are gitignored; more usefully, the plan mandates in-memory staging without saying that a context-managed `patch.object` is what makes restoration automatic on failure | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 0 convention 4 now records both gitignored locations (each confirmed with `git check-ignore -v`) and states that review used `unittest.mock.patch.object` as a CONTEXT MANAGER, with the reason (it restores on exit including on exception) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-03's exemption does not make the escape reachable without `ygb3nk`. Declare a dependency, absorb `ygb3nk`'s change into this plan, or leave the plans unordered as authored? | Declare `- Item-Dependencies: executed:ygb3nk` | (a) Absorb the partition change here, rejected because it is `ygb3nk`'s single behavioral change, that plan is already `approved`, and two plans editing `work_cmd._validate_plan_via_engine` is how a Set produces a merge conflict and a double-counted change; this plan's own scope fence forbids it. (b) Leave unordered and note the limitation in prose, rejected because the ordering is a machine-consumable fact the queue sorter reads (`queue_sort_key`/`dependency_depth`) and prose does not reach it, so an unattended run could dispatch this plan first and produce a green execution whose deliverable has no effect | Measured: E-03's exemption staged in memory with the partition untouched still returns exit 1 on the engine gate, so the two refusals are consecutive rather than independent. `ygb3nk` is `approved`, so the edge is satisfiable now and costs no stall. The `executed:<id6>` spelling is already in use on six pending plans and the linter accepts it here | yes |
| D-2 | V-03(b) demands an exit-0 acceptance that cannot occur before `ygb3nk` lands. Weaken it, drop it, or make it conditional? | Make it conditional and require the executor to say which gate it passed | (a) Drop the acceptance proof, rejected because it is the plan's headline claim and V-03 would then verify only refusals. (b) Leave it unconditional, rejected because an honest executor on a pre-`ygb3nk` tree would record a failure that is not a defect, and a less careful one would "fix" it by editing `_validate_plan_via_engine`, which is precisely the cross-plan edit the fence forbids | The R1-only proof (the `out-of-scope change(s) present` refusal disappearing for the reasoned path) is fully verifiable on today's tree and is exactly what E-03 owns; the end-to-end acceptance is `ygb3nk`'s to unlock. Splitting the evidence along the same line as the ownership keeps both halves checkable | yes |
| D-3 | The malformed-token refusal cannot come from the shared parser. Add a count comparison, fork the parser, or drop the requirement? | Count comparison at the call site, parser reused for parsing | (a) Fork a second `PATH=WHY` parser, rejected because E-03 explicitly forbids it and two parsers for one grammar is how the two ends of the lifecycle drift apart. (b) Drop the malformed case, rejected because a flag that accepts input and silently discards it is the exact failure mode the sibling plan's OQ-01 warns about and which this plan quotes approvingly. (c) Change `_parse_scope_reason_flags` to raise, rejected as out of scope and behavior-changing for finalize and `status_set`, which depend on its current silence | Measured the parser returns `{}` for all four malformed shapes with no exception. A token that produced no map entry is detectable by comparing `len(values)` against `len(parsed)` at the call site, which needs no parser change and keeps one grammar | yes |
| D-4 | Should the lane-naming requirement be a fixture instruction, or should the fixtures assert the lane resolves? | Both: name the lane for the plan id AND assert `_plan_execution_tree` is not None | Instruct the naming only, rejected because the failure is SILENT and a future edit that renames a fixture lane would restore the false green with no signal; the plan's own gate says a green suite is not sufficient evidence here | Review measured the false green directly: the same scenario differing only in lane id gave rc 0 with zero findings versus rc 1 with the refusal. An assertion on resolution catches any future cause of a None lane, not just a misnaming | yes |
| D-5 | The plan flags the `AGENTS.md` execution-contract text as a reviewer judgement (it names only two `aw commit` spellings and this plan adds a third). Fold it in, file a carrier, or leave it flagged? | Leave it flagged and out of scope, as authored | (a) Fold it into this plan, rejected on the plan's own correct reasoning: the relevant text sits inside a MANAGED BLOCK installed from `engine.py`, so editing the file alone is reverted by the next install and the honest change is a template edit whose blast radius is every managed repo. (b) File a backlog carrier now, rejected because the obligation does not exist until the flag ships, and the flag does not ship until `ygb3nk` and this plan both execute; filing now would create an item whose subject may not exist | The plan surfaced this explicitly rather than omitting it, named the mechanism accurately (I verified the managed block is installed from `engine.py`), and proposed the correct shape (its own plan in this Set). Nothing is owed at review time beyond leaving the flag visible, which it is | yes |
