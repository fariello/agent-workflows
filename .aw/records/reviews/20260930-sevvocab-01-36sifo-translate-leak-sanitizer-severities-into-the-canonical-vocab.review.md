# Review findings: plan 36sifo

- Subject-Id: 36sifo
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-101 (HIGH, fixed), PR-102 (MEDIUM, fixed), PR-103 (LOW, fixed), PR-104 (MEDIUM, fixed), PR-105 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `37b80807c`. The plan file was committed and the tree was
clean (`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review; `--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:`
bullet reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

THE DEFECT IS REAL, REPRODUCES END TO END, AND THE PLAN'S DIAGNOSIS IS CORRECT IN EVERY PARTICULAR I
could check. I built a git fixture OUTSIDE this checkout with one committed home-style path and drove
the real CLI:

- F-01 reproduces verbatim. `aw doctor --dir <fixture> --json` emits
  `data.report.sanitizer.findings[0].severity == "fail"` while the SAME document's
  `diagnostics[]` entry for `doctor.leak-home-path` emits `severity == "error"`. The raw token is also
  in that diagnostic's `detail` (`fail: P = "<a home-style path>"`) and in the sanitizer drift's `detail`. Under
  `NO_COLOR=1` the human line reads `- leak.py:1: home-path (fail: P = "<a home-style path>")`. Both runs exit 1.
- The three-site census is exactly right and complete. `grep -n severity agent_workflows/doctor.py`
  returns exactly three sites that forward or interpolate a sanitizer severity: `to_dict`'s
  `getattr(f, "severity", "error")`, `probe_sanitizer`'s `f"{f.severity}: {f.snippet[:120]}"`, and
  `render_human_report`'s per-finding line. Nothing is missed.
- F-07 reproduces, and it is the plan's most valuable finding. Measured directly:
  `error -> 1`, `warning -> 1`, `"" -> 1`, `info -> 0`. So `warn -> warning` is exit-neutral and
  `warn -> info` would silently stop a leak finding failing `aw doctor`. I also confirmed
  `core.drift_exit_code(report.all_drift)` really is what produces doctor's exit code, so the gate
  interaction is live and not theoretical.
- F-03, F-04, F-05 reproduce: `Finding.severity` is declared `severity: str  # "fail" | "warn"`, the
  module docstring builds its contract on both tokens, `leak_sanitizer`'s own `CommandResult` branch
  writes `severity="error" if f.severity == "fail" else "warning"` (the authority E-02 reuses), and
  both other consumers (`security_hardening.check_evidence_redaction`, documented in `host_runner`)
  compare against `"fail"` as control flow and render nothing.
- F-06 reproduces: the string `severity` appears ZERO times in `tests/test_doctor.py`, which is the
  only module touching `probe_sanitizer`/`SanitizerProbeResult`. Nothing pins any of the three sites.
- F-08 reproduces and is a genuinely good catch: `term.ROLE_COLOR_256` maps `fail -> 196` and
  `error -> 196`, `warn -> 226` and `warning -> 226`, so the wrong token renders in exactly the right
  color and the bug is invisible to the eye.
- F-09 reproduces: `nwcf8j` is in `pending/` with `- Status: approved`, declares `doctor.py` in its
  `- Scope-Paths:`, and does extract a shared classifier in `render_human_report`.

SO THE FIVE FINDINGS ARE ABOUT ONE ITEM'S JUSTIFICATION, TWO MEASUREMENTS, AND TWO EXECUTION HAZARDS,
not about the plan's approach, which is sound and correctly narrow.

PR-101 IS THE SUBSTANTIVE ONE AND IT HAS TWO HALVES. E-03's stated rationale was that populating
`Drift.severity` is "the difference between a payload that merely LOOKS right and a drift object that
CARRIES its severity for any consumer that reads the field". There is no such consumer on this path. I
applied E-03 ALONE (constructing the Drift with `severity="error"`, detail text untouched) and the
`--json` payload came back byte-unchanged: the sibling diagnostic still read `error`, the sanitizer
finding still read `fail`, and the serialized drift still carried exactly `location`/`rule`/`detail`.
The reason is that `SanitizerProbeResult.to_dict`'s drift serializer OMITS severity, and doctor's
machine `Diagnostic` is built with a HARDCODED `severity="error"` literal rather than a read of the
drift. The probe was reverted and `git diff --stat` confirmed empty. E-03 is still worth keeping (it
stops the drift asserting the legacy empty severity and makes its `drift_exit_code` contribution
honest rather than accidental) but its claim had to be corrected, and V-03 now requires the executor to
STATE that no other output moves, so a byte-unchanged payload reads as success rather than as a failed
fix. The second half is that doctor's hardcoded literal is itself a live defect of the same class,
`nwcf8j` fixes the TWIN in `attention.py` and not this one, so it survives both plans. That is now
F-10 with a REQUIRED carrier: a plan reaching `executed` classes `done` in `aw attention`, so an
obligation living only in this plan's prose would vanish.

PR-104 is the same hazard in the other direction: E-03 cannot be implemented the obvious way at all.
`core.Drift` is an immutable `NamedTuple`, so `setattr(d, "severity", "error")` raises
`AttributeError: can't set attribute`, and `severity` is its NINTH positional field, so a fourth
positional argument silently populates `observed`. I know because I made that exact error while
verifying F-07 and briefly measured `info -> 1`, which would have falsified the plan's central safety
claim. Passing the keyword correctly gives `info -> 0`. Recorded as F-11 so the executor does not
repeat it, since the wrong version fails SILENTLY (it writes a real field, just not the one intended).

PR-102: F-02's structural conclusion is right and its number is not. The load-bearing fact is that
`include_warn=False` compiles ZERO warn rules, which I confirmed and which is structural (the
`if include_warn or hostname_fail:` block is the only writer of `rs.warn`). But the row cited
"8 fail / 29 warn when `include_warn=True`", and the warn rules are DERIVED PER REPOSITORY AND PER
MACHINE by `derive_warn_tokens(repo_root)`: measured here as 3, all `derived:` tokens for this
environment. A test or a re-derivation keyed on any warn count would be flaky across checkouts, so
E-04 now explicitly forbids asserting one.

PR-105: V-04 told the executor to "stash or revert the `doctor.py` change" to take the red state. A
bare `git stash` is repository-wide, not path-scoped, so in this shared checkout it sweeps a
co-worker's unrelated uncommitted work onto the stash stack. That is not hypothetical here: the stash
list in this very lane contains an entry labelled "pre-existing WIP popped in error by plan-review",
i.e. the accident has already happened once. V-04 now prescribes taking the red state BEFORE applying
E-02 (write the test first, run it against untouched code), with path-scoped fallbacks and an explicit
prohibition on bare `git stash`. The dependency plan `nwcf8j` independently states the same preference.

PR-103 is minor: V-01 attributed the in-tree-fixture trap to "F-02's sibling trap", but F-02 is about
warn-rule reachability and the trap is recorded in E-01 and belongs to `nwcf8j`. Corrected, and I
added the confirmation that the stop condition is actually satisfiable, since I reproduced every value
V-01 demands from an out-of-tree fixture.

WHAT I DID NOT WEAKEN. The approach is right and I left it alone: translating at the consumer rather
than renaming the sanitizer's vocabulary is correct, well-evidenced in F-03 through F-05, and is the
item's own fix sketch. The refusal to map `warn -> info` is the single most valuable thing in this plan
and I strengthened its evidence rather than trimming it. The honest-limits note was already unusually
candid (it volunteered that the `warn` half is seam-proven rather than end-to-end) and I added a fourth
limit rather than removing any. E-04's prohibition on reading production source is correct and its
prescribed idioms all exist (`tests.support.init_repo`, `run_cli`, `doctor --dir`). OQ-01 is resolved
on sound reasoning and correctly marked non-blocking.

ONE INCIDENTAL CONFIRMATION, recorded rather than filed: E-04's `warn` seam works as described. Patching
`leak_sanitizer.scan_working_tree_counted` to return a single `Finding(location=..., rule=...,
severity="warn", snippet=...)` and calling the real `doctor.probe_sanitizer` produced drift detail
`'warn: tok'` and a `to_dict` severity of `'warn'`, so it reproduces the raw token on both surfaces the
fix must clean. `Finding`'s signature is `(location, rule, severity, snippet)` with no defaults; added
to E-04 so the executor does not guess it.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | IN-SCOPE | A. Correctness / G. Plan executability (an item justified by a consumer that does not exist, plus an unfixed live defect with no carrier) | `SanitizerProbeResult.to_dict`'s drift serializer emits `{"location", "rule", "detail"}` only; doctor's `Diagnostic` is built with a literal `severity="error"`. Applying E-03 alone left `aw doctor --json` byte-unchanged (sibling diagnostic `error`, sanitizer finding `fail`, drift keys three). `nwcf8j` E-03 fixes the `attention.py` twin, not doctor's | **E-03's rationale is false: no consumer reads `Drift.severity` on this path, so the item changes nothing observable.** An executor told it is "the difference between a payload that merely LOOKS right and one that CARRIES its severity" would reasonably conclude the fix failed when the payload came back identical. Worse, doctor's hardcoded `severity="error"` is a live defect of the SAME class that neither this plan nor its dependency fixes, and it lived only in review prose | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03's justification corrected to forward-looking hygiene with an explicit "changes no observable output today"; V-03 requires the executor to STATE that, so a byte-unchanged payload reads as success. New F-10 records doctor's hardcoded literal with a **Carrier-Required** row (file `aw backlog new`, `- Work-Kind: bug`, `- Blocks-Release: next`, cite the id6 in V-02), and the Scope check declares the expected out-of-fence `.aw/records/backlog/` write. Goal/honest-limits/gate all updated so no section still claims the machine diagnostic severity becomes truthful |
| PR-102 | MEDIUM | IN-SCOPE | A. Correctness (a measurement presented as a code fact is environment-derived) | `build_ruleset`'s `if include_warn or hostname_fail:` block is the only writer of `rs.warn`, and it populates from `derive_warn_tokens(repo_root)`. Measured at review: `include_warn=False` -> `fail=8 warn=0`; `include_warn=True` -> `fail=8 warn=3`, the three being `derived:<environment-token>`-style entries | **F-02 cited "8 fail / 29 warn", but the warn rules are derived PER REPOSITORY AND PER MACHINE, so no warn count is a stable fact.** The ZERO under the default is the load-bearing claim and is structural; the 29 is not reproducible and a test or re-derivation keyed on it would be flaky across checkouts | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 rewritten: the zero is identified as the structural load-bearing fact with the reason, the authoring figure is marked corrected with the review measurement, and the row states not to treat any warn count as a regression signal. E-04 gains an explicit prohibition on asserting a warn-rule count, with flakiness as the reason |
| PR-103 | LOW | IN-SCOPE | G. Plan executability (a stale cross-reference in a FAIL condition) | V-01 said "F-02's sibling trap shows an in-tree fixture can answer about the live repository". F-02 is about warn-rule reachability; the trap is recorded in E-01 and belongs to `nwcf8j`'s `_resolve_runs_repo_root` measurement | **A FAIL condition pointed at a finding that does not support it,** so a validator checking the citation would find nothing about fixtures and could reasonably discount the condition | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now cites E-01's recorded trap and names the mechanism (`_resolve_runs_repo_root` walking parents) instead of F-02, and adds the review confirmation that an out-of-tree fixture reproduces every value the item demands, so the stop condition is satisfiable rather than aspirational |
| PR-104 | MEDIUM | IN-SCOPE | A. Correctness (the prescribed implementation cannot work, and the wrong version fails silently) | `core.Drift` is a `NamedTuple`: `setattr(d, "severity", "error")` raises `AttributeError: can't set attribute`. Its fields are `location, rule, detail, observed, required, recovery, assurance, determinism, severity`, so `severity` is NINTH. A reviewer's fourth-positional error measured `info -> 1`; the keyword form gives `info -> 0` | **E-03 said to "set the `Drift.severity` field", which is impossible on an immutable tuple, and the near-miss (a fourth positional argument) silently populates `observed` instead.** The silent variant is the dangerous one: it writes a real field, so nothing raises, and F-07's central safety claim would appear to be falsified | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now mandates `severity=` as a KEYWORD on construction, names the immutability and the ninth-field position, and records the measured near-miss. New F-11 carries the evidence; V-03 requires quoting the constructed `Drift` to show the keyword |
| PR-105 | MEDIUM | IN-SCOPE | B. Security / C. Operability (a validation instruction that can destroy a co-worker's uncommitted work) | V-04 said "stash or revert the `doctor.py` change". `git stash` is repository-wide, not path-scoped. `git stash list` in this lane contains an entry labelled "pre-existing WIP popped in error by plan-review", so the accident is recorded as having already happened | **A validation step instructed a bare `git stash` in a shared checkout, which sweeps another party's unrelated uncommitted work onto the stash stack**, and a mistaken `pop` then restores it into the executor's tree. AGENTS.md forbids touching a co-worker's uncommitted work, and the dependency plan `nwcf8j` already prefers the before-the-fact ordering for this reason | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | V-04 now prescribes taking the red state BEFORE applying E-02 (write the test, run it against untouched code, then fix), gives path-scoped fallbacks (`git stash push -- <path>`, or diff-then-checkout with a `git diff --stat` confirmation), and explicitly prohibits a bare `git stash` with the shared-checkout reason stated |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-101: E-03 changes nothing observable. Drop it, keep it with a corrected justification, or widen the plan to fix doctor's hardcoded `severity="error"` so E-03 becomes visible? | KEEP E-03 with a corrected justification, and file the hardcoded literal as a required carrier | (a) Drop E-03 entirely as a no-op; (b) widen scope to fix doctor's hardcoded literal in this plan, which would make E-03's field read by a real consumer and turn it into a visible fix; (c) keep E-03 and leave its justification as written | Option (b) is the tempting one and I rejected it on blast radius and on sequencing: the literal governs EVERY doctor drift rule, not just the sanitizer's, so changing it alters reported severity across git, naming and version findings too; `nwcf8j` F-10 already measured that the correct read is `check_engine.enrich_drift(d).severity or "error"` rather than a bare `d.severity or "error"`, so the fix depends on that plan's groundwork; and `nwcf8j` is editing the same file, so adding a third region here maximizes collision on the one file both plans touch. Option (a) throws away a real improvement: an empty `severity` is a legacy shape that happens to produce the right exit code, and leaving it empty keeps the correct gate decision ACCIDENTAL. Option (c) is the finding. Keeping the item while correcting its claim preserves the hygiene and removes the false premise, and the carrier is what keeps the discovered defect alive after this plan goes terminal | yes |
| D-2 | PR-101: should the F-10 carrier be `Carrier-Required` (filed before finalize) or `Carrier-Declined` with the reasoning recorded? | `Carrier-Required`, with `- Work-Kind: bug` and `- Blocks-Release: next` | (a) `Carrier-Declined`, on the argument that `nwcf8j` is already in the severity-truth area and could absorb it; (b) file it as `chore`; (c) leave it as a Findings row with no carrier | Option (a) misreads the dependency: `nwcf8j` is `approved` and its scope is fixed at the two `attention.py` sites, so "it could absorb it" is a hope about a plan already past review, not a carrier. Option (b) is wrong under this repository's own rule: a machine consumer receiving a constant severity for every finding is a correctness defect on a surface other tooling reads, and the gating set is `bug`, so filing it `chore` would also dodge the release gate. Option (c) is exactly the failure mode the carrier rule exists for, and the plan-review workflow's own PR-905 precedent (plan `z3si7r`) treats an obligation living only in plan prose as a finding. I chose Required over merely recommended because this plan is expected to execute soon and the obligation would otherwise die with it | yes |
| D-3 | PR-102: F-02's warn count is wrong. Correct the number, or remove counts from the row? | Keep the ZERO as the load-bearing structural fact, report the measured 3 as environment-derived, and forbid asserting any warn count | (a) Simply replace 29 with 3; (b) delete all counts from F-02 | Option (a) reproduces the defect in a new disguise: 3 is this machine's number, derived from this checkout's git identity and hostname, so writing it as a code fact invites the next reader to treat a different value as a regression. The honest shape is to distinguish the STRUCTURAL zero (which follows from `rs.warn` having exactly one writer, guarded by `include_warn or hostname_fail`) from the DERIVED nonzero (which is environment state). Option (b) loses the zero, which is the entire reason E-04 needs a seam at all. Keeping both with their epistemic status labelled is what lets E-04's prohibition be justified rather than arbitrary | yes |
| D-4 | PR-105: how should the executor take the pre-fix red state in a shared checkout? | Write the test FIRST and run it before applying E-02; path-scoped fallbacks only | (a) Keep "stash or revert" but add a warning; (b) mandate `git stash push -- agent_workflows/doctor.py` as the primary route; (c) require a scratch clone | Option (a) leaves the dangerous verb as a sanctioned route, and the measured history in this lane's own stash list shows a warning is not sufficient. Option (b) is safe but needlessly fragile: it still mutates the working tree between two states and still requires the executor to remember to restore, which is the step that failed before. Writing the test first is strictly better because the red state is simply the state the repository is ALREADY in, so there is nothing to save or restore and nothing of a co-worker's to touch; `nwcf8j` independently reached the same preference. Option (c) is disproportionate for one file and would complicate the `--dir` fixture work. Path-scoped forms are retained as fallbacks because an executor who discovers the need for a red state after the fact needs a safe route, not a prohibition with no alternative | yes |
