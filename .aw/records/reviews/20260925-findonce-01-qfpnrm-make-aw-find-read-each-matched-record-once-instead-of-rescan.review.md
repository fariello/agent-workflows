# Review: Make aw find read each matched record once instead of rescanning the whole plans and research trees

- Subject-Id: qfpnrm
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was correctly skipped per
Step 1. Structural preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0)
before review and again at `--phase review-finalize` after the revisions.

EVERY MEASUREMENT IN THIS PLAN REPRODUCES, which is unusual enough to state first. Using an audit hook
counting `open` events on `.aw/records/**.md`, `find plans <id6>` opened 1555 files for 777 unique
plans with all 777 opened twice; `find plans` with no selector opened 777 with zero doubles;
`find research <id6>` was 249/124/124 and `find research` 124/124/0; `find specs <id6>` and
`find backlog <id6>` each showed exactly one double, the intended single display read of the matched
file. The authored table said 1508/754/754, 754/754/0, 248/124/124, 37/37/0 and 606/604/1, so every
row holds within corpus growth. The warm in-process split, wrapping both `plans_index.scan_plans` and
`selectors.resolve`, measured total 323.4ms with `scan_plans` 128.0ms and `resolve` 91.6ms against the
authored 316.3/129.6/89.3. The cold subprocess best-of-7 was 0.58s (median 0.61s) against a
`--version` floor of 0.26s, where the plan claimed 0.61s and 0.35s. So the defect is real, the ~130ms
is real, and it is a real share of a command a human waits on - which is what earns `Work-Kind: bug`
under this repository's perceptibility test.

THE THREE MATERIAL FINDINGS ARE ALL THE SAME SHAPE: the whole-tree scan supplies a behavior as a side
effect, and a per-path builder loses it silently. That is the interesting class here, because the
plan's premise is byte-identical output and none of the three would show up in a naive test.

PR-701 IS THE ONE THAT COULD MAKE THE COMMAND SLOWER. Both `scan_plans` and `_scan_docs` call
`artifact_core.get_ignored_dirs(<root>)` exactly once before their loop, and that function runs
`subprocess.run(["git","ls-files","--others","--ignored","--exclude-standard","--directory","-z"])`.
Measured on this tree: 2.7ms best, 3.4ms median. E-03 as authored gave `plan_entry` the signature
`(plans_dir, p)` with no way to receive the ignored set, which invites resolving it inside - one
subprocess per matched path. A setid selector matching thirty plans would then pay roughly 80ms of new
subprocess cost to save a 128ms scan, and on a large Set it could exceed it. The fix is small (hoist
it to the caller, inject it keyword-only with no default so it cannot be skipped) but it has to be
stated, and V-05 now requires the call count be compared on a MULTI-match selector, because a
single-match timing cannot see this regression at all.

PR-702 IS THE ONE THAT COULD CHANGE OUTPUT, and it is genuinely counter-intuitive.
`research_index._scan_docs` `continue`s past any doc whose filename fails `parse_name` or whose
frontmatter fails to parse, so it yields 122 entries for 124 non-index `.md` files. The two without
entries are `conformance-results-template.md` and
`20260712-0156-14-chatgpt-modular-report-template.md`. The RESOLVER does not skip them:
`selectors._iter_files` yields all 124, and `selectors.resolve(root, "research", "template", ...)`
returns both with kind `substring`. I ran the command: `aw find research template` prints
`no matching research`. So the resolver and the display layer disagree about which files exist, the
display layer wins, and the current answer for a real matchable token is zero rows. A per-path
`_doc_entry` that returns an entry for such a doc would ADD rows `find` has never printed - an output
change on a plan whose whole promise is byte-identical output, invisible to any test built only from
well-formed fixtures. E-02 gains case (e) pinning that output and the fixture gains an unparseable doc.

PR-703 IS A FAILURE PATH THAT MOVES. `scan_plans` calls `p.read_text(encoding="utf-8")` with no
try/except, while `selectors._iter_paths`'s own docstring records that "a filename match no longer
depends on whether the body happens to be readable" and the `path`/`stem`/`substring` rules use it
precisely for that reason. Today an unreadable plan makes the whole-tree scan raise for every
`find plans` command; after the change it raises only when that file is matched, and a filename rule
can match it exactly because filename matching does not need a readable body. Whichever behavior is
correct, it is a change in an uncovered failure path, so E-02 gains case (f) to pin HEAD's behavior and
E-03 is explicitly forbidden from adding a try/except as part of a "pure refactor".

