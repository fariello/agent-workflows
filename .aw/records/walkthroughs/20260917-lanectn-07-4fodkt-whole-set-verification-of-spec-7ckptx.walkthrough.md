# Walkthrough: `lanectn` whole-Set verification (spec `7ckptx` worker lane containment)

- Date: 2026-09-17
- Kind: whole-Set verification record
- Target-Id: 4fodkt
- Spec: `7ckptx` (worker lane containment: one authoritative signal per instruction)
- From-Spec: 7ckptx
- From-Backlog: vqv9im
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verified at: HEAD `e299a9a587fad4472dd694fb005c673160b883c8`, branch `aw/lane/4fodkt`

This is the record `h0zljh` E-02 promised and could not produce. It exists because that verification
was parked on the Order-0 ORCHESTRATOR, whose six children are all `executed`, so the runner would
retire it on sight and retirement deliberately skips the pre-transition checkpoint. The 31 live
criteria would have been marked demonstrated having never been run. Plan `4fodkt` carries the work as
a child that an agent actually executes; this file is its deliverable. No product code was authored.

## Summary

All 31 LIVE acceptance criteria of spec `7ckptx` Section 4 are demonstrated with pasted command
output. The 5 criteria that Section 4 marks WITHDRAWN were confirmed withdrawn at execution HEAD and
were deliberately NOT demonstrated.

| verdict | count |
| --- | --- |
| PASSED | 31 |
| FAILED | 0 |
| UNVERIFIED | 0 |
| **live total** | **31** |
| WITHDRAWN (confirmed, not demonstrated) | 5 |

ONE ADJACENT DEFECT WAS FOUND and is reported below rather than folded into a criterion's verdict: the
porcelain parser that R6.1 requires to have a single definition has been re-forked in
`runner_shared.dirty_tree_overlap`. It does not change any criterion's outcome, and it is a genuine
R6.1 violation.

TWO THINGS THIS RECORD IS NOT. It is not an independent audit: the same session that authored plan
`4fodkt` executed it. And it does not set the spec's status; see the closing section.

## 1. How the criterion list was derived (E-01)

RE-DERIVED FROM THE SPEC AT EXECUTION HEAD, not copied, because a copied enumeration is exactly how a
live criterion gets skipped. Every `A*` id in `## 4. Testable acceptance criteria` was partitioned by
whether its own text says `WITHDRAWN`.

```
TOTAL A* ids: 36
WITHDRAWN: 5 ['A7b', 'A7b-1', 'A7b-2', 'A7b-3', 'A7c']
LIVE: 31 ['A1', 'A2', 'A3', 'A4', 'A5', 'A5b', 'A5c', 'A6', 'A7', 'A8', 'A8b', 'A8c', 'A9',
          'A10b', 'A10c', 'A10e', 'A10d', 'A10', 'A11', 'A12', 'A12b', 'A13', 'A14', 'A14b',
          'A15', 'A15b', 'A16', 'A17', 'A18', 'A19', 'A20']
```

DIFFERENCES AGAINST THE TWO PRIOR ENUMERATIONS, both required to be reported:

1. Against the authoring-time measurement recorded in plan `4fodkt`'s history (36 total, 5 withdrawn,
   31 live): **NO DIFFERENCE**. The spec has not changed in this section since authoring.
2. Against the list written into `h0zljh` E-02 ("A1 through A20 plus A5b, A5c, A8b, A8c, A10b, A10c,
   A10d, A10e, A12b, A15b"): **ONE DIFFERENCE, CONFIRMED**. That list covers 30 of the 31 live ids and
   OMITS `A14b`, which is live, cites `R5.4`/`R6.1`, and carries an explicit anti-cheat clause.
   `A14b` was demonstrated here (it PASSES), so the omission cost nothing in the end, but it is
   precisely the failure mode E-02's own text warned about.

A NOTE ON FAMILY GROUPING, since the plan split the work by requirement family. Grouping by each
criterion's TRAILING requirement citation puts `A18` under R2 (it cites `R2.2`) and `A20` under R4 (it
cites `R4.6`), whereas the plan's item lists place them under R5 and R1. The plan's assignment governs,
per its own instruction that item boundaries stay fixed and a moved criterion is demonstrated under the
family the plan assigns it. Both are recorded so the difference is visible rather than silent.

