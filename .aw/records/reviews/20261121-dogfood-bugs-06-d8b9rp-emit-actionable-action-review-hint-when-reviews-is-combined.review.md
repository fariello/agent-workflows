# Review findings: ipd d8b9rp

- Subject-Id: d8b9rp
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: opencode/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `34792ea0bcce89b5d82dbf628e0ada14c0e1ea77` plus local commit `ad7d776c9` (the `c74ey2` review, which touches no file this plan cites), in an isolated runner review-sweep lane worktree. The target plan `.aw/records/plans/pending/20261121-dogfood-bugs-06-d8b9rp-emit-actionable-action-review-hint-when-reviews-is-combined.ipd.md` was committed and clean at turn start (last changed in `6efa5700e`), so no pre-review snapshot commit was needed. It is Order 6 of Set `dogfood-bugs` (orchestrator `p2zmjs`), graduated from backlog `bqqhdu`, and carries `- Blocks-Release: next`. Before edits, `aw ipd lint --phase author --agent` returned `clean` (exit 0, 0 findings).

The central result: the plan put its fix in `describe_unresolved_plan_selector`, which the reported input does not reach in any repository whose plan filenames contain the token. The fix moves to one guard at the top of `runner_shared.expand_selectors`, which both hosts call.

AW-TIER: standard

### Step T

1. Yes, minor: a selector list that today resolves (by filename substring) or fails with a different message will now be refused with exit 2. No flag, schema, or spec text changes; spec `25kzda` 2.1 already says a new run takes exactly one selector.
2. No: the selector resolver guards no private data, commit, worktree, merge, or sandbox path. The guard refuses before any of those run.
3. No: four E-items, one function, one new test module, one changelog line.
4. Yes: `- Scope-Paths:` is present. Review added `CHANGELOG.md`.
5. Low: the guard only adds a refusal for inputs that are wrong today; single status selectors, named-only lists, and a Set literally named after a token are pinned unchanged by cases (f) to (h).

`AW-TIER: standard`

### Step R1

- Checked: `agent_workflows/runner_shared.py::expand_selectors` (18194; single-token `reviews` branch 18223, `all` branch 18250, per-name loop 18311, exact-Set step 18367, prefix step 18371, filename-substring step 18385-18399), `describe_unresolved_plan_selector` (18607), `STATUS_SELECTOR_TOKENS` (18756), `REVIEW_SELECTOR_TOKENS` (18760), `is_status_selector` (18763), `HostLabels` (37850; `command` and `review_command`), `OC_HOST_LABELS` / `AGY_HOST_LABELS` (37977, 37996), `enforce_requested_action` (39070), `initialize_run` selector expansion (40400); `agent_workflows/oc_runipd.py:1742` and `agent_workflows/agy_runipd.py:2050` (thin wrappers); `agent_workflows/cli.py::expand_host_review_argv` (21023); spec `25kzda` 2.1, 2.3, 2.4a; `tests/test_unresolved_selector_near_match.py`; `tests/test_reviews_type_noun_surface.py:184-220`; `tests/test_agy_runipd_cli.py:1964-1982`; `tests/test_runner_shared.py:58`; `CHANGELOG.md` `## 2.0.0 (pending)`. Every citation resolved.
- Found F1: the chosen fix site is reached only after filename-substring matching finds zero plans (18397). Measured at `34792ea0b`: `reviews` is a substring of 9 plan filenames, `review` of 89, `to-review` of 4, `all` of 141. Both hosts' `expand_selectors(manifest, ["reviews", "dogfood-bugs"], repo)` raised `Ambiguous filename selector: reviews matches multiple plans: ['p06t7i', 'd8b9rp', ...]`, as did `aw oc run --prepare-only reviews dogfood-bugs` and `aw agy run --prepare-only reviews dogfood-bugs` (exit 2 on both). The plan's E-01 would not have changed what an operator sees here. Fixed: the guard moves to the top of `expand_selectors`.
- Found F2: when exactly one plan filename contains the token, the run silently queues it. Probe on an in-memory manifest: `oc_runipd.expand_selectors(m, ["to-review", "perfopt"])` returned `['bbb222', 'aaa111']`, where `bbb222` is an unrelated plan named `...-to-review-cleanup.ipd.md`. The plan neither named nor tested this case. Fixed: E-02 case (b).