PR-704 IS A CORRECT CAUTION WITH AN OVERSTATED CONSEQUENCE, and both halves needed saying. E-04 warns
that `_resolve_selectors_with_kinds` returns `sorted(seen)` over STRINGS while `scan_plans` iterates
`sorted(plans_dir.rglob("*.md"))` over PATHS. The distinction is real: on Python 3.14,
`Path("a/b.md") < Path("a-b/c.md")` is True while the string comparison is False, because `/` sorts
below `-`, `.` and `_`. But the consequence is narrower than the item implies, for two independently
measured reasons. First, `plans_index.query` ends with
`sorted(out, key=lambda e: (e.set_id or "", e.order or 0, e.path))` and `research_index.query` with
`sorted(out, key=lambda e: (e.set_id, e.order, e.id6))`, so ANY query carrying an explicit
`--id`/`--set`/`--status`/`--disposition` discards the build order entirely. Second, over the real 777
plan paths the two sorts are IDENTICAL, because the tree is flat: `find .aw/records/plans -mindepth 2
-type d` returns nothing, no `<disposition>/YYYYMM/` shard exists yet. So the order is observable only
for a no-flag selector query over a sharded tree. Using the `Path` sort is still right - it is what
`scan_plans` does, it costs nothing, and `aw archive plans` is designed to create shards - but E-02(c)
would pass vacuously on a flat fixture, which is why V-02 now demands proof the fixture's shard exists,
and the fix must not be reported as closing an observable bug.