## 2. Per-criterion results

Every row's verdict rests on pasted command output in the named evidence file. Evidence files live in
this run's lane submission directory, under
`.aw/state/lane-submissions/run-20260917T210518Z-1714328/02-4fodkt/attempt-1/evidence/`. That tree is
gitignored machine state, so the files are NOT committed; the substance of each is summarized here and
the commands are reproducible from the scripts in the same directory.

### R1: prompt containment and lane-path discipline (E-02)

| criterion | requirement | verdict | what was observed |
| --- | --- | --- | --- |
| A1 | R1.1, R1.2 | PASSED | Isolated prompts built from BOTH drivers; `absolute_paths_outside_lane` returns `[]` for each. The ONLY absolute path either prompt contains is the lane root itself. The recovery-path prompt is also clean, while still carrying the branch and prior disposition a resuming worker needs. |
| A2 | R1.3 | PASSED | Non-isolated prompt path-block digest, per driver: `oc_runipd` emitted `897a6dd4...` vs expected `897a6dd4...`; `agy_runipd` emitted `0ec64b99...` vs expected `0ec64b99...`. Both digests pasted, both identical. `build_prompt(lane_root=None)` is byte-identical to omitting the argument. |
| A17 | R1.4, R3.1 | PASSED | Both drivers emit `COMPLETE authorized workspace`, `it is your working directory`, `ISOLATED GIT WORKTREE`, and the exact token form `AW_MISSING_INPUT:<repo-relative-path>:<why it is required>`. All three worker paths are lane-RELATIVE (`is_absolute=False`). |
| A20 | R4.6 | PASSED | See section 3; demonstrated in two states AND observed live in this very turn. |

A1'S TWO NEGATIVE CONTROLS WERE RUN, NOT DESCRIBED.

Control 1, an injected out-of-lane absolute path: the detector returned that path for both drivers, so
the check FAILS when the product is broken.

Control 2, REWORDING the retired exception clause: four rewordings were tried against the R1.2 clause
detector. Three are caught. One is NOT:

```
reword 2: 'The five paths above are an exception to the rule; write them verbatim.'
  literal-fragment check catches it: False
  SEMANTIC check catches it       : False -> []
```

That is recorded rather than glossed, and it was then chased to a conclusion, because A1's subject is
"the check" and R1.1/R1.2 are verified by the COMPOSITE of the path scan and the clause checks. An
exception clause only violates R1.2 if there is an out-of-lane path for it to except, so the evasive
wording was re-tried together with the four paths it would except:

```
CASE 2: the evasive rewording PLUS the paths it would except (a REAL R1.2 violation)
    R1.1_out_of_lane_paths = ['.../runs/run-1', '.../decisions-and-questions.md',
                              '.../outcomes/01-aaaaaa.json', '.../execution-report.md']
    R1.2_literal_fragments = []
    R1.2_semantic_offenders = []
    -> check FAILS (violation detected)
```

So the composite check still fails, and A1 PASSES. The residual weakness in the clause detector is real
and is reported as finding F2 in section 5.

### R2: outcome reconciliation and submission collection (E-03)

| criterion | requirement | verdict | what was observed |
| --- | --- | --- | --- |
| A3 | R2.1 | PASSED | Same lane-written outcome, both drivers: `reconcile_disposition` returns `'partial'` (the empty-outcome fallback) WITHOUT collection and `'substantially-complete'` WITH it. The difference is the defect R2.1 exists to prevent. |
| A4 | R2.3 | PASSED | Both halves, separately. See below. |
| A5 | R2.4 | PASSED | An empty lane collects to a `complete` receipt whose three submissions are each `absent` with a reason, and `reconcile_disposition` returns `'partial'` with no exception, both drivers. |
| A5b | R2.5 | PASSED | Four states distinguishable from the RECEIPT alone: uncollected (`receipt=None`, file absent), collected (`status='complete'`, `result='collected'`, `source_sha256=6e6cffd9...`), interrupted (`status='in-progress'`), repeated (still 3 submissions, not duplicated). A FAILED collection is recorded as `result='failed'` with its `IsADirectoryError` reason rather than omitted. Receipts are attempt-keyed (`...attempt-1.json` vs `...attempt-2.json`, both present). |
| A5c | R2.6 | PASSED | 15 shared rules each have exactly ONE definition in the declared home `lane_containment.py`; neither driver re-defines any; `agy_runipd` imports none of them from `oc_runipd`. Established by AST and the import graph. |
| A18 | R2.2 | PASSED | After collection the lane still holds its outcome (201 bytes) and its decisions (39 bytes) while the driver side also holds them, so the retention classifier has evidence to inspect. |