### Step R2

- Checked: the E/V bijection after revision (E-01..E-04 to V-01..V-04, `Highest E allocated: 04`), `Depends on` order, Scope-Paths completeness, and V-item evidence specificity.
- Found F3: the message text was unspecified ("clearly explains"), and the suggested `--action review <selector>` omitted the verb, which differs per host. The `HostLabels` descriptor already carries `command` and `review_command` for this, and `aw <host> review <selector>` is the spec 2.1 alias. Fixed: E-01 gives the exact message for each case and reads both fields from `labels`.
- Found F5: V-01 demanded a diff of the old function; V-02 lumped typecheck, sanitizer, and tests together; the test command had no `-o addopts=""` and so hid per-test lines; the new test module had no `core` marker, so the bare routine gate would skip it. Fixed: V-01..V-04 each name their units and fail conditions; Required tests uses precise commands; E-02 sets `pytestmark = pytest.mark.core`.
- Found F7: the plan did not say what happens when the status token is not first (`perfopt reviews`), when the case differs (`REVIEWS`), or when every selector is a status token (`reviews all`). Fixed: E-01 matches case-insensitively and position-independently and defines the all-status message; E-02 cases (a), (d), (e).

### Step R3

- Checked (short form): the guard compares strings from argv against a fixed token set and a manifest key set, then raises. It adds no I/O, subprocess, network, or credential handling, and it echoes only the operator's own selector strings. It refuses before any run directory, lease, or session exists.
- No security finding.

### Step R4

- Checked: correctness against spec `25kzda` 2.3 precedence (exact Set id before exact status token); the exit path (`DriverError` exits 2 with no run directory, observed; `EmptyStatusSelection` would exit 0 and must not be used); behavior of unchanged inputs (probes at HEAD: `["reviews"]` and `["all"]` return `['aaa111', 'bbb222']`, `["perfopt", "docs"]` returns `['aaa111', 'bbb222']` on both hosts, and with a Set named `reviews` holding `ccc333`, `["reviews", "perfopt"]` returns `['ccc333', 'aaa111']`); `expand_selectors` mutating the manifest (tests must pass a fresh copy); test cost (in-memory manifests plus two `--prepare-only` CLI calls).
- Found F4: a guard that refuses every status-token spelling in a list would break a Set literally named `reviews`, which spec 2.3 resolves as the Set. Fixed: the guard exempts exact `sets` keys, and case (h) pins it.
- Found F6: the change is user-visible (a different refusal, and a previously accepted wrong-plan input now refused), but the plan had no user-facing note. Fixed: E-04 adds one `- Fixed:` CHANGELOG bullet, and `CHANGELOG.md` joins Scope-Paths.
- Found F8: orchestrator `p2zmjs` names `describe_unresolved_plan_selector` as this child's fix site (E-06 expected outcome, child table row 06) and cites this plan's `V-02` for typecheck (now `V-04`). Outside this plan's Scope-Paths. Deferred to `p2zmjs` with a `Carrier:` line.

### Proofreading

Checked the plan against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Title, Short-Description | Emit a hint in the not-found message | Refuse the combination and name the correct command | F1 |
| Concern, Scope, Scope-Paths | One symptom; fix in `describe_unresolved_plan_selector`; no changelog | Three observed symptoms; guard in `expand_selectors`; `CHANGELOG.md` added | F1, F2, F6 |
| Goal and diagram | One sentence, no diagram | Outcome, definition of a status selector, spec rule, and a flowchart of the guard and today's fall-through | F1; requirement 12 |
| E-01 | Branch in the not-found function; unspecified text | Guard placement, exemption, error class, and exact messages from `labels` | F1, F3, F4, F7 |
| E-02 | Five selector lists | Cases (a) to (h) over both hosts, with expected return values | F2, F4, F7 |
| New E-03, E-04 | Absent | CLI test per host; CHANGELOG bullet | F5, F6 |
| Step 0 | Two bullets, one of them leading to the wrong site | Measured resolution order, alias definition, spec precedence, exit path | F1, F3, F4 |
| Deferred | One declined carrier | Three declined items and the `p2zmjs` carrier | F8 |
| Scope check, Required tests, Spec sync | "none" claims; imprecise commands; "N/A" | Accurate scope; precise commands; spec 2.1 rationale and changelog note | F5, F6 |
| V-01..V-04 | Diff of the wrong function; lumped evidence | Per-item units and fail conditions | F5 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |

