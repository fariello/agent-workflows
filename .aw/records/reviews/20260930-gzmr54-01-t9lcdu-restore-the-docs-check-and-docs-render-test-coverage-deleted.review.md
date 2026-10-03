# Review findings: plan t9lcdu

- Subject-Id: t9lcdu
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-301 (HIGH, fixed), PR-302 (HIGH, fixed), PR-303 (MEDIUM, fixed), PR-304 (MEDIUM, fixed), PR-305 (MEDIUM, fixed), PR-306 (LOW, fixed), PR-307 (MEDIUM, fixed), PR-308 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `ba383298b`. The plan file was committed and the tree
clean (`git status --short` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review, and `--phase review-finalize` reports `conforming` (exit 0, one advisory `IPD-Z602`) after
revision. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator
child-row check does not apply.

THIS IS AN UNUSUALLY WELL EVIDENCED PLAN AND ITS CENTRAL CLAIM IS TRUE. The author did not stop at
"coverage is missing"; they recovered the deleted file, ran it, and found a live defect. I reproduced
that end to end rather than taking it on trust, and it holds exactly:

- Recovering `19313eed^:tests/test_docs.py` into gitignored scratch with `REPO_ROOT` re-anchored
  gives `1 failed, 27 passed in 0.42s`, failing at `DocCheckTests::test_no_findings_across_docs` on
  precisely `DocFinding(doc='skill-selection.md', line=27, check='aw-command', message="'aw router'
  is not a known subcommand")`.
- The defect needs no recovered file to see: `docs_check.check_docs_dir(Path("docs"))` returns that
  one finding today, still at line 27.
- F-05's diagnosis is exact. The module docstring promises to check "every ``aw <subcommand>``
  referenced in a fenced command block", and `check_aw_commands` iterates `text.splitlines()`
  applying `_AW_CMD_RE` with no notion of a fence or a span anywhere. `'router' in
  known_subcommands()` is False over 68 real subcommands, so the fallback list is genuinely not in
  play, and `docs/skill-selection.md:27` really is the plain-prose heading `## The aw router skill`.
- F-06 holds: `git merge-base --is-ancestor 19313eed a2394b00` succeeds, so the heading post-dates
  the deletion and the trim did not knowingly drop a failing test.

Also verified: F-01 (472 lines, 28 `def test_`), F-02 (zero test callers; 181 and 173 lines), F-03
(all three `fzueyy` symbols present in `tests/test_run_scratch_path_guard.py`), F-08 (both deferred
classes green, `8 passed`), F-09 (18 required docs, all present, all linked from the index), the
inert-gate claim (`rg -n doc_findings` matches only `release_readiness.py`), E-02's ignore claim
(`check_docs_dir` really does call `get_ignored_dirs`/`is_ignored_path`), E-07's coupling list (3, 31
and 10 `docs/` references in the three named files), and all four cited carriers resolving to live
items.

TWO THINGS I PROVED THAT THE PLAN ONLY ASSERTED, both using a method worth recording because it
touched zero tracked files:

1. **F-07, both halves.** I implemented the restricted scan OUTSIDE the module (fence toggle plus
   backtick-span extraction, reusing `docs_check._AW_CMD_RE`): 0 findings across every
   `docs/**/*.md`, while `` run `aw florb` please `` still flags and the prose heading goes silent.
   Separately I copied `docs/` into gitignored scratch, applied ONLY the heading fix there, and ran
   the UNCHANGED checker: 1 finding became 0. So the two fixes are genuinely independent.
2. **F-09's subsumption.** Rather than accept the link-check argument, I deleted `docs/recovery.md`
   from a scratch copy: findings went from 1 to 6, three of them `internal-link` findings naming the
   missing target from `README.md` (twice) and `troubleshooting.md`. The property really does stay
   red-on-deletion without the hand-maintained list.

THE TWO HIGH FINDINGS ARE BOTH STALE-MEASUREMENT TRAPS POINTING IN THE DANGEROUS DIRECTION. F-10
told the executor the suite is red at the base and to "EXPECT ONE PRE-EXISTING FAILURE"; the suite is
now fully green (`3867 passed, 2 skipped`) and that node passes in isolation, because it was a
UTC-midnight date-rollover flake. A plan that pre-authorizes a specific failure teaches an executor
to wave it through, so if that node were red again for a NEW reason it would be accepted. And the
Required-tests section named 3604 collected as "the baseline to compare against" while E-07
correctly said to measure at the execution base: the two contradicted each other, and 3604 is now
4077. Both are the same categorical error (a live population frozen into an acceptance bar), and
both are now self-relative.

