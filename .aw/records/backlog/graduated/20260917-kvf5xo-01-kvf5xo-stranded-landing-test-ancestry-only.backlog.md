- Id: kvf5xo
- Status: graduated
- Blocks-Release: next
- Set: kvf5xo
- Priority: high
- Work-Kind: bug
- Summary: aw attention --check fails closed against spec F3a's own normative exclusion: the landing test is ancestry-only, so six re-executed lanes whose work IS on main report STRANDED forever

## Workflow history
- 2026-09-18 graduated (aw set): Design handed off to plan 0ta5vg (stranrep-01), which fixes all four stranded-report defects as one cohesive change; that plan carries From-Backlog: kvf5xo and inherits Blocks-Release: next
- 2026-09-17 created (aw backlog): lane_work_has_landed tests only git merge-base --is-ancestor, so a lane whose work reached main by re-execution reports STRANDED forever; six of twelve reported lanes are such cases, violating spec F3a's normative landing exclusion

Spec `attention-registry-and-cross-tree-status` F3a makes an exclusion NORMATIVE (spec line 233):

    TWO EXCLUSIONS ARE NORMATIVE, because a check that fails on correct behavior is a check operators
    bypass. A lane owned by a LIVE driver process ... MUST NOT fail the gate; and a lane whose work HAS
    reached the integration target MUST NOT fail it either, which requires a reachability test against
    the target and cannot be decided from "the lane holds commits beyond its own base" alone.

The only landing test is `runner_shared.lane_work_has_landed` (`runner_shared.py:1077-1107`), a single:

    git merge-base --is-ancestor <branch> <target>

That answers ANCESTRY. It cannot see work that reached the target by RE-EXECUTION, cherry-pick, rebase
or reimplementation, all of which land the CONTENT without making the dead branch an ancestor.

## Measured: six of twelve reported lanes are re-executed first attempts whose work IS on main

Each plan below was re-executed on a SECOND lane; that second lane is what integrated, so the first
lane's branch is not an ancestor of the finalize commit, yet the content shipped. Finalize commit on
`main`, and the signature symbol proving the work is present (measured 2026-09-18):

| lane | finalized on main by | proof the work is on main |
|---|---|---|
| `03ie04` | `bc9b3f43` | `oc_runipd.edge_satisfied` carries the directory-vs-field precedence rule, its comment citing "depreview 03ie04 E-01, OQ-01" |
| `fn2l1u` | `e0c139ea` | `attention_contract.actor_refusal` (`attention_contract.py:618`) |
| `mm5p3v` | `a912d5a9` | `aw runs analyze --help` works |
| `nna8yz` | `14d5429a` | `lane_containment.LANE_INPUT_SUBDIR` / `LANE_INPUT_MANIFEST_NAME` |
| `r2i1b1` | `84c5adcd` | `render_stream.Refusal` + the `remedy` field in `run_viewer` |
| `ybkmzp` | `68930180` | `runner_shared.resolve_verification_decision` |

For every one, `git merge-base --is-ancestor aw/lane/<id> <finalize commit>` returns non-zero, i.e. the
reported lane is NOT an ancestor of the commit that finalized its own plan. All six plans are filed
`executed` on `main`.

## Consequence

`aw attention --check` fails closed permanently against F3a's own normative exclusion. Combined with
the five deliberately-retired `wtiso` lanes (whose retirement reasoning is already written in
`.aw/records/plans/superseded/`) and `d7qoxv` (whose single commit would REGRESS a plan from `executed`
to `approved`, see `wlyg3g`), the current report contains ZERO lanes that need recovering. A gate that
is permanently red on nothing trains its own dismissal, and buries any FUTURE genuine strand.

## IMPORTANT: this contradicts a review finding, deliberately

Plan `ut0vzr`'s review record (2026-09-18) states "the report already excludes a merged lane ...
Measured at review HEAD, `aw attention --check` reported 12 distinct lanes and ALL 12 were provably not
ancestors of `main`, i.e. zero false positives." That measurement is CORRECT and this item does not
dispute it. The disagreement is over which question counts: "not an ancestor of `main`" is true of all
12, while F3a asks whether the WORK REACHED THE TARGET. By F3a's standard six are false alarms. Stating
this explicitly so the two records are not read as a contradiction to be resolved by picking one.

## Expected

The landing exclusion is satisfied by CONTENT reaching the target, not only by ancestry. A lane whose
commits are all represented on the target is LANDED and silent.

## Fix sketch

1. Add a CONTENT-landed reading beside the ancestry one, as a NEW helper. Use `git cherry <target>
   <branch>`, which compares PATCH IDS and so sees a cherry-pick or rebase; an all-`-` result means
   landed. Keep the same three-valued `True`/`False`/`None` contract, so an unanswerable question stays
   UNKNOWN and never reads as either answer.
2. Do NOT edit `describe_lane`: its body is pinned byte-for-byte against
   `tests/fixtures/runner_shared_premove_fingerprints.json` (captured at HEAD `1ecc5891`) to prove a
   pure move out of the two runners. `lane_work_has_landed` exists as a separate helper for exactly this
   reason (`runner_shared.py:1124-1130`). New readings go in new helpers.
3. Consult both readings in `classify_lane_integration` (`runner_shared.py:1110-1191`) so `STRANDED`
   requires absence by BOTH; record which reading settled it (e.g. `landed_by`) for debuggability.
4. AMEND F3a to say the exclusion is content-based, since its "requires a reachability test against the
   target" wording is what licensed the ancestor-only reading. Narrowing and additive: nothing that
   previously failed stops failing except the case F3a already said must not fail. If the new key
   surfaces in `--json`, F8 obliges a `schema_version` bump.
5. Regression test in a temporary git repo (NOT the developer's real repo, per `no0j8g`): a lane whose
   commits were cherry-picked onto the target reports LANDED; a lane with a genuinely absent commit
   still reports STRANDED. Note the target defaults to `HEAD`, not `main`
   (`LANE_INTEGRATION_TARGET_FALLBACK`, `runner_shared.py:1074`), so a test must control HEAD.

## A discarded approach, recorded so it is not retried

Text-similarity is NOT a sound landing test. Added-line presence for these lanes measured 8-18% against
`main` even where the work is demonstrably present: `03ie04` scored 8%, yet its fix is on `main` and its
comment cites the plan by id. The fix was REIMPLEMENTED with the same rationale, not cherry-picked. Use
patch ids, and accept that a genuine reimplementation may still not be provable mechanically.

## Honest limit

`git cherry` will NOT resolve a lane whose work was reimplemented rather than cherry-picked, and
`03ie04` is the likely such case. A lane the reading cannot resolve must stay reported (UNKNOWN or
STRANDED) and be escalated to a human, never quietly reclassified: a false LANDED is strictly worse
than the current false STRANDED, because it hides real loss.