### Step S5

- Checked: the plan has no open questions. The judgement calls are recorded in Decisions D1 to D4 and are reversible. The mechanism (a membership test before the existing branches) is simple; its outcome on concrete inputs is what E-02 cases (a) to (h) check, and the unchanged-input half of those cases was demonstrated by probe at HEAD. Nothing needs a human answer before approval.

### Pass 2

- Re-read the revised plan end to end. The guard rule (more than one selector, a status token by case-insensitive match, not an exact Set id) reads the same in the diagram, E-01, Step 0, and V-01. The case letters match between E-02 and V-02. `aw ipd lint --phase review-finalize --agent` returned `clean` (exit 0, 0 findings).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | HIGH | IN-SCOPE | R1 / Wrong fix site | agent_workflows/runner_shared.py:18385-18399; `aw oc run --prepare-only reviews dogfood-bugs` printed `Ambiguous filename selector: reviews matches multiple plans` (exit 2) | `describe_unresolved_plan_selector` is not reached when any plan filename contains the token, so the planned fix would not change what the operator sees. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Guard at the top of `expand_selectors`. |
| F2 | HIGH | UNDER-SCOPE | R1 / Silent wrong result | probe: `expand_selectors(m, ["to-review", "perfopt"])` returned `['bbb222', 'aaa111']` | One substring match queues an unrelated plan without any error. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Guard refuses it; E-02 case (b). |
| F3 | MEDIUM | IN-SCOPE | R2 / Message contract | agent_workflows/runner_shared.py:37850 `HostLabels.review_command`; agent_workflows/cli.py:21023 | The message was unspecified and the suggested command had no host verb. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Exact messages from `labels.command` and `labels.review_command`. |
| F4 | MEDIUM | IN-SCOPE | R4 / Spec precedence | spec 25kzda 2.3 step 3; probe with Set `reviews` returned `['ccc333', 'aaa111']` | A blanket guard would break a Set literally named after a token. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Exempt exact Set ids; case (h). |
| F5 | LOW | IN-SCOPE | R2 / Evidence and tier | plan V-01, V-02, Required tests; tests/test_runner_shared.py:58 | V-items demanded a diff of the wrong function and lumped evidence; the new module would be skipped by the bare gate. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | Per-item V-evidence, precise commands, `core` marker. |
| F6 | LOW | UNDER-SCOPE | R4 / Docs | CHANGELOG.md `## 2.0.0 (pending)` | A user-visible change had no user-facing note. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-04 bullet; `CHANGELOG.md` in Scope-Paths. |
| F7 | LOW | IN-SCOPE | R2 / Edge cases | plan E-01, E-02 | Token position, letter case, and all-status lists were unspecified. | C:Low;U:Low;S:Low;F:Low;Overall:Low | FIXED | E-01 rules; cases (a), (d), (e). |
| F8 | LOW | OUT-OF-SCOPE | R4 / Cross-plan consistency | p2zmjs E-06 expected outcome, child table row 06, line 104 | The orchestrator names the old fix site and V-item. | C:Low;U:Low;S:Low;F:Low;Overall:Low | DEFERRED | Carrier `p2zmjs` recorded in the plan's Deferred section. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | --- | --- | --- | --- | --- |
| D1 | Where does the fix go? | One guard at the top of `runner_shared.expand_selectors` | Branch in `describe_unresolved_plan_selector` (original plan); a check in each host's argv parsing | Only the top of the shared function sees every list before substring matching, and it already receives `labels` | yes |
| D2 | What about a Set literally named `reviews`? | Exempt exact `sets` keys | Refuse it too | Spec 25kzda 2.3 puts exact Set id before exact status token | yes |
| D3 | Which error and exit code? | `DriverError`, exit 2, before any run directory | `EmptyStatusSelection` (exit 0) | Spec 2.3: zero or invalid matches exit 2; exit 0 is reserved for an empty lone `reviews` | yes |
| D4 | Enforce spec 2.1's one-selector rule for named selectors too? | No; status tokens only | Refuse every multi-selector run | Multi-name runs work and are used; changing that is a contract decision outside this bug | yes |
