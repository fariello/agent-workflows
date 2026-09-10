# Review: give the hardened execution profile a request path or record why it has none, child n5qca5 (Set hardreach)

- Subject-Id: n5qca5
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `261a72a2`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0 findings)
before semantic review, and `--phase review-finalize` conformed after the revisions. The plan carries
`- Blocks-Release: next`, correctly inherited from backlog `fjs11i`.

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat this as a
near-self-review and worth less than an independent one.

THE PREMISE IS TRUE AND I RE-MEASURED ALL OF IT. There is exactly ONE occurrence of
`options["execution_profile"]` in the package and it is a COMMENT (`oc_runipd.py:5499`), there is no
setter and no CLI flag, and the capability it guards genuinely works here:
`detect_host_capabilities("opencode")` returns `supports_os_sandbox=True`, `sandbox_mechanism="landlock"`,
with the probe note recording that a write outside the allowed root was actually refused. The plan's
staleness corrections to the backlog item are also correct: `dh0uno` really did land in `6771e590`,
`checkout_control_root` exists, `tests/test_statefork_dh0uno.py` passes 17/17, `7p9n2v` really is in
`superseded/`, and `q65sz3` really is still `status: todo`. This is a well-evidenced plan whose central
claims survived independent checking.

THE FINDING THAT WOULD HAVE STOPPED EXECUTION IS THAT THE CHOSEN OUTCOME IS UNIMPLEMENTABLE AS SCOPED.
OQ-01 is resolved to the per-profile `runner_profiles` field, and `ALLOWED_PROFILE_KEYS` is BYTE-PINNED by
two security-fence tests that the plan did not declare:
`tests/test_runner_profiles.py::test_no_arbitrary_argv_or_credential_field_is_persistable` (`:1650-1674`)
and `tests/test_runner_profiles_e2e.py::test_every_field_the_doc_says_is_refused_really_is` (`:841-844`)
each assert the sorted list LITERALLY as `["agent","model","runner","validate","variant","verify_with"]`.
The first test's own comment states the intent: the literal exists "so widening them requires editing this
test and stating why". So E-03 could not have landed without touching two undeclared files, and touching
them undeclared would have tripped the finalize scope gate. Both are now declared, and E-03 is required to
satisfy the fence the way `verify_with` did, by justifying the new key IN the test rather than loosening
the assertion.

THE SAME E2E TEST BINDS THE SCHEMA TO THE DOC, which promotes E-04 from documentation to a build
dependency: the allowed list must equal what `docs/runner-profiles.md` lists, and a sibling test forbids
em and en dashes in that file. A plan that treated the doc as optional polish would have failed the suite.

THE SECURITY LENS FOUND THE CONSTRAINT ON THE FIELD ITSELF. `FORBIDDEN_PROFILE_KEYS` refuses `permission`
and `permissions` BY NAME, alongside argv, credential and prompt keys, each because it "would convert a
convenience alias into a command-injection, credential-disclosure, or behavior-override surface". A
sandbox-request field sits directly next to that boundary, so its name and value space matter: it must be
a closed enum or boolean, never a path, root, argv fragment or permission expression. The `verify_with`
precedent is explicit that a REFERENCE to an already-validated concept is what makes a new key safe where
an inline value would not be.

THE GATE PARAGRAPH CONTRADICTED THE ARTIFACT AND WOULD HAVE HALTED AN EXECUTOR. It said the plan "carries
a BLOCKING open question (OQ-01) and therefore cannot execute past E-02", while all three questions read
`- Blocking: no` and OQ-01 is `- Status: resolved` with a recorded maintainer decision of 2026-09-08. Left
as written it tells an executor to stop and wait for an answer that already exists. Corrected, with E-02
reframed as record-the-analysis and E-03's branch named.

TWO SMALLER CORRECTIONS THAT CHANGE THE WORK. `SCHEMA_VERSION` is 2, not 1 as the plan says, with both 1
and 2 read, nothing migrated, and the reader deliberately version-AGNOSTIC about a FIELD, so an optional
key needs no version bump and the plan's migration worry is already answered by existing design. And a
profile field means the agy host SILENTLY IGNORES a hardened request rather than refusing it, because that
host reads no profile keys at all; that is degradation-by-omission, the precise failure mode
`select_execution_profile` raises to prevent, so it must be stated in the user-facing doc.

