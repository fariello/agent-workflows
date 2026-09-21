# Review: enforce setid length bounds and dynamic cutover, child x75obw (Set setidlen)

- Subject-Id: x75obw
- Subject-Type: ipd
- Reviewed-At: 2026-09-21
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed in an isolated lane worktree at HEAD `cd2e6adb`. `aw ipd lint --phase author` CONFORMING
before semantic review; after revision it reports exactly one `IPD-Q501`, which is the newly raised
blocking OQ-03 firing as designed and is NOT a structural defect.

NOT A SELF-REVIEW: this plan was authored by `antigravity`, so nothing here rests on my own prior
reasoning. Its evidence was nonetheless verified by RUNNING rather than reading: the setid audit was
re-derived from the corpus, the cutover stamper was exercised against a scratch `project.json`, the
five `--set`-taking verbs were probed via `--help`, the managed-block boundary in `AGENTS.md` was
computed, and both the four named test files and the full suite were run.

THE GOAL IS SOUND AND THE CENTRAL AUDIT REPRODUCES. The setid group in BOTH naming regexes is
genuinely unbounded (`(?P<set>[a-z0-9-]+?)` at `artifact_naming.py:111` and `:119`), so the gap is
real. Re-measured: 662 unique declared setids, 626 at <= 14, **36** at 15-24, **0** over 24. The two
figures that carry the argument (36 and 0) match the plan EXACTLY; only the corpus totals moved from
its 597/561, which is ordinary drift rather than an error, though those totals must not be quoted as
current. The plan's decision to keep length OUT of the regex is also right, and better-supported than
it argued: the unbounded group appears TWICE, so a regex-level limit would have to be added in two
places and could not express a warn tier at all.

THE MOST CONSEQUENTIAL FACT IN THE PLAN WAS UNSTATED, AND IT IS A SAFETY PROPERTY. The `> 24` error
threshold has ZERO MARGIN: the longest setid in the repository is `research-prompt-pipeline` at
EXACTLY 24 characters. So "0 setids > 24" is not headroom, it is a boundary touching live data. An
off-by-one in the comparison converts a real committed record into a hard `error`, and the plan's own
proposed test ("post-cutover record with 26-char setid produces the error") would PASS while that bug
shipped. The boundary must be pinned at 24-conforms and 25-errors.

THREE FINDINGS WOULD HAVE PRODUCED DUPLICATED OR MISPLACED CODE RATHER THAN A FAILURE, which is the
harder class to catch later. E-02's ENTIRE install-side deliverable already exists: dependency `ogs6a2`
shipped `sync_cutovers_on_install`, it is already wired at `engine.py:6566` and
`install_wizard.py:921`, and it is GENERIC over `config.KNOWN_FEATURE_CUTOVERS`. I proved the reduction
by adding `setid_length` to that dict in-process and running the stamper against a scratch
`project.json`: it wrote `"setid_length": "2026-09-21"`, left the pre-existing `spec_id6: 2026-08-29`
untouched, and `resolve_cutover_date(..., "setid_length")` then returned `20260921`. So E-02 is one
registry entry, and following the plan literally would have added a second call site that double-writes.
E-01 likewise proposed a second cutover reader and a second stamper beside the shipped generic ones,
and offered two config keys as if interchangeable when only `cutovers.setid_length` is resolvable by
the shipped resolver. E-03 proposed carrying the new rules under `I-16`, which is ALREADY taken by
`check.setid-collision` and defined normatively as setid SEMANTICS, a sentence that says nothing about
length.

THE BLOCKING QUESTION IS NOT A PLAN DEFECT. OQ-03 is a genuine conflict between the maintainer directive
this plan records ("the cutover date must not be a hardcoded calendar date in the Python source code")
and the mechanism the plan's own dependency shipped (`KNOWN_FEATURE_CUTOVERS` maps each feature to a
hardcoded introduction date, consumed to locate the first install at/after it). Registering
`setid_length` writes one calendar date into source. That is either within the directive (the
ENFORCEMENT boundary still comes from `project.json`) or outside it, and only the maintainer can say
which reading governs, because E-02's whole content changes with the answer. Three options and a
recommendation are recorded in the question. Had OQ-03 not existed, the verdict would have been APPROVE
WITH REVISIONS APPLIED and the readiness `go-pending-approval`.