A4'S TWO HALVES, SHOWN SEPARATELY because evidence for the first alone would pass while a sibling
lane's work was lost. A sibling lane collected FIRST, then this lane's collection ran TWICE:

```
[oc_runipd] HALF 1  own marker count after 2nd collection = 1   exactly once: True
[oc_runipd] HALF 2  SIBLING marker count after both runs  = 1   still present: True
[oc_runipd] register identical across the two runs (pure replace): True
```

and the register body shows both contributions in their own delimited blocks
(`<!-- aw:lane-decisions 02-bbbbbb-attempt-1 -->` and `01-aaaaaa-attempt-1`). Identical for
`agy_runipd`.

### R3: the missing-input refusal path (E-04)

| criterion | requirement | verdict | what was observed |
| --- | --- | --- | --- |
| A6 | R3.2, R3.3a, R3.6 | PASSED | See below. |
| A7 | R3.3, R3.5, R3.6 | PASSED | Eleven request shapes, ten distinct rules, every one `verdict='refused'` with `copied_into_lane=False` and `granted_original_checkout_access=False`, each carrying a specific reason. The lane was byte-for-byte unchanged after all eleven. |
| A19 | R3.7 | PASSED | For three paths, a denied-permission event and a worker token produce the same `rule`, the same `reason` and the same `verdict`, differing ONLY in `source` (`'denied-permission-event'` vs `'worker-token'`). `classify_denied_permission_path` is 25 lines and its only name-call is `classify_missing_input_report`. |

A6 IN ITS AMENDED REFUSAL FORM. A well-formed, existing, resolvable path was requested:

```
path = 'agent_workflows/engine.py'          <- the file DOES exist in the checkout
verdict = 'refused'
rule = 'withdrawn-repair-path'
copied_into_lane = False
granted_original_checkout_access = False
lane_preserved_for_missing_input(item) -> True
attempt['lane_paused_for_missing_input'] = True
lane files before = []   lane files after = []   unchanged: True
MissingInputDecision fields = ['path', 'reason', 'rule', 'source', 'detail', 'verdict']
grant-shaped fields          = []
```

A7'S SHARED-PREDICATE CLAUSE, PROVEN BEHAVIORALLY rather than by reading the AST: patching
`worktree_lease.path_is_worker_forbidden` moved the classifier's verdict from `withdrawn-repair-path`
to `coordinator-owned-surface`, which a copied list could not do, and the module was restored.

THE DELEGATION'S HONEST SCOPE, since overclaiming it would be the failure: only the
COORDINATOR-SURFACE class is delegated. The other nine classes are checked beside it in the one
classifier, which the classifier's own docstring explains (they are properties of a requested PATH,
and widening the shared predicate would change `assert_worker_scope`'s rule for a lane's declared
WRITES). R3.3 requires the reject set be the shared predicate rather than a second copy of the rules;
there is one definition of each class and both drivers reach it through one `MissingInputObserver`,
so no rule is forked.

HOW THE DRIVERS REACH IT, worth recording because a direct-call count is zero in both: each driver
constructs `lane_containment.MissingInputObserver` (`oc_runipd.py:6098`, `agy_runipd.py:2944`) and
feeds it stdout lines (`:6147`, `:2967`); the observer delegates to the one classifier. Fed a real
worker stdout line end to end, it wrote `event='missing-input-refused'` with
`rule='withdrawn-repair-path'` and copied nothing.

THE FIVE WITHDRAWN IDS were confirmed withdrawn from the spec text at HEAD (`A7b` at `:518`, `A7b-1`
`:524`, `A7b-2` `:529`, `A7b-3` `:533`, `A7c` `:537`, each saying `WITHDRAWN by R3.3a` in its own
line) and NONE of the five was demonstrated. Demonstrating any would assert behavior the spec now
forbids.