The suite baseline is wrong in both halves in the same way I found on three sibling plans: `1 failed, 5958
passed` at the reporting-contract parity test (another party's gitignored `opencode-recovery/` tree), not
`1 failed, 5648 passed` at `test_orchestrator_retirement`, which passes at `112 passed`.

VERIFIED CORRECT AND LEFT ALONE: the fail-closed resolver contract and OQ-02's reasoning, OQ-03's refusal
to change the default, the `q65sz3` fence against proposing a second enforcement mechanism, the no-lane
`SandboxProfileError` branch being dead today, the constructed-capabilities test strategy (which is the
right call and makes the refusal test deterministic on every platform), and the agy-asymmetry measurement.

Eight findings, all FIXED in place, no deferrals. No new open questions: OQ-01 is resolved and the
remaining decisions are execution requirements rather than maintainer questions.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-C01 | HIGH | UNDER-SCOPE | B. security; G. executability | `tests/test_runner_profiles.py:1650-1674`; `tests/test_runner_profiles_e2e.py:841-844`; both assert `sorted(ALLOWED_PROFILE_KEYS)` literally | **THE RESOLVED OUTCOME IS UNIMPLEMENTABLE AS SCOPED: adding the key breaks two pinned security tests that were not declared.** Both assert the allowed-key list as an exact sorted literal, and the first test's comment says the literal exists so that widening it "requires editing this test and stating why". E-03 could not land without editing two undeclared files, and doing so undeclared would trip the finalize scope gate | C:Low; U:Low; S:Medium; F:High; Overall:Medium | FIXED | Both test files added to `Scope-Paths` with the reason; E-03 requires editing both literals WITH an in-test justification following `verify_with`'s precedent, and forbids loosening either assertion into a subset check; required-tests and V-03 demand the edited literals, the empty allowed/forbidden intersection, and both suites' summary lines; new F-10 |
| PR-C02 | HIGH | UNDER-SCOPE | B. security; A. correctness | `runner_profiles.py:215-225` (`permission`, `permissions` forbidden by name); the `verify_with` reference-not-inline rationale | **THE FIELD'S NAME AND VALUE SPACE ARE CONSTRAINED BY A SECURITY LIST THE PLAN NEVER MENTIONS.** `FORBIDDEN_PROFILE_KEYS` refuses `permission`/`permissions` outright, alongside argv/credential/prompt keys, each because it would convert a convenience alias into an injection or override surface. A sandbox-request field is adjacent to that boundary; unconstrained, an executor could store a path or a root | C:Low; U:Low; S:High; F:Medium; Overall:Medium | FIXED | Concern and E-03 require a closed enum or boolean, never a path, root, argv fragment or permission expression, with the `verify_with` reference precedent cited; required-tests and V-03 demand proof those three value shapes are REFUSED; conventions updated; new F-12 |
| PR-C03 | HIGH | IN-SCOPE | G. executability | plan `:149`, `:152`, `:160`, `:167` (all `Blocking: no`, OQ-01 `resolved`) versus the gate paragraph | **THE GATE PARAGRAPH CONTRADICTS THE ARTIFACT AND WOULD HALT AN EXECUTOR AT E-02.** It claims a blocking OQ-01 that "cannot execute past E-02 until the maintainer answers", while OQ-01 is resolved with a recorded maintainer decision and no question is blocking. An executor obeying the gate would wait for an answer that already exists | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten to state no blocking question, name the resolved outcome, reframe E-02 as record-the-analysis, and mark E-03's other two branches as retained-for-legibility rather than live alternatives; new F-13 |
| PR-C04 | HIGH | IN-SCOPE | E. testing; G. executability | `tests/test_runner_profiles_e2e.py:838-844` (allowed list "is exactly what the doc lists"), `:846-850` (no em/en dash) | **THE DOC IS TEST-BOUND, so E-04 is a build dependency rather than documentation.** The e2e suite asserts the schema's allowed list equals the doc's list and forbids dashes in that file, so the doc must gain the field in the SAME change or the suite fails. The plan treats `docs/runner-profiles.md` as user-facing prose only | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 states the doc binding; spec-sync section rewritten to say the edit is mandatory and test-enforced; new F-11 |
| PR-C05 | MEDIUM | IN-SCOPE | Evidence accuracy; A. correctness | `runner_profiles.py:145-159`: `SCHEMA_VERSION = 2`, `SUPPORTED_SCHEMA_VERSIONS = {1, 2}`, both read, nothing migrated, reader version-agnostic about a field | **SCHEMA_VERSION IS 2, NOT 1, AND NO VERSION BUMP IS NEEDED.** The plan's migration caution rests on a wrong version and on a concern the module already answers: a v1 document keeps loading byte-for-byte and the reader is deliberately agnostic about which fields a version carries | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 corrected with the real constants and the reasoning; required-tests demand a `schema_version: 1` document still loads and that NO bump was made; conventions updated; new F-15 |
| PR-C06 | MEDIUM | UNDER-SCOPE | B. security; F. UX honesty | F-7's measurement (five profile identifiers grep to zero in `agy_runipd.py`) plus `select_execution_profile`'s raise-not-degrade contract | **A PROFILE FIELD MEANS AGY SILENTLY IGNORES THE REQUEST RATHER THAN REFUSING IT.** The plan documents the asymmetry but never names the consequence, which is degradation-by-omission: a user who set the field in a shared profile and runs on agy believes a boundary exists when none does. That is exactly the harm the fail-closed resolver raises to prevent | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | E-03 requires the consequence stated explicitly and forbids adding an agy refusal as a smuggled change; spec-sync requires the doc to state it; V-03 requires the statement pasted; new F-16 |
| PR-C07 | MEDIUM | IN-SCOPE | E. testing; Evidence accuracy | bare pytest at `261a72a2` -> `1 failed, 5958 passed, 3 skipped, 2 xfailed` at `test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`; `test_orchestrator_retirement.py` -> `112 passed` | **THE SUITE BASELINE IS WRONG IN BOTH HALVES AND NAMES A TEST THAT PASSES.** The real failure is the reporting-contract parity test, caused by another party's gitignored `opencode-recovery/` transcript tree. An executor could attribute it to their own change or clean up files that are not theirs | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 and required-tests carry the re-measured baseline, the real node id, the cause, a do-not-touch prohibition under the shared-checkout rule, and node-id rather than count comparison; V-05 requires both node-id lists; new F-14 |
| PR-C08 | LOW | IN-SCOPE | G. executability; Evidence accuracy | measured by symbol: comment at `:5499` not `:5392`; `_apply_execution_profile` `:5030`; `runner_profiles` symbols `:150`/`:190`/`:612`/`:633` not `:101`/`:126`/`:480`/`:501` | **THE WRITER'S SEAM IS UNSTATED AND SEVERAL CITATIONS HAD DRIFTED.** "Resolve it into `options` at run creation" does not name `resolve_launch_profile`, whose two properties are load-bearing: resolution happens BEFORE the run directory exists (so a bad config leaves no partial state) and the options snapshot is FROZEN ONCE (so a later config edit cannot change a running run) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 names the seam and both properties, plus the module's "an explicit flag always wins" precedence rule; required-tests and V-03 demand proof of both; conventions updated; F-6 re-located and new F-17 records the drift |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Adding the profile key breaks two pinned security tests (PR-C01). Declare and edit them, or find a route that avoids touching them? | DECLARE BOTH and require the literals be edited WITH an in-test justification, following `verify_with` | Loosen the assertions to a subset or membership check (rejected: the literal list IS the control, and its own comment says widening must require editing the test and stating why, so weakening it defeats the fence while appearing to satisfy it); route the request through a non-profile surface to avoid the tests (rejected: OQ-01 is resolved to the profile field by the maintainer, and choosing a surface to dodge a test is the wrong reason to choose a surface) | the two literal assertions and the first test's stated intent; `verify_with`'s precedent of editing both literals with a justification | yes |
| D-2 | The gate paragraph says OQ-01 is blocking while the artifact says resolved (PR-C03). Which is authoritative? | THE ARTIFACT'S FIELDS ARE AUTHORITATIVE: no blocking question, OQ-01 resolved, so the gate prose is stale and was corrected to match | Treat the gate as authoritative and set `Blocking: yes` (rejected: that would forge a maintainer question out of stale prose and would refuse a plan whose decision is recorded in its own OQ-01 with a date and reasoning); leave both (rejected: an executor reading the gate stops at E-02 and waits for an answer that exists) | plan `:149`/`:152`/`:160`/`:167`; OQ-01's recorded 2026-09-08 maintainer decision | yes |
| D-3 | A profile field makes agy silently ignore the request (PR-C06). Add an agy refusal, or document the gap? | DOCUMENT IT, in both the code site and the user-facing doc, and explicitly forbid adding an agy refusal in this plan | Add a refusal in `agy_runipd` (rejected: that host has no profile integration at all, so a refusal needs a profile reader first, which is `rununify`/`runprofile` territory and would be a smuggled architectural change); say nothing (rejected: silence recreates the exact harm the refuse-not-degrade rule exists to prevent, one host over) | five profile identifiers grep to zero in `agy_runipd.py`; `select_execution_profile`'s raise-not-degrade contract | yes |
| D-4 | Does the optional field need a schema version bump (PR-C05)? | NO. Both versions are read, nothing is migrated, and the reader is version-agnostic about a field | Bump to 3 (rejected: it would make every older `aw` refuse a document it can actually read, and the module's own `verify_with` note explains that the bump to 2 was about which REFUSAL an old aw shows for an unknown FIELD, not about field addition per se); leave the plan's v1 claim (rejected: it is simply wrong and the migration worry it raises is already answered) | `runner_profiles.py:145-159` | yes |
