# Review findings: plan 7ehv8l

- Subject-Id: 7ehv8l
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `bfdcb514f` in a runner review-sweep lane worktree (non-interactive). The lane-input
copy (revision 1) is byte-identical to the tracked plan, which was committed and unmodified, so no
pre-review snapshot was needed. `aw ipd lint --phase author` reported clean before the revisions.

The plan's record-change claims were reproduced on a throwaway `git clone --shared` of this lane,
created under the gitignored `.aw/state/` and then deleted: E-02, E-03 and E-04 were run as written
(with `--yes`), followed by `aw commit --no-plan` on the four record paths. Observed:
- `aw specs set superseded 2vev8j --from-backlog -` moved the file to `specs/superseded/`, set
  `- Status: superseded`, removed `- From-Backlog: ms06pi`, kept `- Blocks-Release: next`, and added one
  history line. With `--no-commit` the setter STAGES the rename itself (`git status` shows `RM`).
- `aw specs set approved 4sd62s --from-backlog ms06pi` reported `unchanged` and added exactly two lines:
  `- From-Backlog: ms06pi` and `- 2026-11-06 approved (aw set): ...` (the tag is the status, because
  `status_set` writes `status_tag = norm_status` for a same-status spec write).
- `aw backlog set graduated ms06pi` added one `same-status` history line and nothing else.
- Afterwards: `aw releases show next` listed `ms06pi` and `4sd62s` and not `2vev8j`; `aw specs check`
  printed "all specs conform. 48 specs checked."; `aw check release-gates` printed "CONFORMS 76
  release-gates checked ... errors 0 warnings 0 info 0"; `find_from_backlog_artifacts(repo, 'ms06pi')`
  returned only the `4sd62s` path; `evaluate_blocking_close(repo, <ms06pi path>, 'done')` refused with
  only `4sd62s` named as not shipped; and `aw check --agent` severity counts were unchanged at
  `{'error': 14, 'warning': 1, 'info': 55}`, with the only matching diagnostic being
  `check.spec-criteria-uncovered` at the new `superseded/` path.
- `aw commit --no-plan -- <old path> <new path> <4sd62s> <ms06pi>` committed all 4 paths as one commit
  (rename detected), leaving a clean tree.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| E-01 | Baseline saved to `/tmp/opencode/...` | Saved to `.aw/state/7ehv8l/check-before.jsonl` | A lane may refuse writes outside its workspace (measured at review); `.aw/state/` is gitignored. |
| E-01, E-05, E-06, V-01, V-05, V-06 | Hard-coded "16 files", "8 named modules", "16-line" output | Re-derived file list from E-01 is the bar; authoring counts kept as context | Rubric G re-derivation convention for live-artifact counts. |
| E-05 mapping | E1 -> `4sd62s` C3 and 4.7 | Adds `4sd62s` P3, which cites the measured evidence, and states the rewrite cites where it is recorded | `4sd62s` C3 is a requirement, not the measurement the comment describes. |
| E-05 namespace-gate comment | "the superseded artifact-metadata-storage spec (now 4sd62s)" | "the artifact-metadata-storage spec since superseded by 4sd62s" | The comment records a historical measurement; the old text implied `4sd62s` was the measured spec. |
| F-05 | "after E-NEW steps" | "after the E-02 to E-04 steps", with the review re-measurement | Stale placeholder token. |
| V-05 | No per-line check for modules | Adds `git diff -U0 -- agent_workflows` line check | E-05's outcome ("every changed line is a comment, docstring, or the recovery string") had no evidence demand. |
| Gate | Partial execution contract | Adds resolved-questions note, fence as declaration with `--scope-reason`/`--scope-ack`, rename-commit note, no `git add -A`, honesty rule, runner vs hand finalize ownership | S7 execution-contract rule. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes: it changes two spec records (status of `2vev8j`, `- From-Backlog:` of `4sd62s`) and one user-facing `recovery=` hint string in `check_engine.py`.
2. No: none of the named guard modules (`leak_sanitizer`, `git_commit_helper`, `commit_lock`, `lane_containment`, sandbox) is touched; `status_set.py` changes in one comment only.
3. Moderately: 7 E-items in 4 task groups, touching 8 modules and 8 tests, but every code change is a comment or docstring.
4. Yes: `- Scope-Paths:` lists all 21 paths, including both locations of `2vev8j`.
5. Low: the record changes are reversible through the setters, and the release-gate effect was measured clean. The real risk is ordering: clearing `2vev8j`'s link before `4sd62s` holds it leaves `ms06pi` briefly with no carrier, which E-02 to E-04 sequence correctly within one uncommitted change.

AW-TIER: standard

### Step R1

- Checked: `4sd62s` "Relation to prior work", OQ-4 and section 7 ("The first plan of phase A also SUPERSEDES `2vev8j`"); `4sd62s` 4.2 (`seq` "from `2vev8j` 4.3"), 4.2b ("taken from `2vev8j` 4.4"), C6 ("from `2vev8j` C5"), C3, P3 (cites `2vev8j` E1 to E4), 4.7; `2vev8j` C5, 4.3, 4.4, E1 headings; every `rg -n 2vev8j` hit in `agent_workflows/` and `tests/` (16 files, 18 module lines and 14 test lines, matching F-01); `check_engine.py::find_from_backlog_artifacts`, `check_engine.py::_carrier_is_executed` (a spec counts only at `implemented`), `check_engine.py::evaluate_blocking_close`, `releases.py::get_release_blockers` (reuses `attention.release_blockers`, live items only); `check_engine.py::check_spec_criteria_coverage` loop (keys on `From-Spec`, not on status, so the `2vev8j` advisory follows the file, as E-07 predicts); `aw specs set --help` (`--from-backlog` accepts `-`); `tests/test_check_engine_release_gate.py` and `tests/test_release_gate_one_way_mismatch.py` exist; `CHANGELOG.md` is the only other non-record file citing `2vev8j`.
- All citations resolve. The one mapping gap (E1 -> C3) is PR-003.