### R4: permission posture, turn bounds, and role selector (E-05)

| criterion | requirement | verdict | what was observed |
| --- | --- | --- | --- |
| A8 | R4.1, R4.1a, R4.2 | PASSED | OPENCODE: the runner emits `OPENCODE_CONFIG_CONTENT={"permission": {"external_directory": "deny", "question": "deny"}}`; after `pinned_child_env` the policy, the inherited `PATH` and the import pin all survive. Policy observation distinguishes three states: `observed`+`conforms=True`, `unverified`+`conforms=None` with a reason, and `observed`+`conforms=False` when a higher-precedence source overrode the runner. ANTIGRAVITY: `posture='no-denial-posture'`. The two hosts' postures differ, so no uniform assertion was made. |
| A8b | R4.1a | PASSED | The antigravity record's `posture` is not `denied`, it carries no `requested_policy`, and its `containment_layers` are exactly `CONTAINMENT_LAYERS_WITHOUT_HOST_DENIAL`, naming R1 prompt purity and R4.4 driver bounds. The opencode record names its own three layers instead, so the wording is not borrowed. |
| A8c | R4.1c | PASSED | `parse_args(['start','--repo','.','sel']).dangerously_skip_permissions = True`, and `argv.append("--dangerously-skip-permissions")` at `agy_runipd.py:2712`. |
| A9 | R4.3 | PASSED | Four operator shapes. An unrelated key is MERGED and preserved (`{"model": ..., "permission": ...}`). A conflicting `external_directory: allow` is merged with a LOUD note naming which keys the runner's denials won. Malformed JSON yields `source='override-unparseable-operator'` with the parse error and the original preserved on the record. No shape produces a silent overwrite. |
| A10b | R4.4, R4.4a | PASSED | `PERMISSION_TIMEOUT = 0.0`, `MAX_TURN_TIMEOUT = 14400.0` (4.00 h), no `*_DEADLINE` constants exist, both construct fine at 0, and both docstrings state MEASURED FROM and RESET BY explicitly. `TurnBoundWatch(` is constructed unconditionally in both drivers (`oc_runipd.py:6083`, `agy_runipd.py:2926`) with no enclosing isolation branch, so a non-isolated turn is armed too. |
| A10c | R4.4b | PASSED | Spec option (ii). The default remains `0`, and the artifact records that detection "is UNVERIFIED against a real ask", that the motivating evidence came from a LOG FILE rather than stdout, and, verbatim: "CONSEQUENCE, stated plainly: `MAX_TURN_TIMEOUT` is currently the ONLY bound covering a permission deadlock." |
| A10d | R4.4d | PASSED | `agy_runipd.DEFAULT_TIMEOUT='240m'` parses to `14400.0`; `driver_bound_for_host(14400.0)` returns `14100.0`, so the driver's bound fires 300s FIRST, and the docstring says which is expected to win. `bound_expiry_record` names the bound (`'permission-timeout'` vs `'max-turn-timeout'`) so a post-mortem can attribute the kill. |
| A10e | R4.4c | PASSED | Neither bound appears in `cli.py`, in either driver's argparse surface, or in the config modules; both remain 0-disable-able. The declaration-surface baseline is discussed below. |
| A10 | R4.4 | PASSED | The detector flags an unanswered ask on a top-level session AND on a NESTED CHILD session (the shape the measured deadlock took). A root-session answer does NOT clear a child ask; an answer on the child's own session does. Disposition is `'failed-safely'`. |
| A11 | R4.5 | PASSED | See below; demonstrated against the real CLI in this real lane. |

A10E'S BASELINE NEEDED AN EXPLICIT INVOCATION AND HAS A PRE-EXISTING FAILURE.
`tests/test_command_surface_declarations.py` is `pytestmark = pytest.mark.slow` while `addopts`
carries `-m 'not slow'`, so a bare suite run never executes it. Run explicitly it FAILS:

```
AssertionError: 5 != 0 : Found undeclared parser leaves:
  {'oc profile add', 'oc profile list', 'oc profile remove', 'oc profile default', 'oc profile show'}
```

