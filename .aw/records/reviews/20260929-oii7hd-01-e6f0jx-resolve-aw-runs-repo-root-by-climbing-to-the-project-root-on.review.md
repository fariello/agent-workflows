# Review findings: plan e6f0jx

- Subject-Id: e6f0jx
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `10947a78` in a lane worktree. Structural preflight `aw ipd lint --phase author`
CONFORMED before revision (exit 0, `findings: 0`); `--phase review-finalize` conforms after revision
with all seven `E-*`/`V-*` pairs. No pre-review snapshot was owed: the plan was committed and unmodified
at review start, and the lane-input copy under `.aw/state/lane-inputs/rev-17/` is byte-identical to the
tracked plan. Bare suite at review HEAD: `3246 passed, 2 skipped, 3 warnings in 48.10s`. The named
baseline modules: `tests/test_run_viewer.py tests/test_run_analytics_cli.py tests/test_project_context.py`
-> `65 passed in 7.58s`, matching the plan's F-13 arithmetic (38 + 27). NO PRODUCTION FILE OR TEST WAS
MODIFIED by this review; measurements ran against purpose-built fixtures under `.aw/state/runtime/`,
deleted afterwards, and never against the live `.aw/records/runs/`.

THIS IS AN UNUSUALLY WELL-EVIDENCED PLAN AND EVERY MATERIAL FINDING REPRODUCES. I re-measured the
load-bearing ones rather than accepting them.

F-01 reproduces exactly. On a fixture holding `.aw/records/runs/run-abc123/state.json`, `aw runs
run-abc123` from the project root renders the run at exit 0, and from `sub/` emits `error: no run matched
target 'run-abc123'` at unpiped exit 2.

