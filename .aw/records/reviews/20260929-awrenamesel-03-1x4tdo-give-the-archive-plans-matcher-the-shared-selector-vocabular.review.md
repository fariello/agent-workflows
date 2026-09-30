# Review findings: plan 1x4tdo

- Subject-Id: 1x4tdo
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `2fdce009` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent` conforms after.
`IPD-S407` does not apply: the plan's own first `- Kind:` bullet reads `child`. No pre-review snapshot was
owed: `git status --porcelain` was empty at review start.

NO PRODUCTION FILE WAS MODIFIED BY THIS REVIEW. Every measurement was an in-process `cli.main` call under
`redirect_stdout`, a direct library call, or a read; `--apply` was never passed to `archive`, so no plan was
moved. Two probes wrote only into `tempfile.TemporaryDirectory()` scratch repos. The only writes were to
this plan and this record.

THE PLAN'S DIAGNOSIS IS CORRECT AND ITS TWO DEFECTS ARE REAL, SILENT, AND WORSE THAN THE BACKLOG ITEM'S OWN
SUBJECT, exactly as it argues. Both reproduce verbatim. I re-derived all eleven findings; ALL CONFIRMED:

- **F-01, the silent no-op.** `aw archive plans 20260808-0004-06-migrate-existing-plans.ipd.md` printed
  `✓ CLEAN  no terminal-root plan or Set matches '<filename>'` at EXIT 0, while
  `aw archive plans 7qx7ys` printed `--- would archive 20260808-0004-06-migrate-existing-plans.ipd.md ->
  202608/ ---` at exit 0. Same plan, opposite outcome, and the failing form looks like success.
- **F-02.** `aw archive plans nonexistent-token-xyz` -> the same `✓ CLEAN` banner, EXIT 0.
- **F-03, the raw-line comparison.** `aw archive plans researchorg` matched nothing;
  `aw archive plans 'researchorg (research-org)'` previewed an archive. `_find_targets` really does
  `sm = re.search(r"(?m)^- Set:\s*(.+?)\s*$", text)` then `sm.group(1) == selector`.
- **F-04's load-bearing numbers.** 136 plans carry a parenthetical and 77 distinct terse setids are
  unaddressable, both EXACTLY as stated (the denominators drifted; see F-15).
- **F-05.** `plans_index.set_terse_id` is the named authority and `selectors._first_set_token`'s docstring
  reads "The terse set-id: the first whitespace token before any '(' (mirrors plans_index)" verbatim.
- **F-06.** `research_archive._resolve_research_for_mutation` calls `resolve_for_mutation` with
  `deny=frozenset({selectors.MATCH_PATH})` and then confines to the research root, as quoted.
- **F-07.** Selector kinds resolve as claimed (filename/stem -> `substring` n=1, path -> `path` n=1,
  id6 -> `id6` n=1, setid -> `setid`).
- **F-08.** `_find_targets` computes `rel = p.relative_to(plans_dir)` and skips anything failing
  `_at_disposition_root`, which is `len(rel_parts) == 2 and rel_parts[0] in TERMINAL_DIRS`.
- **F-10.** `run_archive` handles `if target:` first with its own `return 0`, then falls through to the bare
  sweep, so the branches are precisely separable as the plan claims.
- **F-11.** Baseline green: `3291 passed, 2 skipped, 3 warnings` (authoring measured `3246`).

THE PLAN'S SCOPING JUDGEMENT IS ALSO RIGHT AND I CHANGED NONE OF IT. Keeping the bare sweep at exit 0
(OQ-01), distinguishing a non-terminal match from no match (OQ-02), and NOT denying `MATCH_PATH` the way
`research_archive` does (OQ-03) are each correctly reasoned; OQ-03 in particular is right that Order 01's
in-resolver guard makes per-caller path denial the wrong layer. What I added is the refusal path the plan did
not know the resolver had, and the shape of the tests it will meet.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | MEDIUM | UNDER-SCOPE | A (correctness); F (prevent silent failure); G (executability) | measured `resolve_for_mutation(repo,'plans','migrate')` -> 0 paths, `err="selector 'migrate' is ambiguous (substring) matching multiple files; pass --force to act on all"`; `aw archive --help` lists `--force`; `grep force agent_workflows/plans_archive.py` -> no match | **THE PLAN TREATED `resolve_for_mutation` AS A SOURCE OF MATCHES AND NEVER ACCOUNTED FOR ITS REFUSAL PATH.** It returns zero paths PLUS an error for an ambiguous substring or a unique-kind collision. E-04 as authored distinguished only two cases (matched nothing / matched a non-terminal plan), so an ambiguous selector would be reported as "matched nothing" when the truth is it matched too MANY, which is a fresh misreport in a plan whose whole purpose is to stop the command lying about what it did. Compounding it, the resolver's refusal instructs the operator to `pass --force`, `aw archive` genuinely advertises `--force`, and `plans_archive` reads `force` nowhere, so that advice would be a dead end. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires printing the resolver's `err` verbatim and threading `force=getattr(args,"force",False)`; E-04 distinguishes THREE reasons; OQ-04 records the decision with both rejected alternatives; V-04 and the Required-tests list demand the ambiguous case both with and without the flag. Recorded as F-12. |
| PR-302 | MEDIUM | UNDER-SCOPE | E (testing); G (executability) | `tests/test_plans_archive.py` `test_targeted_archive_by_id` (`argparse.Namespace(target="aaaaaa", dir=..., apply=True)`) and `test_sweep_custom_age_duration`; `self.pdir = self.root / ".agents" / "plans"`; 9/9 green at review; legacy/modern root probe | **THE PRE-EXISTING ARCHIVE TESTS WILL BREAK ON THE OBVIOUS IMPLEMENTATION, AND THE PLAN'S FIXTURE GUIDANCE DOES NOT MATCH THEM.** They call `run_archive` directly with a hand-built Namespace carrying NO `force` and no `age`, so reading `args.force` (rather than a defaulted `getattr`) raises `AttributeError` in all nine. Their fixtures also live under a LEGACY `.agents/plans/` root while E-01 instructs seeding `.aw/records/plans/`. The plan asked the executor to "search for and run every existing archive test" but named none, leaving a discoverable trap for mid-execution. A further sharp edge measured: when BOTH record roots exist the resolver enumerates only one, so a fixture must not create both. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now names both test files, the Namespace shape, the legacy root and the both-roots hazard; E-03's evidence (V-03) must show `getattr(args,"force",False)` and not `args.force`; the gate carries it as an explicit prohibition; the fence proof adds `tests/test_plans_archive.py`. Recorded as F-13. |
| PR-303 | LOW | UNDER-SCOPE | A (correctness); D (anti-regression) | measured: 887 terminal-root candidates under the plans dir `_find_targets` walks; all 887 present in `selectors._iter_paths` (1038 tree-wide); zero invisible | E-03 replaces a private enumeration with the shared resolver's, and the plan never established that the second COVERS the first. If any archive candidate were invisible to the resolver, a currently-archivable plan would silently become unreachable, which is the same class of silent failure the plan exists to fix. The sibling plan `87m438` proved exactly this property for its own routing change; this plan omitted it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now states the containment property with the measurement and requires re-derivation; V-03 requires the count of invisible candidates, which must be zero. Recorded as F-14. |
| PR-304 | LOW | IN-SCOPE | G (live-artifact criteria) | re-measured: plans declaring a `- Set:` = 1027 (not 908), addressable distinct setids = 522 (not 423), suite `3291` (not `3246`) | Three authored counts have drifted. The plan correctly marks F-11's suite count as "not a bar" but states F-04's denominators as bare facts. The two numbers its argument actually rests on (136 plans, 77 setids) are UNCHANGED, so no reasoning is affected, but a criterion counting live artifacts must require re-derivation rather than pinning a measured number. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-15 records each drift with the re-measured value and reaffirms that the load-bearing 136/77 hold; F-11 gains the re-measured suite line; the Required-tests entry names it. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should `aw archive plans` honor `--force` for an ambiguous selector, or refuse unconditionally? | Honor it, threading `getattr(args,"force",False)` into the existing resolver call | (a) IGNORE the flag, REJECTED because the shared refusal already instructs the operator to pass it, so an inert flag would make the command give advice that does nothing, the same class of defect as this plan's own F-01. (b) REFUSE unconditionally with no escape, REJECTED because it would make `archive plans` stricter than the `rename`/`group` family routed through the same resolver by Order 02, reintroducing inconsistency in the opposite direction, and it would discard the resolver's deliberate kind-aware policy under which a setid multi-match needs no flag at all, which is exactly what a set-wide archive wants | Measured `resolve_for_mutation(repo,'plans','migrate')` -> 0 paths with the `pass --force` refusal; `aw archive --help` advertises `--force`; `plans_archive` reads `force` nowhere. The remedy is one defaulted `getattr` | yes |
| D-2 | E-03 swaps a private enumeration for the resolver's. Must the plan prove coverage, or may it be assumed? | Prove it, and require re-derivation at execution | (a) Assume it, REJECTED: an uncovered candidate would make a currently-archivable plan silently unreachable, which is precisely the silent-failure class this plan exists to remove, and the sibling `87m438` set the precedent of measuring the equivalent property rather than assuming it. (b) Pin the measured counts as the bar, REJECTED because the corpus grows; the PROPERTY (containment) is the bar | Measured: 887 terminal-root candidates, all 887 visible to `selectors._iter_paths`, zero invisible. Recorded as F-14 with an explicit instruction to re-derive | yes |
| D-3 | Are OQ-01 (sweep keeps exit 0), OQ-02 (two refusal messages) and OQ-03 (do not deny `MATCH_PATH`) correctly resolved as authored? | Yes, all three left exactly as written | (a) Reopen OQ-03 to mirror `research_archive`'s `deny=MATCH_PATH`, REJECTED: the plan's reasoning is right that Order 01's in-resolver guard makes path safety a resolver concern rather than a per-caller one, and denying the kind would reject the legitimate in-tree path an operator plainly wants, which E-01 asserts must work. (b) Reopen OQ-01 to make the sweep refuse too, REJECTED: an empty sweep genuinely is a successful no-op and a scheduled caller depends on it. OQ-02's two messages are correct and my PR-301 EXTENDS them to three rather than replacing them | Verified `run_archive`'s `if target:` branch is separable (F-10 holds), that a resolved PENDING plan is a real possibility after routing (the terminal-root filter is post-resolution), and that `aw archive plans <a repo-relative path>` is the case F-01's sibling reports an operator wanting | yes |
| D-4 | The plan's prose asserts it carries no `- Readiness:` field, yet review must write one. Rewrite the prose or leave the contradiction? | Write the field, and amend the sentence to say review wrote it and that it is not human approval | (a) Leave the sentence as-is, REJECTED: `aw ipd lint` refused with `IPD-M107` (unattested `- Readiness:`) until the review's own workflow-history line was present, and the stale sentence would then read as denying a field the file visibly carries. (b) Omit the field, REJECTED: it is a REQUIRED output of review and a consumer finding none fails closed, so a cleared plan would simply not be picked up | `IPD-M107` observed firing and clearing; the workflow's own rule that the field is the machine signal while the history line is for humans | yes |

No `Reversible: no` decision was taken, so no escalation is owed. No finding was left `OPEN` or `DEFERRED`,
so no `- Blocking: yes` escalation is owed either.