A10e's wording is "no worse than its measured baseline", so the question is GROWTH. All five leaves are
`oc profile *`, introduced by the `runprofile` Set (commit `eaa51f9b`, 2026-09-06); the failure is
recorded as pre-existing in plans predating `lanectn`; and the spec ITSELF cites this test as already
failing when it argued for adding no new knobs. Neither timeout bound is among the leaves. So the
baseline did not grow and A10e passes.

A11 AGAINST THE REAL CLI, IN THIS REAL LANE. This turn genuinely runs with
`AW_EXECUTION_ROLE=worker`, so the refusal is live rather than simulated:

```
$ AW_EXECUTION_ROLE=worker python3 -m agent_workflows ipd begin <plan> --actor demo/verification
AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role process must
not run them (refused: aw ipd begin). ...
   exit code: 2

$ AW_EXECUTION_ROLE=worker python3 -m agent_workflows ipd finalize <plan> --actor ... --message ...
AW-LIFECYCLE-ROLE-001: ... (refused: aw ipd finalize). ...
   exit code: 2

- Status: approved          <- unchanged
still in pending/           <- unchanged
git status --porcelain: (clean)   <- the refused verbs wrote nothing
```

and the same binary outside worker role reaches the verb normally (`aw ipd lint` returns
`conforming`, exit 0). ONE HONEST NARROWING: the "driver's own invocation still succeeds" half was
shown with a READ-ONLY verb, deliberately, because running a real `begin` from this verification
would transition a plan it has no business transitioning.

### R5: inputs, clean base, and retention (E-06)

| criterion | requirement | verdict | what was observed |
| --- | --- | --- | --- |
| A12 | R5.1, R5.2 | PASSED | Every manifest entry records `"mode": "copy"` with a `source_sha256`. `verify_lane_input_manifest -> conforming=True`. Link independence checked by INODE and DEVICE, not just `is_symlink`: each input has `nlink=1` and a different inode from its source. Both negative controls detected: replacing a copy with a hard link, then with a symlink, each made `verify_link_independence` report not-independent. |
| A12b | R5.1a | PASSED | See below, all three parts. |
| A13 | R5.3 | PASSED | Both attachment classes localize into the lane and exist there; `attachments_outside_lane` returns `[]` for an argv carrying both. Two negative controls detected: an out-of-lane attachment, and a traversal (`lane/../../../plan.ipd.md`) that only looks contained. |
| A14 | R5.4 | PASSED | See below, four cases separately. |
| A14b | R5.4, R6.1 | PASSED | See below; the anti-cheat clause is honored. |
| A15 | R5.5, R5.6 | PASSED | See below, all four dispositions. |
| A15b | R5.6a | PASSED | See below; the run SUMMARY pasted. |
| A18 | R2.2 | PASSED | Recorded under R2 above. |

