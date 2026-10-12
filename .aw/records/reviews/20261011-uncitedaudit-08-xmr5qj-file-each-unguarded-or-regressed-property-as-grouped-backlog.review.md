# Review findings: plan xmr5qj

- Subject-Id: xmr5qj
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `9f8eb0db7`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent`: `clean` before review;
`--phase review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.
Upstream verdict sets were taken from the reviewed text of `8d0qsg`, `anzu8q` and `rq3q7v` (reviewed earlier in
this sweep, which added `stale-at-trim`, `replay-env-limited` precedence and the probe-verdict mapping).

Probes:
- `git diff --name-only 27ba5283c^..HEAD -- agent_workflows tests tools`: 6 files, all from `work(pua92o)` and `work(m47znv)`.
- `git log --name-only --format= -E --grep '^[a-z-]+(\(| )(pua92o|m47znv)\b' -- agent_workflows tests tools | sort -u`: exactly those 6 files, so subject attribution works; the same pattern over this Set's id6s returns 0 commits today (no Set code committed yet).
- `aw find backlog lost_guard_census` -> `no artifact matched selector`; `aw backlog new --summary x --work-kind chore` -> `--priority required`.
- `aw check --agent`: `findings 137`, exit 1; `aw backlog check`: exit 0.
- Release `f33nrj` 2.0.0 is the single `planned` release.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness (whole-Set check) | E-03 (e) original; F-04 probe | The `<Set base>..HEAD` range diff includes other Sets' concurrent code commits (6 files at review), so check (e) would fail on unrelated work; and `--grep 1ub8ex` matches only review commits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Attribute by commit subject (`<verb>(<id6>)`) over this Set's nine id6s; demonstrated on `pua92o`/`m47znv`. |
| PR-002 | HIGH | IN-SCOPE | A completeness (carrier set) | E-03 (d) and E-02 original; `8d0qsg` Scope verdicts; `anzu8q` `stale-at-trim`; `rq3q7v` `import-only` | (d)'s exclusion list was an incomplete negative list: `stale-at-trim` was unknown, `replay-env-limited`, `api-moved` and `import-only` had no stated disposition, `api-moved`-with-surviving-coverage and `pass-shared`-guarded are not verdicts any order produces, and E-02's rollup trigger omitted several carrier-needed outcomes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (d) now lists both sets explicitly over the verdicts the upstream plans actually emit; E-02's rollup trigger and Scope reference that set. Resolves `anzu8q` review PR-007's cross-reference. |
| PR-003 | MEDIUM | IN-SCOPE | G executability (dedupe) | F-05 probes | `aw find backlog <module>` is not a text search, so the primary dedupe step finds nothing; parked items and pending plans were not searched. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Dedupe is `grep -rlnwF` over open/graduated/blocked/parked backlog and pending plans, plus `aw backlog new`'s advisory dry-run report. |
| PR-004 | MEDIUM | IN-SCOPE | G executability (filing) | F-05 (`--priority required`) | E-02's command omitted the required `--priority`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `--priority` added, decided in E-01's filing plan. |
| PR-005 | MEDIUM | IN-SCOPE | C operability (checks / commit) | F-06; `.aw/.gitignore:50-51` | `aw check` and `aw research index --check` already fail at HEAD, so "conform" was unsatisfiable; committing whole directories could sweep in a co-worker's untracked backlog file; the index is gitignored. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 captures `aw check --agent` per-rule counts; E-04 compares; commit names exact files. |
| PR-006 | LOW | UNDER-SCOPE | G evidence | V-01 to V-03 original | V-items did not reconcile grouped outcomes against upstream counts or show which commits (e) attributed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 count reconciliation; V-03 per-verdict carrier table and the attributed subject list. |
| PR-007 | LOW | IN-SCOPE | Gate / OQ owner | Gate original; OQ-01 `Owner: none` | Gate lacked the paste-actual-output rule, fence wording and prerequisite; OQ owner `none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate itemized; owner `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to attribute code changes to this Set? | By commit subject `<verb>(<id6>)`. | Range diff, rejected (F-04); `AW-Item` trailers, rejected because `work(...)` commits do not carry them (checked on `work(lxb1ew)`). | F-04 probe. | yes |
| D-2 | Do `replay-env-limited` and `api-moved` need a carrier? | Yes, via the rollup. | Carrier-free, rejected: both leave a deleted test's behavior unverified, and the rollup is cheap. | `8d0qsg` Scope verdict definitions. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