F-03's four sites are all present as described: `run_viewer.run_viewer_cli` (`repo_root =
Path(getattr(args, "dir", None) or ".")`), `run_cli.resolve_ledger_path` (`root = Path(repo_root).resolve()
if repo_root else Path.cwd().resolve()`), `run_cli._classify_absent_target` (`repo_root = Path(repo_dir) if
repo_dir else Path(".")`), and `run_analytics_cli._repo_root` (`return Path(getattr(args, "dir", None) or
".")`). F-04's precedent is real: `run_cli._projection_dir` already calls `resolve_verb_repo_root`.

F-05 AND F-06 REPRODUCE, AND F-05 IS THE FINDING THAT JUSTIFIES THE RELEASE GATE. From `sub/`, `aw runs
analyze` exited 0 printing `CONFORMS  analyzed 0 run(s)` and CREATED a machine-local project tree that did
not exist before the invocation, containing `records/runs/analytics/` with `cache/salt`,
`versions/v000001/manifest.json`, `analysis.json`, `report.html`, `index.html` and a `latest` symlink. The
same command at the fixture root exited 1 with `FINDINGS  analyzed 1 run(s): 0 cached, 0 rebuilt, 1
skipped` and published inside the fixture. So the wrong invocation is quieter than the right one, exactly
as F-06 says.

F-07 reproduces by count: `grep -c "IS a driver run"` is 1 at the project root and 0 from `sub/`.

F-08 reproduces, including the self-contradiction. `d91i3e`'s findings-table F-15 axis (c) says the viewer
"resolves through `resolve_verb_repo_root`, which CLIMBS to the project root" and that from `tests/` `aw
runs repair <id>` SUCCEEDS; its own V-02 axis (c) transcript says "It does not. `run_viewer_cli` reads
`Path(getattr(args, "dir", None) or ".")` directly". The transcript is the correct half.

F-10, F-15 AND OQ-02'S BASIS ALL HOLD. On a canonical-root fixture the emitted `run_dir` is absolute and
`agent_schema.validate_agent_record` returns `Unsanitized absolute home path in field 'run_dir'`; on a
legacy-root fixture it is `.aw/runs/run-legacy1` and no `run_dir` violation is reported. I also confirmed
the climb's effect directly: `discover_run_dirs(Path("."))` on the legacy fixture returns
`.aw/runs/run-legacy1` while `discover_run_dirs(resolve_verb_repo_root(None))` returns the absolute path,
which is precisely why normalization is required rather than optional. `normalize_repo_path` turns the
absolute canonical path into `.aw/records/runs/run-abc123` and passes the legacy relative value through
unchanged. F-11 (`relative_to` count 0 in `run_viewer`), F-12 (`tests/test_run_recovery_cli.py` absent,
`TestLedgerResolutionAndWrongFormatVerdict` nowhere, one surviving `resolve_ledger_path` reference at
`tests/test_run_viewer.py:1880`) and F-14 (76 across 23 vs the docstring's recorded 64 across 21) all
confirm.

E-02's design is sound and I verified its mechanism: with the fixture's ledger under `.aw/state/runs/`,
`resolve_ledger_path('run-led1')` from `sub/` returns `None` (today's defect) while
`resolve_ledger_path('run-led1', resolve_verb_repo_root(None))` resolves it. The four named callers
(`_run_show`, `_run_evidence`, `_run_verify_ledger`, `_resolve_or_error`) are accurate, and each uses
`repo_dir` for nothing but this call, so resolving at the leaf boundary is safe. The `--dir` contract is
preserved by construction and I confirmed it end to end: `aw runs --dir <fixture> run-abc123` from `sub/`
renders at exit 0 today.

WHAT I FOUND THAT THE PLAN DID NOT. Four findings, all IN-SCOPE gaps in an otherwise correct plan, and two
of them are ways it could have shipped a half fix or a test that proves nothing.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | UNDER-SCOPE | E (testing) / D (anti-regression) | plan E-05 case list; `agent_workflows/project_context.py` `_is_project_marker` | E-05's fixture recipe requires only `.aw/records/`, but V-01 demands legacy-root before/after evidence and NO E-05 case exercises the legacy root. Worse, a legacy fixture built the obvious way (holding only `.aw/runs/<run>`) is NOT a project root, because `_is_project_marker` requires a durable `system`/`records`/`config` child. MEASURED: from such a fixture's `sub/`, `find_project_root()` returned THIS CHECKOUT's root, not the fixture, so the case would silently test the live repository and pass or fail for unrelated reasons | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-05 case (h) added, asserting the emitted `run_dir` is repo-relative on BOTH surfaces for BOTH roots, with the legacy fixture explicitly required to carry a durable `.aw/records/` alongside its `.aw/runs/`. E-05's expected outcome is now eight cases with (h) among those that must fail pre-change. V-05 additionally requires the resolved-root-equals-fixture assertion, and new F-19 records the measurement |
| PR-102 | HIGH | IN-SCOPE | A (correctness) / B (privacy) | plan E-01; `agent_workflows/run_viewer.py` `r_dict["run_dir"] = str(...)` and `s_dict["run_dir"] = str(...)` | `run_dir` is stringified at TWO sites (the `--json` branch and the `--agent` branch) and BOTH leak the absolute path today, reproduced on a fixture; `aw runs list --agent` reaches the `--agent` site by a third route. E-01 said only "normalize `run_dir`", which a literal executor could satisfy on one branch, leaving the other emitting the home path the gate paragraph itself calls the way this plan can silently make the payload worse | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | E-01 now names both stringification sites, records that both leak today, notes `aw runs list --agent` as the third route, and states that `normalize_repo_path` is idempotent on an already-relative value so no per-root branch is needed. V-01 now requires the before/after paste from BOTH `--json` and `--agent` and explicitly refuses an `--agent`-only paste. New F-16 and F-18 record the measurements |
| PR-103 | MEDIUM | IN-SCOPE | E (testing) / honest evidence | plan V-01; `agent_schema.validate_agent_record` | V-01 tells the executor to paste `validate_agent_record` on the after-payload and show zero `run_dir` home-path findings, but that validator returns FOUR findings on this payload, not one: the `run_dir` path PLUS `Invalid schema`, `Invalid kind` and `Field 'cmd' must be a non-empty string`. The plan's own convention note and `d91i3e` F-16 both record that non-conformance as pre-existing and out of scope, but V-01 did not say so, so an executor could read a still-failing validator as a failure of E-01 or try to fix a machine contract this plan deliberately does not touch | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now states that the three schema findings are the pre-existing non-conformance F-17 records, are NOT this plan's to fix, and that neither their presence nor their absence bears on this item. New F-17 records the measured four-finding output |
| PR-104 | LOW | IN-SCOPE | G (plan executability) / plan-review Step 4 | plan gate, final sentence | The transition sentence forbade moving the plan before the gate conforms but did not state the conditional runner/executor ownership of `aw ipd finalize`, nor that the release-gating backlog item must not be closed `done` here | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate's final paragraph rewritten to the conditional-ownership wording (runner owns it under `aw oc run`/`aw agy run`; a hand execution invokes it; never hand-roll a `git mv`), plus the `oii7hd` `graduated`-not-`done` obligation that preserves the inherited `Blocks-Release: next` |

No finding was DEFERRED and none was left OPEN, so no escalation to a `- Blocking: yes` question is owed
(`check.review-finding-unescalated` satisfied vacuously). No `BLOCKER` was found. Both HIGH findings were
fixed in place, so none remains unfixed.

WHAT I DELIBERATELY DID NOT FLAG. The scope fence is correctly worded under the 2026-09-01 maintainer
ruling: it says an out-of-scope edit is to be MADE and then JUSTIFIED with a `--scope-reason`, and it
carries no "STOP and report" directive for the scope case, so it must not be flagged for lacking one.
E-07's may-be-a-no-op shape is legitimate and not an empty item: it forces a visible decision and V-07
requires evidence either way. The four `Carrier-Declined` rows each state a reason that survives scrutiny;
in particular the `okm6e6`/`quqyc4` row is right that pointing at a `done` item which shipped only the
documentation would misrepresent a note as a fix. The release gate is consistent: backlog `oii7hd` is
`Work-Kind: bug`, `Blocks-Release: next`, `graduated`, and the plan inherits the gate; `aw check
release-gates` conforms.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-05 had no legacy-root case while V-01 demanded legacy-root evidence. Add a case, or relax V-01? | Add case (h) covering both roots on both surfaces | Relaxing V-01 to canonical-only, rejected because the legacy root is exactly where the shape DIVERGES (F-10) and is the reason OQ-02 exists; dropping it would leave the plan's own central shape decision unpinned | The plan's F-10 and V-01 as authored; `_is_project_marker` measured at review, which also dictates how the fixture must be built | yes |
| D-2 | Is the two-site normalization a scope widening needing maintainer sign-off? | No; it is the same one-field fix E-01 already owns, stated completely | Filing a separate follow-up for the `--json` site, rejected because it would knowingly ship a half fix of a privacy leak the plan's own gate paragraph identifies as its silent-failure mode | Both sites are in `run_viewer.py`, already declared in `- Scope-Paths:`; F-15's leak is one FIELD, and E-01 already owns normalizing that field | yes |
| D-3 | Should this review resolve OQ-03 (the zero-run `CONFORMS` exit contract) rather than leave it open to the maintainer? | No; leave `open` with `Owner: maintainer` | Resolving it from evidence, rejected because the measurement genuinely does not establish a defect: both verdicts are correct for their inputs, and whether an empty analysis should refuse is a judgement about what `CONFORMS` asserts | plan F-06 and OQ-03's own reasoning, re-measured at review (root exit 1 with one skipped run, `sub/` exit 0 with zero runs); it is non-blocking so it does not gate readiness | yes |
| D-4 | Should OQ-04 be resolved by the reviewer, given E-07 defaults to no edit? | No; leave `open` with `Owner: maintainer` and let E-07 decide visibly at execution | Resolving YES and mandating the docstring line, rejected because the docstring explicitly says the gap "does not license converting them on the way past", and a reviewer mandating a shared-documentation edit about a design question neither plan settled is the scope creep that note guards against | `project_context.resolve_verb_repo_root`'s own docstring, read at review; the question is non-blocking and self-closing inside E-07/V-07 | yes |

No `Reversible: no` decision was taken, so no escalation is owed under the irreversible-decision rule.

### Note for the maintainer (not a plan finding)

Reproducing F-05 necessarily created one machine-local directory OUTSIDE this workspace,
`~/.aw/projects/sub-032a16`, which is the very defect the plan fixes. I could not delete it: the path is
outside my authorized workspace and the removal was refused. It is inert (an analytics bundle for a
throwaway fixture) and safe to delete by hand. Noted here rather than silently left, and it is incidental
evidence that F-05 is real rather than theoretical. A pre-existing `~/.aw/projects/sub-42bd16` was present
BEFORE my probe and is not mine.