A12B'S THREE PARTS. (i) the manifest file is `-r--r--r--` (`0o444`), no owner write bit. (ii) each
materialized input is likewise `-r--r--r--`. (iii) an in-place append raises
`PermissionError: [Errno 13]`, while a legitimate input change produces a NEW revision (`rev-1`
becomes `rev-1` plus `rev-2`, with rev-1's manifest still present and unedited). THE HONEST LIMIT is
stated in the manifest's own `seal_note`: "Read-only is an ACCIDENT GUARD, not immutability and not a
boundary: the owning user can restore the write bit."

A14B IS THE CRITERION `h0zljh` E-02 OMITTED, and its anti-cheat clause is binding. Against a REAL
dirty git tree:

```
evaluate_clean_base(shared_tree=False) -> clean=False dirty_paths=['tracked.txt']
evaluate_clean_base(shared_tree=True ) -> clean=False dirty_paths=['tracked.txt']
IDENTICAL CLASSIFICATION : True   (both False)
IDENTICAL PATH LIST      : True

ANTI-CHEAT CHECK: does the implementation achieve the isolated behavior by making the RULE report
CLEAN?   rule.clean on isolated = False
-> A14b's forbidden implementation is ABSENT
```

and only the CALLER's disposition differs: `clean_base_launch_decision` returns `'warn'` for the
isolated result and `'refuse'` for the shared-tree one, both carrying the same dirty-path list. So
A14b PASSES on its own terms. The rule DOES call the shared porcelain parser; a separate fork exists
elsewhere and is reported as finding F1.

A14'S FOUR CASES, and a fixture correction worth recording. The guard's own call site passes
`--untracked-files=no`, which is what makes case (iv) true by construction; a first pass omitted that
flag and so listed untracked paths as dirty. Re-measured with the real flag:

| case | rule (both paths) | isolated caller | shared-tree caller |
| --- | --- | --- | --- |
| genuinely clean | `clean=True paths=[]` | `proceed` | `proceed` |
| dirty tracked, unstaged | `clean=False paths=['tracked.txt']` | `warn` | `refuse` |
| dirty tracked, staged | `clean=False paths=['tracked.txt']` | `warn` | `refuse` |
| untracked only | `clean=True paths=[]` | `proceed` | `proceed` |

The isolated turn PROCEEDS and the dirty paths are still recorded in durable state on BOTH
dispositions (`attempt["clean_base_dirty_paths"]` at `oc_runipd.py:6547`/`:6577` and
`agy_runipd.py:3333`/`:3361`, with `clean-base-warning` and `clean-base-refused` events), so this is
not the "passes equally if the report were silently dropped" case the spec warns about. Untracked
content is still reported once per run (`UntrackedDirtReport(total=1, sample=('untracked-only.txt',))`).

A15'S FOUR DISPOSITIONS, with the lane directory checked on disk after each. An unknown UNTRACKED
file, an unknown IGNORED file, and a dirty TRACKED file each leave the lane PRESERVED with the
condition named in the inventory. A lane whose submission was actually COLLECTED (receipt `complete`,
no failure) is TORN DOWN (`torn_down=True`, `lane still on disk: False`). The contrast case is the
useful one: the SAME lane shape whose collection FAILED is preserved, with
`submission_detail='collection FAILED for: outcome'`. A lane inspected with no receipt available is
also preserved, with `'no run directory or item was supplied, so no collection receipt can be read'`,
which is the fail-toward-preservation rule working rather than a defect. The R5.6 event names the
condition: `event='worktree-preserved'` with `retention_reasons=['unknown-ignored-file']`.

A15B'S RUN SUMMARY, pasted, because an event-only record does not satisfy it:

```
## Preserved lanes (NOT torn down)

Each lane below still exists on disk and still holds its branch. It was preserved rather than
destroyed because the driver could not account for its contents, or because its work was never
integrated (spec `7ckptx` R5.5, R5.6a).

- `aaaaaa` (position 1) lane `aw/lane/aaaaaa`
  - Worktree: `.aw/worktrees/aaaaaa`
  - Why preserved: an unknown IGNORED file remains in the lane: ignored-artifact.bin
  - Retention conditions: `unknown-ignored-file`
- `bbbbbb` (position 2) lane `aw/lane/bbbbbb`
  - Worktree: `.aw/worktrees/bbbbbb`
  - Why preserved: the lane's submission was never collected
  - Retention conditions: `uncollected-submission`
```

A run with nothing preserved renders `[]`, and the renderer is wired into the shared report writer at
`runner_shared.py:8920`.

### R6: shared predicates (E-07)

| criterion | requirement | verdict | what was observed |
| --- | --- | --- | --- |
| A16 | R6.1, R6.2, R6.3 | PASSED | Nine predicates in `wtiso_gate.py`, each with its state. |

FOUR IMPLEMENTED: `check_scope` (delegates to `ipd_lifecycle._scope_match`),
`format_missing_input` and `parse_missing_input` (delegate to the `lane_containment` token functions,
and both were verified to return IDENTICAL results to them), and `check_permission_deadline` (a real
body, unit-tested, exercised under A10 above).

FIVE RAISE, each CALLED with its real signature so the raise was observed rather than inferred. Each
message names a real owning plan id6 AND its disposition, and refuses to soften:

```
check_lifecycle_role  -> NotImplementedError, owner `rchpms` (Phase 2, RETIRED 2026-09-02, partly landed)
check_hook_bypass     -> NotImplementedError, owner `rchpms` (... its observed-from-git half never landed and has NO successor plan)
check_protected_refs  -> NotImplementedError, owners `2c122z` (RETIRED UNLANDED) and `1o4eif`
classify_retention    -> NotImplementedError, owner `rchpms` (... near-miss with `xdr83v` explained)
check_receipt         -> NotImplementedError, owners `rchpms` and `58ha43`, BOTH RETIRED
```

R6.3'S CASE: `check_scope` is implemented and has ZERO product call sites, which is correct rather
than an oversight, since its wiring phase was retired and no plan is chartered to wire it.

## 3. A20 (R4.6), and why this turn is unusually good evidence for it

A20 permits satisfaction by citing the sequencing constraint and showing the two states, but forbids
claiming R4.6 holds without evidence the ordering was actually respected. Three independent pieces:

STATE B (shipped): the isolated prompt's out-of-lane absolutes are `[]`.
STATE A (reconstructed pre-R1.1): re-adding the five driver-owned paths makes the scan return four
out-of-lane absolutes, which the denial posture would refuse.

THE ORDERING WAS ACTUALLY RESPECTED, from git history: R1.1's lane-relative prompt landed in
`a7736095` at 2026-09-05 03:24, and the opencode denial policy landed in `8a491d4c` at 2026-09-05
19:59, roughly 16 hours later. The plan that owns the posture (`lhmrhx`) declares
`Item-Dependencies: executed:cqx5v7`, the plan that owns the prompt.

AND IT WAS OBSERVED LIVE IN THIS TURN, which is the strongest of the three. This turn runs with the
denial active (`OPENCODE_CONFIG_CONTENT` carries `external_directory: deny`, matching
`LANE_PERMISSION_POLICY` exactly). Early in the turn the agent tried to read the spec by its
MAIN-CHECKOUT absolute path; the host REFUSED the tool call, citing
`{"permission":"external_directory","pattern":"*","action":"deny"}`. The identical read of the
IN-LANE copy succeeded. So with the denial active a prompt still naming out-of-lane paths would fail
on those paths, and with R1.1 satisfied this turn proceeded to completion.

## 4. Closing reconciliation

Computed by COMPARING E-01's derived LIVE list against the verdict table, not asserted:

```
E-01 LIVE list (31)          vs   verdicts assigned (31)
LIVE ids with NO verdict (missing)        : NONE
verdicts for ids that are NOT live (extra): NONE
ids assigned a verdict MORE THAN ONCE     : NONE
withdrawn ids given a verdict             : NONE
every live id appears in exactly ONE item: True

PASSED: 31   FAILED: 0   UNVERIFIED: 0   TOTAL: 31  (equals the LIVE count 31: True)
```

Per-item coverage: E-02 n=4, E-03 n=5, E-04 n=3, E-05 n=10, E-06 n=8, E-07 n=1.

## 5. Findings (defects found while verifying)

### F1 (MEDIUM): the ONE porcelain parser required by R6.1 has been re-forked

`lane_containment.parse_porcelain_entries` documents itself as "THE ONE PORCELAIN PARSER (spec R6.1),
and the ONLY place the porcelain FORMAT is decoded", and records that it replaced inline copies in
both drivers. But `runner_shared.dirty_tree_overlap` (`runner_shared.py:1957-1971`) decodes porcelain
INLINE again: it strips the two status columns and splits `orig -> dest` itself, and calls neither
`parse_porcelain_paths` nor `parse_porcelain_entries`.

WHY THE EXISTING TEST DOES NOT CATCH IT.
`tests/test_lane_clean_base.py::SharedPredicateTests::test_dirty_tree_overlap_no_longer_forks_the_parser`
accepts two shapes: SHAPE A, where a driver re-exports the shared object, short-circuits with
`continue`; SHAPE B, a local wrapper, must call the shared parser. Both drivers now take SHAPE A
(`oc_runipd.dirty_tree_overlap is runner_shared.dirty_tree_overlap` is `True`), so the test never
reaches its parser assertion, and the shared object it re-exports is the one carrying the re-forked
loop. The test's reasoning is sound for what it asserts (an identity re-export cannot drift between
HOSTS); the gap is that it stopped checking whether the shared implementation still delegates parsing.