ONE FINDING WOULD HAVE COST A GUARANTEED ROUND TRIP. `check_doc` takes a `Path` and reads the file
itself; I hit `TypeError: check_doc() takes from 1 to 2 positional arguments but 3 were given` trying
to pass text. E-01 rightly says to re-verify signatures, so I recorded all five in the item, and
re-routed V-04's independence probe through a gitignored docs copy, which is the only way to drive
altered CONTENT through a Path-taking checker without editing the tracked tree.

WHAT I DELIBERATELY DID NOT FLAG. OQ-02 is left OPEN with `Blocking: no`, and that is correct: it
asks whether two classes belong to this item or their own, which is a scope judgement reserved to
the maintainer, and the work is carried by live backlog `spvm3v` either way, so a "no" drops nothing.
Per the 2026-09-10 maintainer ruling a non-blocking open question does not make a plan `NO-GO`. I
also did not flag the absence of a test wiring `check_docs_dir` into `aw check`: the plan names the
gate inert, measures it, and carries it to `tj9dq9`, which is the honest treatment.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | IN-SCOPE | E (testing); D (anti-regression) | `python3 -m pytest` at review -> `3867 passed, 2 skipped, 3 warnings in 72.89s`; the named node alone -> `1 passed in 0.21s`; `aw find backlog fnb8pl` -> `open`; F-10 and V-07 as authored ("EXPECT ONE PRE-EXISTING FAILURE ... confirm it fails at the execution base") | F-10 HAS INVERTED SINCE AUTHORING AND NOW TEACHES AN EXECUTOR TO WAVE THROUGH A RED NODE. The plan states the bare suite is not green at the base and instructs the executor to confirm `test_release_exempt_setter_roundtrip_and_parity` FAILS. Measured, the suite is fully green and that node passes in isolation: the local-versus-UTC clock skew only bites when a run straddles UTC midnight, so it was a date-rollover FLAKE, not a standing failure. Pre-authorizing a named failure is the dangerous direction of baseline rot: if that node goes red again for an unrelated reason, this instruction tells the executor to expect it and move on. The latent defect is real (`fnb8pl` is still open) and correctly out of scope; what is wrong is the executor bar. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-10 rewritten with both measurements, the flake mechanism named, and the authored instruction explicitly marked as not to be followed. E-07 and V-07 now require a GREEN before-baseline and green after-baseline, and add a discriminating test: if that node is red at your base, re-run it ALONE and only treat it as pre-existing if it fails in isolation with the same date diff; anything else is new and must be investigated. |
| PR-302 | HIGH | IN-SCOPE | E (testing); G (plan executability) | Required tests as authored ("The baseline to compare against is 3604 tests collected at authoring HEAD `2e2ecce12`") against E-07 ("rather than trusting the 3604 recorded here"); re-measured `4077 tests collected`, `3867 passed`; `git log --oneline 2e2ecce12..HEAD \| wc -l` -> 664 | THE PLAN CONTRADICTS ITSELF ON THE BASELINE, AND THE LITERAL IT NAMES IS SPENT BY 473 TESTS. E-07 correctly instructs measuring at the execution base and explains why a hard-coded number "would misreport a clean run as a regression"; the Required tests section then names 3604 as "the baseline to compare against". An executor following the latter reports a phantom regression on a change that only adds tests. The error is categorical rather than arithmetic: a collected total is a LIVE population moved by every other lane. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required tests now leads with CAPTURE YOUR OWN BASELINE, records both re-measured figures as dated context rather than bars, and makes every comparison self-relative (before, after, delta equals tests added). E-07 and V-07 reconciled to the same rule. A Step 0 convention bullet records the live-versus-stable-code-fact distinction so the contradiction cannot reappear. |
| PR-303 | MEDIUM | IN-SCOPE | C (operability); A (correctness) | V-01, V-03, V-04 each requiring a temporary tracked-file edit; review's two probe methods (out-of-module restricted scan; gitignored `docs/` copy) each touching zero tracked files; AGENTS.md shared-checkout rule | THREE NEGATIVE CONTROLS EDIT TRACKED FILES IN A SHARED CHECKOUT WITH NO WINDOW DISCIPLINE. The plan correctly requires each temporary edit to be reverted and the revert proven, but says nothing about how long the edit may live or which run happens while it is live. A neutered checker or a reverted scan restriction held across a multi-minute full-suite run is exactly the window in which a co-worker's concurrent edit to `docs_check.py` gets discarded by the restore. Worse, V-04's independence probe does not need a code edit at all: it needs altered CONTENT, which a scratch copy supplies. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | A METHOD RULE added to Required tests and mirrored in the gate: hold every temporary source edit for a NARROWED run only (`-o addopts=""` on the single file, never the full suite), restore immediately, paste `git status --short` empty; and for any probe needing altered doc content, copy `docs/` into gitignored scratch instead of editing the tracked tree. A Step 0 bullet records that review verified F-07 and F-09 that way with zero tracked-file edits, so the method is known to work. |
| PR-304 | MEDIUM | IN-SCOPE | A (correctness); G (plan executability) | `check_doc(doc_path, subcommands=None)` read from the module; reproduced `TypeError: check_doc() takes from 1 to 2 positional arguments but 3 were given`; V-04 as authored asking for a `check_docs_dir` comparison with the checker reverted | `check_doc` TAKES A `Path`, NOT TEXT, AND THE PLAN NEVER RECORDS THE SIGNATURES IT TELLS THE EXECUTOR TO VERIFY. E-01 rightly says to re-verify against current signatures rather than pasting blind, but leaves the executor to discover them, and the discovery has a trap: `check_doc` reads the file itself, so a probe over ALTERED content cannot pass a string. I hit the `TypeError` directly. This is a guaranteed round trip for whoever executes, and it interacts with V-04, whose independence probe needs altered content. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-11 with all five current signatures (`check_no_unicode_dashes`, `check_internal_links` taking text AND a Path, `check_aw_commands` with a REQUIRED known set, `check_doc` taking a Path, `check_docs_dir`) and the reproduced `TypeError`. E-01 now carries the signatures inline. V-04 is re-routed through a gitignored docs copy with the Path constraint stated as the reason. |
| PR-305 | MEDIUM | UNDER-SCOPE | G (plan executability); F (honest documentation) | `git show 19313eed^:tests/test_docs.py \| rg -n '^class '` -> ten classes; per-class presence check showing exactly the run-scratch pair present; the plan's "six classes the item names" phrasing | A RESTORATION PLAN'S MOST IMPORTANT PROPERTY IS THAT NOTHING WAS SILENTLY DROPPED, AND THIS PLAN NEVER STATES THE ACCOUNTING. The deleted file held TEN classes; the plan's prose says "six", inheriting the backlog item's own count (which is correct about the item, measured). The dispositions are in fact complete and sound once assembled, but a reviewer has to reconstruct them from three separate sections to see that, and a reader could reasonably believe four classes vanished unaddressed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-12 enumerating all ten with their disposition (two already restored by `fzueyy`, five restored here, one subsumed with the subsumption MEASURED, two deferred to live carrier `spvm3v`), and a FULL ACCOUNTING bullet added to the scope check stating "ten of ten, no silent drop" and noting that the "six" phrasing obscures it. F-09 strengthened with the deletion probe that proves the subsumption rather than arguing it. |
| PR-306 | LOW | IN-SCOPE | E (testing) | the deleted arm reading `dc.check_aw_commands("run \`aw florb\` please", ["run", "ipd"], "x.md")`; `len(docs_check.known_subcommands())` -> 68 | THE RECOVERED FALSIFIABILITY ARM INJECTS ITS KNOWN SET AND THE PLAN DOES NOT SAY TO PRESERVE THAT. The deleted test passed an explicit `["run", "ipd"]` rather than calling `known_subcommands()`, which is what makes it a unit test: the live set has 68 entries derived from the CLI parser and changes whenever a subcommand lands, so an arm built on it silently changes meaning over time. An executor restoring "against current signatures" could reasonably switch to the live set and weaken the arm. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-13 with the measurement. E-01 now instructs injecting the known set in the per-check arms and reserving `known_subcommands()` for E-02's whole-tree arm, where the live set IS the subject. |
| PR-307 | MEDIUM | UNDER-SCOPE | G (plan executability) | the gate as authored (commit instruction, no scope-path declaration or reconciliation language); no sibling plan declaring any of the four paths | THE GATE CARRIES NO SCOPE FENCE. The workflow requires the gate to declare the scope paths so finalize can reconcile edited against declared files, and this plan's gate names them only inside a commit command. It also has genuinely unsafe conditions worth a stop directive that were unstated, which matters more here than usual because two declared paths are shipped artifacts (`agent_workflows/docs_check.py`, `docs/skill-selection.md`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A SCOPE FENCE paragraph added: declares all four paths, states it is a declaration and not a stop condition, points at `--scope-reason`/`--scope-ack`, forbids stopping over a scope question, and names the concrete unsafe conditions that DO warrant stopping. Records the review measurement that no sibling pending or approved plan declares any of the four paths. |
| PR-308 | LOW | IN-SCOPE | G (plan executability) | the post-gate paragraph as authored ("transition the plan to `executed` through the tooled lifecycle (`aw ipd set`)") | THE TERMINAL-TRANSITION VERB IS WRONG AND THE OWNERSHIP IS UNCONDITIONAL. `aw ipd finalize` owns the terminal transition, and it is what runs the scope reconciliation the new fence depends on; `aw ipd set` is the status setter. The paragraph also addresses the executor as the actor in all cases, which is wrong under a runner, where the runner performs the finalize and a second invocation collides with it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The paragraph now separates the unconditional obligation (every `V-*` evidenced plus `pre-transition` conforming) from conditional ownership (runner under a runner, executor via `aw ipd finalize` by hand), names `finalize` as the owning verb with the scope-reconciliation reason, and keeps the authored prohibitions on hand-editing the status line and hand-moving the file. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-02 is left OPEN (`Blocking: no`, `Owner: human`), asking whether the two deferred classes belong to this item. Does that make the plan NO-GO, or should the reviewer resolve it? | Neither: left OPEN and non-blocking, readiness `go-pending-approval`. | (a) Treat the open question as a NO-GO condition. (b) Resolve it myself from repository evidence. | (a) is refused by the 2026-09-10 maintainer ruling (plan `qhy3i3` OQ-01), which changed the NO-GO condition from "any open question" to an unresolved BLOCKING one, precisely so the `- Blocking:` flag carries consequence. (b) is refused because the question is genuinely not answerable from the repository: it asks whether coverage for `run_analytics_export` and the `--help` legend belongs to THIS item or its own, which is a scope and priority call the repository's instructions reserve to the human. The evidence I can supply I did: both classes pass today, both subjects have zero tests (`DETECTOR_BLIND_SPOTS` and the legend-in-help property each match no test file), and live carrier `spvm3v` owns the work either way, so a "no" drops nothing. | yes |
| D-2 | F-10 asserted a red baseline and the suite is now green. Correct the finding only, or also change how the executor treats a red node? | Both: correct F-10 AND replace "expect this failure" with a discriminating re-run-the-node-alone test. | (a) Correct the finding's measurement and leave V-07's instruction. (b) Delete F-10 entirely as spent. | (a) is insufficient and is the dangerous half: a plan that names a specific node as expected-red trains an executor to accept it, so the instruction, not just the number, is the defect. (b) is refused because the underlying defect is real and still open (`fnb8pl`), and the flake can genuinely recur on a run straddling UTC midnight, so an executor who meets it needs to know what it is. The discriminating test keeps that knowledge while removing the pre-authorization: fail in isolation at the base with the same date diff means known flake, anything else means investigate. | yes |
| D-3 | Three V-items require temporary edits to tracked files. Tighten the method, or accept the authored revert-and-prove discipline? | Tighten: narrowed runs only while an edit is live, and a gitignored docs copy wherever only CONTENT must change. | (a) Accept the authored discipline (revert in the same pass, prove with `git diff --stat`). (b) Forbid tracked-file mutation outright and require a different proof. | (a) is insufficient because it constrains WHETHER the edit is reverted but not how long it lives, and the plan elsewhere asks for full-suite runs; a neutered checker held across a multi-minute suite run is exactly the window the shared-checkout rule exists to close. (b) is refused as impossible for V-01 and V-03, whose whole point is that the CHECKER must be broken to prove the test can fail; there is no in-memory substitute when the test imports the module under test by name. The narrowed-window rule is the achievable discipline, and the scratch-copy route removes the one case (V-04) that never needed a code edit at all, which I demonstrated by using it myself. | yes |