PR-705 and PR-706 are the same class as each other: E-01's baseline treats a live population as fixed.
The plans corpus grew from 754 at authoring to 777 at review, so "plans open count equals twice the
plan count" and V-05's literal BEFORE values (1509 opens, 316.3ms, 0.61s) will not reproduce, and a
literal comparison fails on a correct run. Worse, the corpus selectors are live tokens with no check
that any of them matches: a token matching nothing produces an empty baseline file AND an empty
after-file, so E-05's byte-diff passes for that entry while testing nothing - coverage that looks
present and is not. E-01 now requires each selector be verified to match, records substitutions, and
mandates that the corpus retain a single-match id6, a multi-match setid, a filtered query (so
`query`'s re-sort path is covered), both no-selector arms, and a generic-type control. V-01 and V-05
state the pass condition as the SHAPE and the DELTA against E-01's own freshly recorded baseline.

PR-707 matters more than its severity suggests. Both test files the plan names as removed are indeed
absent, and nothing else in `tests/` matches `find` or `selector`. So `tests/test_plans_index.py`
guards `scan_plans` alone, and there is NO pre-existing test over `cli._find_type_records` or
`research_index._scan_docs`. E-02 is not a supplement to existing coverage; it is the entire safety
net for a change to the display path of a command users run constantly. That is the reason the review
added cases (e) and (f) rather than trusting the byte-diff, and the reason E-06 now pins the
no-selector arm, which E-04 restructures around but does not intend to change and which nothing else
would catch.

ON RIGHT-SIZING. Six items became eight. The two additions are each one deliverable: E-06 re-runs the
open counter on the untouched arm, E-07 runs `ruff` (separate from the suite because it is a
fail-closed pre-commit hook here, so a finding costs a commit round trip rather than a test). E-03 and
E-04 remain the two substantive items and were examined against the splitting diagnostics: E-03 is one
mechanical extraction in two parallel modules with one test surface, and splitting it from E-04 is
already the right seam because V-03 checks the refactor changes nothing before the behavior moves.

OQ-01 was already `resolved` and its reasoning holds: I re-measured `find backlog <id6>` at 609 opens
over 607 unique with one double, which is the generic branch's intended single display read, and one
extra open is not perceptible. No action, correctly.

`aw check release-gates` reports `findings: 0`, exit 0, so the inherited gate starts clean. Source item
`59t9x5` is `graduated`, `Work-Kind: bug`, `Blocks-Release: next`, and the plan correctly inherits
both, so no handoff is owed. `evaluate_durable_carrier` reports zero drifts on this plan (its one
Deferred row carries `Carrier-Declined:` and the other `Carrier: kx9md1`, which resolves to an `open`
backlog item). `aw sanitize --agent` is clean. No spec governs `find`'s read strategy, so the plan's
N/A is correct and `Scope-Paths` rightly declares none.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | UNDER-SCOPE | A. Correctness / C. Architecture (a fix that can become a regression) | `plans_index.scan_plans` and `research_index._scan_docs` each call `_core.get_ignored_dirs(<root>)` once BEFORE their loop; that function runs `subprocess.run(["git","ls-files","--others","--ignored","--exclude-standard","--directory","-z"], ...)`; measured at review best 2.7ms / median 3.4ms; E-03's authored signature was `plan_entry(plans_dir, p)` with no channel for the set | THE PER-PATH BUILDER CAN MAKE A MULTI-MATCH QUERY SLOWER THAN THE SCAN IT REPLACES. The ignored-directory set is a once-per-scan SUBPROCESS, and the authored signature gives `plan_entry` no way to receive it, so the natural implementation resolves it internally and spawns one `git ls-files` per matched path. Thirty matched plans would add roughly 80ms of subprocess time to save a 128ms scan; a large Set could exceed it outright. The plan's own premise is a performance win, so silently trading a bounded scan for an unbounded subprocess fan-out defeats it, and a wall-clock check on a single-match selector (which is what E-05 as authored measured) cannot see it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (hoist one call and add a keyword-only parameter) | FIXED | Added F-6 with the measurement. E-03's signature is now `plan_entry(plans_dir, p, *, ignored_dirs)` (and `_doc_entry(research_root, p, *, ignored_dirs)`), keyword-only with NO default so a caller cannot skip it and get a wrong skip decision, with the subprocess arithmetic stated as the reason. E-04 computes it once per invocation. V-03 requires the signatures be pasted and that `scan_plans` still make exactly one `get_ignored_dirs` call; V-05 requires the call count be compared BEFORE and AFTER on a MULTI-match selector. Scope field extended to name it. |
| PR-702 | HIGH | UNDER-SCOPE | A. Correctness / D. Anti-regression (an output change the tests would miss) | `research_index._scan_docs` `continue`s when `R.parse_name` fails or `R.parse_frontmatter` returns None; measured: 122 entries for 124 non-index `.md` files, the two entry-less being `conformance-results-template.md` and `20260712-0156-14-chatgpt-modular-report-template.md`; `selectors._iter_files` yields all 124; `selectors.resolve(root,"research","template",deny={MATCH_PATH})` returns BOTH with kind `substring`; `python3 -m agent_workflows find research template` prints `no matching research` | THE RESOLVER MATCHES TWO REAL RESEARCH FILES THAT THE DISPLAY LAYER CANNOT RENDER, AND THE CURRENT OUTPUT IS ZERO ROWS. A per-path `_doc_entry` that yields an entry for a doc whose name or frontmatter does not parse would ADD rows `aw find` has never printed. That is an output change on a plan whose entire promise is byte-identical output, and it is invisible to any test built from well-formed fixtures - which is exactly what E-02's authored fixture (3 research docs, all presumably valid) would have been. The counter-intuitive current behavior ("matches, prints nothing") is the thing that must be preserved. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-7 with the full measurement and the live command output. E-02's fixture now carries a FOURTH research doc that is deliberately unparseable, plus new case (e) asserting a selector resolving to it still produces NO row. E-03 is required to make `_doc_entry` return None for exactly the cases `_scan_docs` skips, preserving every skip and drift branch. E-01 additionally captures `find research template` (or the executing tree's equivalent) in the baseline corpus, since it is the output most likely to change by accident. V-02 requires the asserted no-row output be pasted. A conventions bullet records the resolver/display disagreement and that the display layer wins. |
| PR-703 | MEDIUM | UNDER-SCOPE | A. Correctness / F. Prevent silent failure | `plans_index.scan_plans`: `text = p.read_text(encoding="utf-8")` with no try/except; `selectors._iter_paths` docstring: "a filename match no longer depends on whether the body happens to be readable"; `selectors._iter_files` skips a file whose header cannot be read, and `path`/`stem`/`substring` deliberately use `_iter_paths` | MOVING THE READ ONTO MATCHED PATHS CHANGES WHEN AN UNREADABLE FILE RAISES, in an uncovered failure path. Today an unreadable plan makes the whole-tree scan raise for EVERY `find plans` invocation; afterwards it raises only when that file is MATCHED - and a filename rule can match it precisely because filename matching does not require a readable body. So the change converts a total, obvious failure into a selector-dependent one. Neither behavior is self-evidently wrong, but choosing one silently inside a "pure refactor" is, and nothing in the suite would notice. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-8. E-02 gains case (f), making one matched plan unreadable and pinning HEAD's behavior before and after. E-03 is explicitly forbidden from adding a try/except ("a behavior change disguised as a refactor"). The Scope field names the read posture as one of the three side effects being preserved, and a conventions bullet records that the two readers are reconciled today only because the whole-tree scan runs first. |
| PR-704 | MEDIUM | IN-SCOPE | A. Correctness / E. Testing (a correct caution whose test passes vacuously) | Measured on Python 3.14: `Path("a/b.md") < Path("a-b/c.md")` True, `"a/b.md" < "a-b/c.md"` False; over the real 777 plan paths `sorted(Path)` and `sorted(str)` are IDENTICAL; `find .aw/records/plans -mindepth 2 -type d` returns nothing; `plans_index.query` ends `sorted(out, key=lambda e: (e.set_id or "", e.order or 0, e.path))`; `research_index.query` ends `sorted(out, key=lambda e: (e.set_id, e.order, e.id6))` | E-04'S SORT CAUTION IS RIGHT AND ITS BLAST RADIUS WAS OVERSTATED, and the overstatement makes its test vacuous. The `Path`/`str` orders genuinely differ, but the build order is observable only for a selector query with NO filter flag over a tree containing a `<disposition>/YYYYMM/` shard: any explicit filter re-sorts inside `query`, and no shard exists in the live tree, where the two orders coincide over all 777 paths. So E-02(c) as authored would pass on a flat fixture without ever testing the ordering it exists to test, and a reader would credit the plan with fixing an observable bug that is currently unobservable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-9 with both measurements. E-04 now states both halves explicitly - keep the `Path` sort (it matches `scan_plans`, costs nothing, and `aw archive plans` creates shards) but do not report it as closing an observable bug - and requires the fixture contain a shard. V-02 requires proof the fixture's shard exists, since on a flat fixture the test passes without exercising the order. A conventions bullet records that both `query` functions re-sort. |
| PR-705 | MEDIUM | IN-SCOPE | G. Plan executability (live-artifact figures asserted as fixed) | Plans corpus 754 at authoring, 777 at review; E-01 expected outcome "plans open count equals twice the plan count"; V-05 required comparison against literal BEFORE values 1509 opens, 316.3ms total / 129.6ms scan, 0.61s cold | E-01'S AND V-05'S ABSOLUTE FIGURES CANNOT REPRODUCE, so a correct run fails a literal check. The record population, the warm milliseconds and the cold seconds are all live measurements of a moving tree, and the plan states them as the bar rather than as context. The repository's own convention requires a criterion counting live artifacts to demand re-derivation and keep the authored number as prose. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now records the numbers OBSERVED and states the pass condition as the SHAPE (selector commands about 2x, no-selector about 1x). V-01 says plainly not to compare against the authored figures and why. V-05 requires each AFTER value be stated beside its own E-01 BEFORE value rather than against the plan's prose, and additionally requires proof no record was added or removed between the two runs, since a moved corpus makes the byte-diff meaningless in either direction. The Findings section now carries the review's own re-measurement table as corroboration with its date. Added F-11. |
| PR-706 | MEDIUM | IN-SCOPE | E. Testing (coverage that looks present and is not) | E-01's corpus names live tokens (`wqq8ua`, `wtiso`, `stopladder`, `executed`, `ctrl`, `c4gd2h`, `59t9x5`) with no check that any matches; an empty stdout file diffs equal to an empty stdout file under `diff -r` | A CORPUS SELECTOR THAT MATCHES NOTHING SILENTLY CONTRIBUTES NOTHING TO THE BYTE-DIFF while appearing as coverage. E-05's whole proof of output equivalence is `diff -r` over these files, so a token that has gone stale (a plan renamed, a Set archived) yields empty-before and empty-after and passes, testing nothing. The plan's central safety claim rests on this corpus, and nothing in it establishes that the corpus exercises anything. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now requires each selector be confirmed to return at least one row before use, with substitutions recorded, and mandates the corpus retain a single-match id6, a MULTI-match setid, at least one query with an explicit filter flag (covering `query`'s re-sort path), both no-selector arms, and a generic-type control that must not change. V-01 requires a row count per selector plus the substitution note. Recorded as part of F-11. |
| PR-707 | LOW | UNDER-SCOPE | E. Testing (the true extent of the safety net) | `ls tests/test_cli_find.py tests/test_selector_zero_open.py` -> both absent; a case-insensitive listing of `tests/` for either `find` or `selector` in the filename returns nothing; `tests/test_plans_index.py` present | E-02 IS THE ENTIRE SAFETY NET, NOT A SUPPLEMENT TO ONE, and the plan does not say so. `tests/test_plans_index.py` covers `scan_plans` only; nothing covers `cli._find_type_records` or `research_index._scan_docs`. So any behavior E-02 fails to pin is caught by nothing at all - which is what makes PR-702's and PR-703's silent-change risks consequential rather than theoretical, and which also leaves the no-selector arm (restructured by E-04, not intended to change) completely unguarded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-10 and a conventions bullet stating the true coverage position. Added E-06/V-06 re-measuring the no-selector arm's open counts after the change and requiring they equal E-01's baseline with zero doubles. The gate's approval paragraph states the no-pre-existing-test fact so a human approving knows what is and is not protected. |
| PR-708 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: two metadata lines plus one three-clause sentence. Compare `0i4fkt`/`8apjpp`/`184tn9`, which carry an approval paragraph, a declaration-style scope fence, an explicit not-in-scope list, an honesty rule naming fakeable claims, stop conditions, and conditional finalize ownership | THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS on a plan that touches the display path of a constantly-used command, carries a release gate, and has no pre-existing test coverage. There was no statement of what a human is approving (so neither the `bug` classification nor the three silent-change risks appeared at the approval point), no scope fence to reconcile against despite the Scope field already carrying an OUT list, no honesty rule on a plan with four separately fakeable validations, and no stop conditions. It also instructed a bare move to `executed/`, which is wrong under a runner that owns the transition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: an approval paragraph giving the re-measured numbers, the perceptibility basis for `bug`, and all three output-equivalence risks with their findings; a per-file scope fence stated as a DECLARATION plus an explicit not-in-scope list (`selectors.resolve`, `_PRECEDENCE`, the matching rules, the Status-regex disagreement, the generic branch, both `query` functions and their sort keys, the display loop and `paw8so` block, the interpreter floor); the hard-MUST honesty rule naming the four fakeable claims (empty corpus entry, flat fixture, moved corpus, single-match subprocess count) with the bare-suite flag prohibitions; two genuine stop conditions; and the lifecycle transition with conditional runner/executor ownership plus the note that `59t9x5` is already `graduated` so the inherited gate is discharged by execution rather than by editing the item. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `get_ignored_dirs` is a subprocess called once per scan. Should `plan_entry` receive the ignored set, cache it, or resolve it per call? | Receive it as a REQUIRED keyword-only parameter with no default; the caller computes it once. | (a) Resolve it inside `plan_entry` - rejected: one `git ls-files` subprocess per matched path, measured 2.7ms each, which can exceed the 128ms scan being removed on a large Set and defeats the plan's purpose. (b) Memoize it at module level keyed on the root - rejected: it adds process-global mutable cache state with no invalidation story, and a stale ignored set silently changes which records are skipped; the repository has explicitly declined module-level mutable state in an adjacent runner module for the same class of reason. (c) Give the parameter a default of `None` meaning "resolve it yourself" - rejected: it makes the slow path the silent one, which is the opposite of failing closed. | `artifact_core.get_ignored_dirs` runs `git ls-files ...` via `subprocess.run`; measured 2.7ms best / 3.4ms median; both scans hoist it above their loop today | yes |
| D-2 | `_scan_docs` skips a research doc whose name or frontmatter does not parse, so two resolver-matchable files print nothing. Preserve that, or make them displayable? | Preserve it exactly: `_doc_entry` returns None for precisely those cases, and E-02(e) pins the zero-row output. | (a) Render them with placeholder fields - rejected: it ADDS rows `aw find` has never printed, breaking the plan's byte-identical-output promise, and it would be a semantic decision about what an unparseable research doc's id6 and status are, which no artifact contract answers. (b) Emit a drift warning for them - rejected: the display path is not a checker, `aw check research` already owns drift reporting, and adding output here is the same promise violation. (c) Say nothing and let the extraction decide - rejected: measured, the natural per-path implementation returns an entry, so silence chooses the wrong answer. | `research_index._scan_docs`'s `continue` branches; measured 122 entries for 124 files; `selectors.resolve(...,"template",...)` returns both entry-less files; `aw find research template` prints `no matching research` | yes |
| D-3 | Moving `read_text` onto matched paths changes when an unreadable file raises. Fix the failure path, or pin current behavior? | Pin current behavior in E-02(f) and forbid E-03 from adding a try/except. | (a) Add a try/except that skips an unreadable matched file - rejected: it is a behavior change smuggled into an item the plan itself calls a pure refactor, and it would diverge the plans path from `scan_plans`, which the no-selector arm still uses, so one command would tolerate what the other raises on. (b) Add it to BOTH, making `scan_plans` tolerant too - rejected: that is a real improvement and a real behavior change, deserving its own plan and its own justification, not a line inside a performance fix. (c) Ignore it - rejected: the failure path genuinely moves, and nothing in the suite covers it. | `scan_plans`'s unguarded `p.read_text(encoding="utf-8")`; `selectors._iter_paths` docstring on filename matching not requiring a readable body; no test in `tests/` covers `_find_type_records` | yes |
| D-4 | The `Path`-versus-`str` sort difference is currently unobservable (flat tree, and `query` re-sorts under any filter). Drop the concern or keep it? | Keep the `Path` sort, and state plainly that it is latent rather than an observed bug; require the fixture to contain a shard. | (a) Drop it and use the resolver's string order - rejected: it silently diverges from `scan_plans`, which the no-selector arm still uses, so the same records would print in two different orders depending on whether a selector was given, and `aw archive plans` is designed to create the shards that expose it. (b) Keep it and claim it fixes an observable ordering bug - rejected: measured, the two orders are identical over all 777 real paths and no shard exists, so the claim would be false. (c) Leave E-02(c) on a flat fixture - rejected: it passes without testing the ordering, which is worse than having no test because it reads as coverage. | `Path("a/b.md") < Path("a-b/c.md")` True while the string compare is False (Python 3.14); the two sorts identical over the real 777 paths; `find .aw/records/plans -mindepth 2 -type d` empty; both `query` functions end in a `sorted(...)` | yes |
| D-5 | E-01's corpus uses live selector tokens and E-05's byte-diff is its only equivalence proof. Ask the maintainer for a frozen corpus, or make the item self-validating? | Make the item self-validating: verify each selector matches, record substitutions, and mandate the shapes the corpus must cover. | (a) Ask the maintainer to nominate stable tokens - rejected: no token is stable against archiving and renaming, so the answer would go stale too, and the property needed (each selector matches something) is checkable mechanically. (b) Build a synthetic fixture corpus instead of the live tree - rejected: the live byte-diff over a 777-plan tree is the plan's strongest evidence precisely because it is not synthetic; E-02 already covers the synthetic side. (c) Leave the corpus as authored - rejected: a stale token contributes an empty-versus-empty diff that passes while testing nothing. | The plans corpus grew 754 -> 777 between authoring and review; `diff -r` cannot distinguish "no output, correctly" from "no output, because the selector is dead"; `plans_index.query`'s re-sort makes a filtered query a distinct code path needing its own corpus entry | yes |