IMPACT, NOT INFLATED: the two decoders agree on the cases exercised here, so no behavioral difference
is demonstrated. R6.1 is explicit that this is non-conforming anyway ("Forking the rule is
non-conforming even when the copies agree at the time of writing"), and the divergence risk is
concrete: the shared parser KEEPS the status columns, which is what lets the retention inventory tell
a dirty TRACKED file from an UNTRACKED one from an IGNORED one, while the inline copy discards them.

This does NOT change A14b's verdict: A14b asserts the clean-base RULE's classification and the
caller's disposition, `evaluate_clean_base` does call the shared parser, and both were measured
conforming.

### F2 (LOW): the R1.2 clause detector misses a plausible rewording

The semantic check pairs an "outside the lane" phrase with a permission word. The rewording `The five
paths above are an exception to the rule; write them verbatim.` names no outside-the-lane referent and
so is not matched. A1 still PASSES because the composite check catches any such clause that actually
introduces an out-of-lane path (section 2). The residual gap is a clause that grants permission using
only RELATIVE traversal (for example authorizing `../../..`), which would evade both the path scan
(it matches absolute paths) and the clause detector.

## 6. Honest limits of this record

1. NOT AN INDEPENDENT AUDIT. The same session authored plan `4fodkt` and executed it. An independent
   verifier would be stronger evidence.
2. MOSTLY SYNTHETIC FIXTURES. A12, A12b, A13, A14, A14b, A15, A15b, A3, A4, A5, A5b, A6, A7, A19,
   A8, A8b, A8c, A9, A10b, A10c, A10d, A10e, A10 and A16 were demonstrated against temporary
   directories, real-but-throwaway git repositories, and direct calls to the shipped functions,
   NOT by observing a full production run. Three criteria have live evidence from this turn itself:
   A8 (the denial policy in this worker's environment), A11 (the CLI refusal in this real lane), and
   A20 (an actual host refusal of an out-of-lane read).
3. SINGLE OBSERVATION, NOT REPEATED. Every criterion was demonstrated once. Nothing here establishes
   flake-freedom or behavior under concurrency.
4. A10C TAKES THE SPEC'S OPTION (ii), NOT (i). No real permission ask was provoked and captured. The
   bound therefore remains disabled, which is what the spec requires in that branch, but this record
   does not prove the detector works on a live stream.
5. A11'S SECOND HALF USED A READ-ONLY VERB. The driver-role success was shown with `aw ipd lint`
   rather than a real `begin`, deliberately, to avoid transitioning a plan.
6. THE EVIDENCE FILES ARE NOT COMMITTED. They live under `.aw/state/`, which is gitignored machine
   state. The scripts that produce them sit beside them, so the measurements are reproducible, but a
   future reader of the repository alone has this walkthrough's quotations rather than the raw files.
7. TWO SELF-CORRECTIONS ARE PART OF THE RECORD. Several first-pass probes were wrong about the PROBE
   rather than the code: an ast docstring extractor missed `#:` comment blocks (A10b, A10c), a
   "count `terminate_process` definitions" check flagged the two thin per-host delegators as second
   reapers (A10), a teardown fixture passed a bare path where a `handle.path` object was required
   (A15), a summary fixture used the wrong state keys (A15b), and a clean-base fixture omitted
   `--untracked-files=no` (A14). Each was corrected and re-measured, and both the wrong and the
   corrected observations are retained in the evidence directory rather than the wrong ones deleted.

## 7. What this record does NOT decide

SPEC `7ckptx` IS NOT SET TO `implemented` HERE. An agent may not make that transition; it requires
cited evidence and is the maintainer's call. The evidence for the decision: all 31 live acceptance
criteria PASS with pasted output at HEAD `e299a9a5`, all six children of Set `lanectn` are in
`.aw/records/plans/executed/`, and the bare suite is green (`7825 passed, 3 skipped, 2 xfailed`). The
counter-consideration the maintainer should weigh: finding F1 is a live R6.1 violation in adjacent
code, and this verification was not independent.

BACKLOG `vqv9im` IS NOT SET TO `done` HERE. `h0zljh` E-03 assigns that transition to the
orchestrator, and moving it into a verification child would spread the parent's bookkeeping across
two artifacts.

THE SET IS DEMONSTRABLY COMPLETE against spec `7ckptx` Section 4: no live criterion is FAILED and none
is UNVERIFIED. That statement is scoped to Section 4's criteria and carries the limits in section 6.