SCOPE: only this plan was a candidate. Read as evidence: `agent_workflows/config.py`
(`KNOWN_FEATURE_CUTOVERS` `:1141`, `_find_install_history_cutover` `:1162`, `resolve_cutover_date`
`:1204`, `sync_cutovers_on_install` `:1256`, `read_dependency_schema_cutover` `:1325`),
`agent_workflows/check_engine.py` (`SPEC_ID6_CUTOVER_DATE` `:40`, `RULE_REGISTRY` setid entry
`:100-102`, `check_collisions` `:1029`, `CARRIER_CUTOVER_DATE` `:4686`),
`agent_workflows/artifact_naming.py:110-121`, `agent_workflows/ipd_lint.py` (codes `:48-60`, the
suppression precedent `:830-845`, `LintResult` `:1259-1262`, aggregation `:1314`),
`agent_workflows/specs.py:988,1018`, `agent_workflows/ipd_authoring.py:336`,
`agent_workflows/research_cmd.py:641`, `agent_workflows/engine.py:6566`,
`agent_workflows/install_wizard.py:921`, `.aw/config/project.json`, `AGENTS.md` (`:26`, `:109`, `:118`),
executed plan `ogs6a2`, specs `pqsx96` (`:144`, `:182-200`), `2lcqno`, `20260817-2147-01`,
`20260802-1904-01`, and `tests/test_config.py`, `tests/test_check_engine.py`, `tests/test_ipd_lint.py`,
`tests/test_awnaming_grammar_and_producers.py`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | HIGH | UNDER-SCOPE | A. Correctness / E. Testing | measured corpus | THE `> 24` THRESHOLD HAS ZERO MARGIN: the longest real setid is `research-prompt-pipeline` at EXACTLY 24. An off-by-one (`>=`) hard-fails a committed record, and the plan's proposed 26-char test would pass while that bug shipped. The plan never states this. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as a Findings entry with both consequences; validation now MANDATES pinning the boundary at 24-conforms / 25-errors and says a 26-only test does not cover it. |
| PR-402 | HIGH | IN-SCOPE | C. Architecture | `engine.py:6566`; `install_wizard.py:921`; `config.py:1256` | E-02's entire deliverable ALREADY EXISTS and is generic. Following the item literally adds a second call site that double-writes `project.json`. Proven by running the existing stamper with `setid_length` registered: it stamped correctly and preserved the existing date. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 rescoped to a single `KNOWN_FEATURE_CUTOVERS` registration, with the measured proof inline and an explicit note that `engine.py`/`install_wizard.py` may legitimately go unmodified and need a `--scope-ack`. |
| PR-403 | HIGH | IN-SCOPE | C. Architecture / F. Principles | `config.py:1141-1167` | The maintainer directive forbids a hardcoded calendar date in Python, but the shipped stamper only covers features listed in `KNOWN_FEATURE_CUTOVERS`, every entry of which IS a hardcoded date. Registering `setid_length` therefore writes a date into source. Not resolvable from the repository: it is a reading of the maintainer's own instruction. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | OPEN | ESCALATED as OQ-03 with `- Blocking: yes` and `- Finding: PR-403`, carrying three options ((a) register anyway, (b) extend the stamper to skip the history search for date-free features, (c) defer the error tier) and a recommendation of (a). Blocks execution by design; `aw ipd lint` now refuses the plan until answered. |
| PR-404 | HIGH | IN-SCOPE | C. Architecture | `config.py:1204,1256` | E-01 proposed a SECOND cutover reader and a SECOND stamper beside the shipped generic ones, and offered `setids.cutover_date` OR `cutovers.setid_length` as equivalents when only the latter is resolvable by the shipped resolver. Two writers to one JSON file is how they drift. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 narrowed to the thresholds plus `ProjectPolicySchema`, delegating the cutover read to `resolve_cutover_date`; the proposed `stamp_setid_cutover_if_missing` is DROPPED and the key is fixed at `cutovers.setid_length`. |
| PR-405 | HIGH | UNDER-SCOPE | D. Invariants / spec sync | `check_engine.py:100-102`; `pqsx96:144` | `I-16` is already carried by `check.setid-collision` and is defined normatively as setid SEMANTICS, which says nothing about LENGTH. Reusing it is a catalog change, and the invariant catalog spec was missing from `Scope-Paths`. The catalog's own history records that mis-homing a rule under a non-describing invariant was a defect it already had to fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires either a NEW catalog entry or a deliberately WIDENED `I-16`, with `pqsx96` amended in the SAME change (following the `216rgg` precedent) and the choice justified; `pqsx96` added to `Scope-Paths`. |
| PR-406 | MEDIUM | IN-SCOPE | A. Correctness | `ipd_lint.py:48-60` | `IPD-M110` DOES NOT EXIST and the next free code is `IPD-M109`; minting M110 would leave a hole at M109. The plan also named "`IPD-M104` / `IPD-M110`" as if either would do, which is two codes for one condition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 requires ONE code, either the reused `IPD-M104` or a newly allocated `IPD-M109`, chosen and justified, defined as a named constant beside its siblings; `IPD-M110` forbidden. |
| PR-407 | MEDIUM | IN-SCOPE | G. Executability | `ls`; `--help` probes | FOUR declared paths do not exist: `agent_workflows/ipd_scaffold.py` (scaffold is `ipd_authoring.run_scaffold:336`), `agent_workflows/research.py` (`research_cmd.run_new:641`), `agent_workflows/artifact_cli.py` (`aw group` is in `artifact_rename.py`), and `tests/test_ipd_scaffold.py`. A nonexistent declared path also creates an unsatisfiable reconciliation at finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All four corrected in `Scope-Paths` and in E-06/validation; `tests/test_shared_checkout_contract.py` added for the regeneration proof. |
| PR-408 | MEDIUM | OVER-SCOPE | G. Executability | `specs.py:988,1018`; `aw specs new --help` | `aw specs new` HAS NO `--set` flag and cannot violate the bound: it passes `set_id=id6`, so a spec's setid is always exactly 6 generated characters. Guarding it is unreachable code, and V-06's test would need a flag that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed from E-06 with the reason recorded; the item now names the FOUR verbs that actually take `--set` and requires ONE shared validator rather than four copies. |
| PR-409 | MEDIUM | IN-SCOPE | A. Correctness / F. Honest docs | `AGENTS.md:26` vs `:109` | `AGENTS.md:26` is INSIDE the generated managed block (which ends at `:109`), so a direct edit is reverted by regeneration and caught by the no-drift test. The plan told the executor to "update `AGENTS.md` lines 25 and 118" (25 is also off by one; the sentence is at 26). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now requires the managed-block change in `engine.py` plus regeneration proven via `NoDriftTests::test_repo_agents_block_equals_generated`, warns that a `merge_aw_block` round trip cannot detect drift here, and directs `:118` to be edited directly. |
| PR-410 | LOW | IN-SCOPE | A. Correctness | `check_engine.py:4686`; `config.py:1325`; `ipd_lint.py:1259-1262` | Three stale citations and one wrong field name: `CARRIER_CUTOVER_DATE` is `:4686` not `:4505`, `read_dependency_schema_cutover` is `:1325` not `:1047`, and `LintResult`'s field is `diagnostics` not `diags`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All corrected in the conventions section with an instruction to verify by symbol rather than by line. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The maintainer-directive conflict over `KNOWN_FEATURE_CUTOVERS`: resolve it myself or ask? | ASK. Escalated as blocking OQ-03 with three options and a recommendation. | Resolving it as option (a) on my own authority, rejected because it is a reading of the maintainer's own instruction, not a repository fact; resolving it as (b) would edit the dependency's shipped function on a reviewer's judgement. | The directive is recorded in the plan's Findings as a maintainer directive; `config.py:1141-1167` shows the mechanism contradicts it in letter. Workflow rule: never guess a human decision. | yes |
| D-2 | E-02's deliverable already exists. Rescope or mark REPLAN? | Rescope to a single registry entry, with the measured proof inline. | REPLAN, rejected because six of seven items remain sound and only this one's premise was wrong. | `sync_cutovers_on_install` already called at `engine.py:6566` and `install_wizard.py:921`; proven generic by running it with `setid_length` registered. | yes |
| D-3 | Should the new rules carry `I-16`, or a new invariant? | Neither chosen for the executor: E-03 must pick and amend `pqsx96` in the same change, justifying the choice. | Picking one myself, rejected because widening a normative invariant versus adding one is a contract decision with different downstream costs, and the catalog is the normative source. | `pqsx96:144` defines I-16 as semantics only; `:182-200` records the prior mis-homing and the `216rgg` same-commit repointing precedent. | yes |
| D-4 | How should grandfathering behave for a setid shared across artifacts of different dates? | PER ARTIFACT, resolved from evidence and recorded as OQ-04 with its accepted cost. | Per-setid (earliest or latest date), rejected because "the setid's date" is not a quantity that exists; a `Drift` is located at a file and both cutover precedents compare against the artifact's own date. | `_spec_requires_id6` uses the filename date; `carrier_severity_for_plan` uses the plan's `- Date:`; measured that `backlog-medhigh-260819` spans 8 artifacts. | yes |
| D-5 | Pre-cutover treatment: downgrade severity or suppress? | SUPPRESS, following the in-tree precedent. | Downgrading, which `ipd_lint.py:830-845` shows is a no-op for an already-advisory rule and would flood the output with findings on untouchable history. | That comment states the reasoning verbatim, including the "roughly a thousand advisories" measurement. | yes |
| D-6 | Should `aw specs new` be guarded? | No: excluded with the reason recorded. | Guarding it anyway for uniformity, rejected as unreachable code that would require inventing a `--set` flag to test. | `specs.py:1018` passes `set_id=id6`; `aw specs new --help` shows no `--set`. | yes |
| D-7 | Is correcting four nonexistent declared paths a reviewer over-reach? | No: corrected, since a nonexistent path is unimplementable AND unreconcilable at finalize. | Leaving them and letting the executor discover it, which wastes a turn and strands the finalize gate. | `ls` shows all four absent; the real symbols were located. | yes |
| D-8 | Is the plan's overall approach sound, or does it need REPLAN? | Sound; no REPLAN. The `no-go` rests on OQ-03 alone, not on plan quality. | REPLAN, rejected because the audit reproduces, the gap is real, and every finding is an instruction-level repair or a question. | Corpus re-measurement matches on the two load-bearing figures; both regexes are unbounded; the dependency shipped the infrastructure the plan consumes. | yes |

PR-403 is the only finding not FIXED. It is `HIGH`, which is at the repository's gate threshold, and it
is therefore ESCALATED into the plan as OQ-03 carrying `- Blocking: yes` and `- Finding: PR-403`, so
`aw ipd lint` refuses the plan at every checkpoint until a human answers. No `Reversible: no` decision
was made in this round.

## Round 2

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-403 | high | IN-SCOPE | C. Architecture / F. Principles | `config.py:1141-1167` | The maintainer directive forbids a hardcoded calendar date in Python, but the shipped stamper only covers features listed in `KNOWN_FEATURE_CUTOVERS`, every entry of which IS a hardcoded date. Registering `setid_length` therefore writes a date into source. Not resolvable from the repository: it is a reading of the maintainer's own instruction. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | fixed | STALE ESCALATION CLOSED 2026-09-21 by opencode its_direct/pt3-claude-opus-5-1m-us. The question this finding was escalated as (OQ-03) is `- Status: resolved`, so the finding it gated on has been answered and the record is caught up. NO FINDING WAS RE-DERIVED and no plan content was re-critiqued: the match was made on the question's declared `- Finding: PR-403` back-reference, not on a judgement about what the question was about. Previous decision: open. |
