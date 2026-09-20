# Review findings: plan h5pyqa

- Subject-Id: h5pyqa
- Subject-Type: ipd
- Reviewed-At: 2026-09-20
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in worktree `.aw/worktrees/gatewire` at HEAD `0f3b88de`. The plan was already committed and
`git status --porcelain` was empty, so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent`: `conforming`, exit 0, BEFORE any revision.

DISCLOSURE, BECAUSE IT BEARS ON HOW MUCH THIS REVIEW IS WORTH: I authored this plan. A self-review
cannot supply the independence a second reviewer would, and the honest mitigation is to make the
findings mechanical rather than judgemental. Every claim below was re-derived by executing code or
reading it at a cited line, and the one HIGH finding was found by testing a regex against real pytest
output rather than by rereading my own prose. A human or a second agent should still read PR-001.

EVERY MECHANICAL CLAIM IN THE PLAN VERIFIED, and I checked each rather than trusting my own authorship:
the seam really is `runner_shared.py:13996`; `integration.earned` really gates self-finalize at BOTH
`:14120` (isolated lane) and `:14325` (non-isolated), so a fix on one alone would be a fix on neither;
`perform_defect_reask` really is called at `:13884`; `integration_is_earned`'s own comment really does
say "a green suite deliberately does NOT override an explicit verifier verdict" (`oc_runipd.py:4016`),
which is the basis for F-04; and `resolve_retry_budget(None)` really returns 2.

I ALSO CHECKED A SCOPE CLAIM THAT LOOKED WRONG AND WAS RIGHT. `integration_is_earned` is defined only
in `oc_runipd.py:3976`, yet the plan declares `agy_runipd.py` in `- Scope-Paths:`. That is correct:
`agy_runipd.py:461` re-exports the symbol and `execute_item_core` fetches it from the driver module
(`runner_shared.py:13103`), so the seam is genuinely shared and a one-host fix would be the
one-sided-guard defect class this repository has been bitten by before.

THE ONE SERIOUS FINDING IS THAT THE PLAN'S CENTRAL MECHANISM COULD NOT WORK AS WRITTEN. Its E-02 said
to build the question from "the failing-test text from `suite_result.summary`". `_SUITE_SUMMARY_RE`
(`oc_runipd.py:3845-3847`) captures ONLY the count line. Measured by running that exact regex over real
pytest output containing a `FAILED tests/...::test_name` line: it yields
`'1 failed, 7080 passed, 3 skipped, 2 xfailed in 98.49s'` and the FAILED line is absent. The full text
exists as `stdout_excerpt` (`oc_runipd.py:3907`) and is discarded after the regex, and
`attempt["suite_check"]` (`runner_shared.py:13987-13994`) persists only the summary. So the agent would
have been asked to attribute a failure it was never shown. "1 failed" is not evidence anyone can
attribute, and the whole design rests on the agent comparing the failing tests against its own changed
files. Split into a capture item (E-02) and the ask (E-07), with V-02 now demanding a real `FAILED
<nodeid>` line and explicitly failing a count-only field.

ONE GAP RECORDED RATHER THAN FIXED, and the reason is scope discipline. `needs-human` is semantically
the same "a human is required" condition that `NEEDS_INPUT_TOKEN` carries, and
`run_evidence.aggregate_run_exit` already maps that to spec `25kzda` 5.6's exit 3 and already outranks a
plain item failure. But `runner_shared.py:11267-11269` records that the aggregator has ZERO call sites
in either driver, so reaching exit 3 means wiring both drivers to it, which changes EVERY run's exit
classification and was already fenced out of an earlier Set. Half-wiring it inside a per-item feature
would smuggle a run-wide behavior change into an unrelated change. Left as a declined deferral with that
measurement, so a later reader does not mistake the omission for an oversight.

WHAT I DID NOT FIND, stated so the absence is not read as unexamined. The plan does not weaken
`integration_is_earned` (the gate stays hard; only an ANSWER can release). It does not add a retry knob
(E-04 uses the resolved `--retry-budget`). It correctly restricts the ask to the `suite-failed` signal,
so a verifier's explicit decline cannot be answered away by the agent it judged. Its F-03 names the
right thing as the item to scrutinize hardest, which is the one place a claim substitutes for a green
suite. And it composes correctly with the disk-only dependency fix (`8d5ccfb1`): a `not-mine` release
drives self-finalize, which moves the plan into `executed/`, which is what the dependency check now
reads.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | E. testing/verification; G. executability | `oc_runipd.py:3845-3847` (the regex), `:3907` (`stdout_excerpt` discarded), `runner_shared.py:13987-13994` (only `summary` persisted); measured: regex over real output yields the count line and drops every `FAILED <nodeid>` line | The plan's E-02 built the question from `suite_result.summary`, which contains ONLY a count line. The agent would be asked to attribute a failure it was never shown, and the entire design rests on it comparing failing tests against its own changed files. Unsatisfiable as written | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into E-02 (capture the failing-test lines into `SuiteCheckResult` and persist them) and E-07 (ask, using them). V-02 rewritten to demand a real `FAILED <nodeid>` line and to FAIL a count-only field; V-07 now owns the question evidence. E-03's dependency re-pointed to E-07 |
| PR-002 | MEDIUM | UNDER-SCOPE | C. architecture and operability | `runner_shared.py:11267-11269` (aggregator has zero driver call sites); `NEEDS_INPUT_TOKEN` maps to spec `25kzda` 5.6 exit 3 | `needs-human` is the same "a human is required" condition that already has an exit-3 mapping, and the plan said nothing about it, so a reader could not tell whether the omission was considered | C:Medium; U:Low; S:Low; F:Low; Overall:Medium | FIXED | Recorded as a declined deferral with the measurement: reaching exit 3 needs BOTH drivers wired to an aggregator neither calls, which changes every run's exit classification and was fenced out of an earlier Set. Deliberately not half-wired here |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should PR-001 be fixed by widening `suite_result.summary` to include the FAILED lines, or by adding a separate field? | A separate field, leaving `summary` as the count line | Widening `summary` in place. Rejected: `summary` is already persisted and read as a count line, and `run_suite_check`'s `reason` interpolates it into operator prose (`oc_runipd.py:3930`, `:3942`), so widening it would change existing output and could break a consumer that expects one line | `oc_runipd.py:3930` and `:3942` interpolate `summary` into a human sentence; `runner_shared.py:13991` persists it as one field | yes |
| D-2 | Does declaring `agy_runipd.py` in `- Scope-Paths:` overstate the change, given `integration_is_earned` is defined only in `oc_runipd.py`? | Keep it declared | Removing it as over-scope. Rejected on measurement: `agy_runipd.py:461` re-exports the symbol and `execute_item_core` resolves it off the driver module, so the agy path reaches the same seam and a one-host fix is the one-sided-guard defect class | `agy_runipd.py:461`; `runner_shared.py:13103` | yes |
| D-3 | Should this review fix the exit-code gap (PR-002) rather than record it? | Record it as a declined deferral | Fixing it here by wiring `aggregate_run_exit` into both drivers. Rejected: that changes EVERY run's exit classification, is far larger than the feature it would ride along with, and the same scope was already fenced out of an earlier Set at that code's own comment | `runner_shared.py:11267-11269` | yes |
| D-4 | OQ-01: where should a `needs-human` item appear in the run summary? | The existing `Diagnostics / Blocked Items:` block, as its own bullet naming the item and the requested decision | A new dedicated section, and a per-item table column. Both rejected: the existing block is already conditional (no spurious line on a clean run), already sits after the summary table where an operator looks for why an item did not finish, and adding a second location fragments the one place that is checked | `render_stream.py:2530-2533` | yes |
| D-5 | OQ-02: may a `not-mine` answer integrate in a fully unattended run? | Yes, unconditionally. Asked the maintainer rather than deciding: it is a risk-appetite judgement the repository cannot answer | Refuse unattended and record the request; require an opt-in flag following `--allow-uncovered-orchestrator-work`. Both rejected BY THE MAINTAINER on the measured cost: refusing unattended preserves the 2026-09-19 loss (three correct lanes refused, $55.02, nothing integrated) exactly where it hurts most | maintainer ruled 2026-09-20 in review; incident run `run-20260919T194413Z-2056285` | yes |