### Step R2

- Checked: E/V bijection 7/7, each V demands pasted diffs, command output or test summaries (reachable by construction; no runtime observation demands beyond the setter output that E-02 to E-04 produce); Scope-Paths covers every file the plan edits, including both `2vev8j` locations; `- Item-Dependencies: none` is correct (Order 01, nothing in the Set precedes it; the orchestrator `63ib9r` is Order 00); no `4sd62s` AC is claimed, so the qualified-citation convention has nothing to qualify. Hard-coded live counts are PR-002. The gate contract gap is PR-005.

### Step R3

- Checked: no secrets, inputs, network or privileged paths. The only user-facing string change is the `recovery=` hint. Release-gate integrity is the security-relevant invariant: the review reproduction shows the gate stays carried (`ms06pi` and `4sd62s` remain listed, close remains refused until `4sd62s` is implemented). `aw sanitize --agent` is in E-07. No finding.

### Step R4

- Checked: A, setter writes are tooled and atomic per file, and the single path-scoped commit keeps the three record changes together; C, reuses `aw specs set`, `aw backlog set` and `aw commit`, no new mechanism; D, the invariant "a release-blocking backlog item cannot close until its carrier ships" is checked by `evaluate_blocking_close` before and after and by the named release-gate test modules; E, exact commands are given; F, smallest change. Right-sizing: each E-item is one concern; E-05 spans 8 files but is one mechanical citation rewrite with one mapping and one V, so no split. Spec sync section is truthful (two record changes, no body text). The baseline path is PR-001; the missing module per-line check is PR-004; the stale `E-NEW` token is PR-006.

### Step S5

- Checked: OQ-01 (resolved, non-blocking). Its claim that a same-status write carries no `--by-human` attestation and leaves the 2026-11-02 approval intact was confirmed in the reproduction: the new line reads `approved (aw set): ...` without `--by-human`. No new question: every finding was fixed in place, and no decision belongs to the human. Decisions recorded below.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | medium | IN-SCOPE | G executability | plan E-01 "`/tmp/opencode/7ehv8l-check-before.jsonl`" | The baseline was written outside the workspace; a lane in this run refused a write to `/tmp/opencode` outside the lane, so a runner executor may be unable to save the baseline E-07 diffs against. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline moved to gitignored `.aw/state/7ehv8l/check-before.jsonl`; E-07 and V-01 name it. |
| PR-002 | medium | IN-SCOPE | G re-derivation convention | plan E-01 "`rg` lists 16 files"; V-01 "16-line"; V-05/V-06 "8 named" | Live citation counts were the success bar. A concurrent change adding or removing a `2vev8j` citation would make an honest execution fail V-01 or leave a citation unaddressed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 re-derives the list; E-05, E-06, V-05, V-06 use it; authoring counts stay as context. |
| PR-003 | low | IN-SCOPE | R1 references | `4sd62s` C3 "Two lanes that change DIFFERENT artifacts never write the same tracked file"; `4sd62s` P3 "(`2vev8j`, evidence E1 to E4)" | The E1 mapping pointed to requirement C3, but the module comments cite E1 as the MEASUREMENT that shared JSONL appends conflict. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Mapping adds P3 and says the rewrite cites where the evidence is recorded. The namespace-gate comment wording no longer implies `4sd62s` was the measured spec. |
| PR-004 | low | UNDER-SCOPE | G verification checklist | plan E-05 "every changed line is a comment, a docstring, or the one `recovery=` string"; V-05 | V-05 did not ask for evidence of E-05's comment-only outcome, while V-06 did for tests. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 demands `git diff -U0 -- agent_workflows` filtered to changed lines. |
| PR-005 | medium | UNDER-SCOPE | S7 execution contract | plan `## Approval and execution gate` | The gate lacked the honesty rule, the ban on `git add -A`/bare add/`-a`, the declaration wording with `--scope-reason`/`--scope-ack`, and the conditional finalize ownership (it instructed `aw ipd finalize 7ehv8l` unconditionally). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten; also notes the setter stages the `2vev8j` rename and that `aw commit` was measured to commit it. |
| PR-006 | low | IN-SCOPE | P proofread | plan F-05 "Scratch copy after E-NEW steps" | Stale placeholder token. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reads "after the E-02 to E-04 steps" with the review re-measurement. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep `- Blocks-Release: next` on superseded `2vev8j`? | Keep (plan as written) | Clear it with `--blocks-release -` | Review reproduction: `aw releases show next` drops `2vev8j` once superseded and `aw check release-gates` is clean; `releases.py::get_release_blockers` lists live items only | yes |
| D-2 | Split E-05 (8 modules) into smaller items? | No | One E-item per module | One mechanical rewrite with one mapping table and one verifiable outcome (`rg` empty plus per-line diff check) | yes |
| D-3 | Move the baseline out of `/tmp/opencode`? | Yes, to `.aw/state/7ehv8l/` | Keep `/tmp/opencode` | Lane write to `/tmp/opencode` outside the workspace was refused during this review; `.aw/.gitignore` ignores `/state/` | yes |
