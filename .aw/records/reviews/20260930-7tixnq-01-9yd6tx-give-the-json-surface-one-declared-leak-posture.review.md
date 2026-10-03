# Review findings: plan 9yd6tx

- Subject-Id: 9yd6tx
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `aa905891d`. The plan file was committed and the tree
clean (`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE any edit;
`--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:` bullet
reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

I RE-DERIVED EVERY LOAD-BEARING MEASUREMENT INDEPENDENTLY rather than trusting the plan's findings,
and the plan's DIAGNOSIS is sound and is its real contribution:

- F-01 reproduces: the same `CommandResult` renders through `JsonRenderer().render` with the home path
  verbatim and raises `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field
  'next'` through `AgentRenderer().render`.
- F-02 reproduces EXACTLY as stated, which is the reframing that makes this plan small: measured over
  eleven channels, `to_dict` is clean for exactly `diagnostics[].location` and `changes[].path` (both
  `_schema.normalize_repo_path`) and LEAKS for `summary`, `diagnostics[].detail`, `diagnostics[].fix`,
  `changes[].detail`, `evidence[].value`, `evidence[].detail`, `next_actions[].command`,
  `next_actions[].description`, and `data`.
- F-05 reproduces: `aw context --json` emits 16 absolute paths, every one under `data`
  (`data.logical_roots.*`, `data.target_repo`, `data.effective_aw_home`,
  `data.permitted_commit_destinations.*`, `data.physical_classes.*`, `data.provenance.*.detail`), so
  blanket redaction would break approved spec `kw5y2s` Section 2.4. The `data` exemption is correct.
- F-06 reproduces on BOTH its independent reasons, and this is the finding that justifies a new
  primitive rather than reuse: `normalize_repo_path('aw foo /home/<user>/secret/x.md')` returns the
  string UNCHANGED (still matching `_HOME_PATH_RE`), and
  `normalize_repo_path('/home/<user>/code/other/.aw/records/a.md')` returns `'.aw/records/a.md'`, a
  repo-relative path that does not exist in this repo. `_rewrite_line` handles both correctly
  (`'aw foo ~/secret/x.md'`, `'~/code/other/.aw/records/a.md'`).
- F-08 reproduces: `'C:\Users\<user>\x'` passes through `_rewrite_line` unchanged and still matches both
  `_HOME_PATH_RE` and `_FAIL_PATTERNS['windows-home']`, because `_HOME_ANY_RE`/`_USERS_ANY_RE` cover only
  the two POSIX forms. So E-01 genuinely cannot delegate.
- F-11 and F-14 reproduce: no spec governs the `--json` payload shape, no `tests/test_renderers.py`
  exists, `JsonRenderer` appears in zero test files, and `tests/test_cli_conformance_matrix.py` is
  absent while `tests/conformance_matrix.py` declares a `"json"` scenario.
- F-12 reproduces verbatim: `docs/cli-output-contract.md` really does say "Both renderers expose
  identical facts ... with zero domain drift" one line after naming three renderers, and its
  Path Sanitization invariant really is written as a property of records generally.

What I found are six problems in HOW the plan executes that diagnosis, two of which are material.

PR-001 IS THE FINDING THAT CHANGED THE PLAN'S SCOPE, AND IT IS A DEFECT IN THE PRESCRIBED FIX RATHER
THAN A DOCUMENTATION GAP. `CommandResult.to_agent_record` assigns `rec["next"] =
self.next_actions[0].command`, reading the dataclass attribute DIRECTLY; `NextAction.to_dict` is called
from `CommandResult.to_dict` and from nowhere else. So E-04's redaction inside `NextAction.to_dict`
could not have reached the `next` field at all, and the plan's repeated claim that the change "also
hardens `--agent`" was false for precisely the channel the backlog item measured. Measured on the seam:
`NextAction.to_dict()` returns `{'command': 'aw x /home/<user>/secret/x.md'}` while `to_agent_record()`
RAISES on the same input. That matters far more than a missed field, because the unredacted `next` makes
a shipped command CRASH: `aw check plans --agent` exits 1 having written ZERO stdout bytes and a 26-line
stderr whose final line is `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in
field 'next': 'aw ipd lint /home/<user>/.../20260929-iguvci-...ipd.md --phase author'`. This also
FALSIFIES the plan's own F-10, which asserted "this plan must NOT claim to fix a live CLI crash" and
"the live, operator-visible defect is the `--json` leak in F-03": there IS a live CLI crash, it is on the
machine surface, and one line of the plan's own primitive fixes it. Note `aw check --agent` (unscoped)
does NOT crash, which is why the plan's own F-09/F-10 probes missed it. I added E-07 (apply the primitive
at the one `rec["next"]` assignment) with V-07 demanding before/after subprocess byte counts, corrected
F-09 and F-10 to name the exception, added F-16 and F-17, and swept the stale "hardens `--agent`" and
"no live CLI crash" claims out of the Goal, the Proposed changes, the Scope check and the Deferred row.

PR-002 IS AN UNACHIEVABLE VALIDATION DEMAND, which would have forced the executor either to fake
evidence or to stall. E-02 promised "a test that fails if a fourth home class is ever added to
`_HOME_PATH_RE` without teaching `redact_home_paths` about it", to be produced by asserting a
clean-and-idempotent property over a FIXED TABLE of inputs, and V-02 demanded a falsifiability
demonstration of exactly that. I implemented a plausible three-class `redact_home_paths` and ran the
described table against today's `_HOME_PATH_RE` (PASS, 0 failures) and against a detector extended with a
fourth alternation (`/export/home[0-9]/<user>`): also PASS, 0 failures, because no table row carries the
fourth class. A string of that class comes back untouched and still matches. The mechanism cannot deliver
the property. E-02 now asserts a PER-CLASS bijection over a shared class list (so a class the detector
gains but the primitive does not handle fails its own row), forbids reading `_HOME_PATH_RE.pattern` by
string inspection as a code-pinning test, and STATES the unenumerated-class bound rather than claiming to
close it; V-02 now demands the falsifiability demo that IS producible (break one enumerated class, show
its row fail by name).

PR-003: `Evidence.value` is typed `Any` and three shipped `cli.py` callers pass dicts
(`Evidence(key="repos", value={"count": len(repos)})`, `Evidence(key="currency", value=counts)`,
`Evidence(key="plans", value={"count": 0})`). E-03's "string values only" qualifier would therefore have
left dict- and list-valued home paths LEAKING while E-06's matrix, driven by a string fixture, declared
the `evidence.value` channel clean. Measured: both the dict and the list form carry the planted path
verbatim through `to_dict`. Added E-08 (container-aware redaction preserving the container type) and V-08
demanding the per-shape type-preservation evidence, plus F-19.

PR-004: the F-03 hit counts are LIVE-ARTIFACT figures stated as the validation bar. They had already
drifted in ONE DAY: the plan recorded 22 for `aw check --json` and 3 for `aw doctor --json` at authoring,
and I measured 16 envelope hits for the first (8 in `diagnostics[].fix`, 8 in `next_actions[].command`)
and 1 for the second. The population is the pending-plan set, which moves daily. Per the re-derivation
convention, Required tests and V-04 now hold the executor to the PROPERTY (nonzero before, zero envelope
after, both re-derived in the lane) and keep the numbers as context only.

PR-005: E-06's planted fixtures would have broken the commit. The repository's `local-leaks` pre-commit
hook scans TRACKED files, so a literal `/home/<name>/...` in the new test module is invisible to
`aw sanitize` while untracked (measured `clean`) and reports `home-path` the moment it is `git add`ed
(measured, exit 1, `tests/zz_probe_leak_tmp.py:1: home-path`). E-06 now mandates runtime fragment
assembly following the shipped convention in `tests/test_local_leaks.py`, V-06 demands a grep proving no
literal survives and that `aw sanitize --agent` is run AFTER staging, and F-20 records the mechanism.

PR-006: F-04 claimed "two implemented/approved specs already forbid an absolute home path in `--json`",
which overstates both citations and which OQ-01 leaned on to justify not asking the maintainer. F8a's
sentence is scoped to a LANE's worktree path ("may contain an ABSOLUTE filesystem path for a lane"), so
only its RATIONALE generalizes to the envelope; `uonrjg` A14 reads "`--agent` and `--json` output contains
no ANSI and no schema-breaking decorated status value", which is about ANSI and not about paths. The
posture decision is still right and the `data` exemption is still forced by `kw5y2s`, but it rests on
rationale plus the surface's contract status, not on a binding clause. Corrected F-04, OQ-01 and the
spec-sync section so a later reader does not propagate a citation that does not say what it was quoted
for.

The gate was also missing three Step 4 elements (an open-questions statement, a scope fence, and the
lifecycle transition with conditional runner/executor ownership) and was silent on the no-dash rule for
the two user-facing `docs/` files; all four were added in place as part of PR-001's revision pass rather
than filed as a separate finding, since none is a defect in the work the plan proposes.

TWO THINGS I DELIBERATELY DID NOT CHANGE. The `data` exemption is correct and E-06's assertion that
`data` STILL leaks is the right shape, because it converts a decision into a pinned test. And F-15's
no-collision analysis with `wqiofa` holds: the two plans touch disjoint regions of `agent_schema.py`,
and E-07 does not encroach on `wqiofa`'s subject, which is GUARDING the raise rather than removing one
class of input that triggers it. I widened the `un6ppd` Deferred row to say so explicitly.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G (executability) / D (invariants) | `agent_workflows/result_types.py` `CommandResult.to_agent_record`, the line `rec["next"] = self.next_actions[0].command` | `to_agent_record` reads `next_actions[0].command` off the dataclass and never calls `NextAction.to_dict`, so E-04 cannot reach the `next` channel; that unredacted string makes `aw check plans --agent` crash today with zero stdout and a `ValueError` traceback, which also falsifies the plan's own F-10 claim that no live CLI crash exists | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-07 (apply the primitive at the one `rec["next"]` site) and V-07 (before/after subprocess byte counts and exit codes); added F-16/F-17; corrected F-09, F-10, Goal, Proposed changes, Scope check and the `un6ppd` Deferred row |
| PR-002 | HIGH | IN-SCOPE | E (testing) / G (executability) | the plan's E-02 Expected outcome and V-02 Required evidence | E-02 promised a test that fails when a fourth home class is added to `_HOME_PATH_RE`, which its stated fixed-table mechanism provably cannot deliver (a three-class primitive passes the table unchanged against a four-class detector), so V-02's demanded falsifiability demonstration was unproducible | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now asserts a per-class bijection over a shared class list, forbids pattern string inspection as code-pinning, and states the unenumerated-class bound; V-02 demands the producible demo (break one enumerated class); added F-18 |
| PR-003 | MEDIUM | UNDER-SCOPE | B (privacy) / E (testing) | `agent_workflows/result_types.py` `Evidence.value: Any`; `agent_workflows/cli.py` `Evidence(key="repos", value={"count": len(repos)})` | E-03's "string values only" qualifier leaves dict- and list-valued home paths leaking while E-06's string-fixture matrix would declare the `evidence.value` channel clean | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-08 (container-aware, type-preserving redaction) and V-08 (per-shape type and no-leak evidence); added F-19; E-03 reworded so it does not narrow the field to `str` |
| PR-004 | MEDIUM | IN-SCOPE | G (live-artifact success criteria) | the plan's F-03 and its Required tests / V-04 bars | the 22 / 3 / 35 hit counts are live-artifact figures used as the validation bar, and had already drifted to 16 / 1 envelope hits one day later | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03, Required tests and V-04 now demand re-derivation in the execution lane and hold the executor to the property (nonzero before, zero envelope after), keeping the numbers as context |
| PR-005 | MEDIUM | UNDER-SCOPE | E (testing) / C (operability) | `.pre-commit-config.yaml` the `local-leaks` hook; `agent_workflows/leak_sanitizer.py` `_tracked_files`; `tests/test_local_leaks.py` `POSIX_HOME` | E-06's planted fixtures, written as literals, would be rejected by the repository's own `local-leaks` pre-commit hook the moment the new module is staged | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now mandates runtime fragment assembly following the shipped convention; V-06 demands a grep proving no literal survives and that `aw sanitize --agent` runs after staging; added F-20 |
| PR-006 | MEDIUM | IN-SCOPE | Step 1 (evidence accuracy) | `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` F8a; `.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md` A14 | F-04 and OQ-01 claim two specs "already forbid" an absolute home path in `--json`; F8a's prohibition is lane-scoped (only its rationale generalizes) and A14 is about ANSI and decorated status values, not paths | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04, OQ-01 and the spec-sync section now state each citation's actual scope and record the posture as a decision resting on rationale plus contract status rather than on a binding clause |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should fixing the `--agent` `next`-field crash be added to this plan, or filed as a separate carrier? | Added in-plan as E-07 | File it as a new backlog item and leave this plan `to_dict`-only; or hand it to `un6ppd`, which already owns the `AgentRenderer` raise | It is the SAME primitive at the same conceptual boundary and the same channel the carrier backlog item measured, so splitting it would leave the plan claiming "one declared posture" while a shipped command crashes on the exact string it redacts. It does not encroach on `un6ppd`, whose subject is GUARDING the raise, not removing one input class: `.aw/records/plans/pending/20260929-un6ppd-01-wqiofa-...ipd.md` Scope explicitly excludes `--json` and names `7tixnq` as this concern's carrier. Measured: `aw check plans --agent` exits 1 with zero stdout and a `ValueError` naming field `next` | yes |
| D-2 | E-02 cannot deliver the fourth-class drift guarantee it promised; weaken the claim, or escalate the primitive's drift risk to the maintainer? | Weaken the claim to a per-class bijection and record the unenumerated-class bound honestly | Leave V-02's demand standing and let the executor discover it; or escalate as a blocking question on whether the three regexes must first be unified (`ddhpcb`'s subject) | The plan already defers regex unification to carrier `ddhpcb` with a stated reason, so the drift hazard has an owner and does not need re-deciding here; and the achievable per-class property catches the realistic failure (a class the detector has that the primitive lacks). Demonstrated at review that the fixed-table mechanism passes identically against a three-class and a four-class detector | yes |
| D-3 | Does the `--json` envelope posture need a maintainer ruling, given PR-006 shows no spec directly binds it? | No; proceed with the split, recording the weaker basis explicitly | Raise a blocking open question asking the maintainer to rule on the envelope posture | The decision is REVERSIBLE in the plan's own terms (OQ-01 notes a disagreement is confined to E-05's wording and E-06's expectations, not the primitive), the direction is already the one the repository's rationale points at (F8a's "pasted into shared contexts"), the surface already normalizes two path fields so no consumer can depend on absolute envelope paths, and `aw attention` already honors the stricter posture. Blocking a plan on a ruling whose wrong answer costs a doc sentence would be disproportionate | yes |
