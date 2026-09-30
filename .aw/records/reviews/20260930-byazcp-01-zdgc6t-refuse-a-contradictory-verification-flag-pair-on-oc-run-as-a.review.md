# Review findings: plan zdgc6t

- Subject-Id: zdgc6t
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-B01 (HIGH, fixed), PR-B02 (MEDIUM, fixed), PR-B03 (MEDIUM, fixed), PR-B04 (MEDIUM, fixed), PR-B05 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `cf173dde`. The plan file was committed and byte-identical
to the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author` reported `conforming` BEFORE semantic review and again at
`review-finalize` after revision. The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check
does not apply. `- Item-Dependencies: none`. Suite at review, bare: `3387 passed, 2 skipped in 58.22s`.

EVERY ONE OF F-01 THROUGH F-10 REPRODUCES AT THIS HEAD. I re-drove all ten rather than trusting any:

- F-01 exactly: `oc start --no-verify --validate` -> `validate=True`, reversed -> `False`, no refusal.
  The dest walk confirms all six spellings on one `BooleanOptionalAction` on both oc subcommands.
- F-02 exactly, including the durable half: oc `resume` carries the same six spellings on the same
  dest, `resume run-x --no-verify --validate` parses `True`, and `oc_runipd.main`'s resume branch
  writes `state["options"]["validate"]` and `["no_audit"]` guarded on `getattr(args, "validate", None)
  is not None`.
- F-03 exactly, and this is the finding that most deserved re-driving because the whole mechanism
  rests on it. I patched the recording subclass onto the LIVE oc `start` and `resume` `validate`
  actions and ran eight argv cases: both contradictory orders and the abbreviated `--no-aud --vali`
  refuse; `--validate --verify`, a bare `start`, and a `status` invocation pass through with the key
  ABSENT from the namespace; three sequential `parse_args` calls on one reused parser show no
  accumulation. Canonical-spelling resolution confirmed (`--no-aud` -> `--no-audit`).
- F-04: the parsed namespace carries `validate` and no spelling record;
  `hasattr(oc_runipd, "verification_flag_tristate")` is `False`.
- F-05: `verification_flag_tristate`'s check is `bool(no_verify) and validate is True` over two
  `getattr` reads, and oc has no second attribute, so the item's lift-verbatim suggestion is indeed
  unusable. The plan's correction is the right shape.
- F-06 exactly: agy `--validate --no-validate` -> `False`, reversed -> `True`, neither raising, while
  `--no-verify --validate` raises in both orders.
- F-07 exactly: `issubclass(RunFlagRefusal, DriverError)` and `oc_runipd.DriverError is
  runner_shared.DriverError` both `True`; `main`'s `except DriverError` prints `runipd: <message>` and
  returns 2.
- F-08: spec 2.1c consequence 2 and the named test both read as quoted. The suite baseline has moved
  from the authored `3246` to `3387`, which the plan already forbids pinning, so this is the drift the
  plan predicted rather than a finding.
- F-09 holds on a wider search than the plan ran: every in-repo occurrence of a contradictory pair is
  a description or an assertion, never an invocation. No internal caller composes runner argv with a
  verification flag; the `aw oc run` wrapper forwards `argparse.REMAINDER` verbatim and declares none
  of these flags itself.
- F-10 holds: the `docs/runner-profiles.md` sentence reads as quoted and is false on oc today.

THE ONE SERIOUS FINDING WOULD HAVE SHIPPED A SECOND INSTANCE OF THE DEFECT THE PLAN EXISTS TO REMOVE.

PR-B01. E-04 said to place the resume refusal "before the branch that writes
`state["options"]["validate"]`". Between the head of the `resume` branch and that write sits
`runner_shared.apply_run_policy_flags_on_resume`, which writes and whose caller saves. Driven with
`resume run-x --no-verify --validate --full-auto`, that helper flipped `options.full_auto` from
`False` to `True` and returned `True`, so `save_state` persists it. A refusal placed where E-04 said
therefore leaves a REFUSED invocation having durably mutated the frozen run. The worst part is that
the plan's own V-04 could not see it: V-04 asked for `options.validate` to be unchanged, and
`validate` is precisely the key that helper leaves alone, because `--validate` is not one of the
sixteen `RUN_POLICY_FLAGS` rows. So the authored evidence requirement would have PASSED on the
defective placement. The harm is the same class the plan is written to remove, a policy applied that
the operator's own invocation was being refused for, silently. The correct seam is the one the two
shipped resume refusals already use: `refuse_frozen_flags_on_resume` and the `--verify-with`
`DriverError` both fire at the head of the branch, before any `load_state`.

THREE FINDINGS OF SUBSTANCE BUT SMALLER BLAST RADIUS.

PR-B02. E-06 and the gate both invoked "the untooled-status pre-commit hook" as the backstop that
would refuse a hand-appended spec history line. It would not. That hook delegates to
`check_engine.check_status_untooled`, whose staged diff is scoped to `_PLANS_PREFIX =
".aw/records/plans/"` and which `continue`s on any path failing `_is_plan_ipd_path`, so it never opens
a `.spec.md`. The only spec-side lifecycle checker, `check_spec_review_attestation`, is scoped by its
own docstring to `- Status: reviewed` and is silent on an `approved` spec by construction. Naming an
absent gate is worse than admitting the gap, because an executor may reason that the hook will catch
a shortcut and take it.

PR-B03. E-01 specified a subclass of `argparse._StoreTrueAction`, a private stdlib symbol, across a
declared `requires-python = ">=3.9"` range. It buys nothing: a `store_true` action's whole behavior is
`setattr(namespace, dest, True)` at `nargs=0`, which a public `argparse.Action` subclass reproduces,
and I drove both forms to identical results. Worth stating precisely because this repository DOES use
`argparse._SubParsersAction` in ten production sites: that one INSPECTS a parser and has no public
equivalent, whereas subclassing a private action to reimplement three lines has one.

PR-B04. OQ-02 resolved "keep both checks" on the premise that they cover different inputs, a
hand-built namespace versus a real parse. Half right. On a REAL parse of `--no-verify --validate` BOTH
fire: the namespace check on the two dests, the shared predicate on the two recorded spellings. So the
call order decides which message an operator sees, and two shipped test classes
(`AgyVerificationFlagSurfaceTests::test_contradictory_flag_refusal_and_partial_namespace` and the
`VerificationDestAsymmetryPerHostTests` method E-02 names) assert on the existing wording. The
premise's correct half is confirmed: a hand-built `Namespace(no_verify=True, validate=True)` is
refused by the namespace check and invisible to the predicate, so retaining it is right.

PR-B05. A batch of coverage and evidence gaps. E-01 never asked whether the recorded list can reach
durable state (it cannot today: `state.json`'s `options` is built from named `getattr` reads plus
`freeze_run_policy_flags`' explicit table, and no `vars(args)` call exists in either runner or in
`runner_shared`, but the property was unstated and a future `vars(args)`-based freeze would start
persisting a parse artifact silently). Validation item 3 pinned "same polarity does not refuse" on one
example when three more exist and were driven. Item 5 asserted the flag surface did not move using
only the `start`/`resume` table, which cannot see a spelling accidentally gained by another
subcommand. E-05 never asked for `assert_verification_flags_are_distinct` to be re-driven under the
subclass, which I did confirm passes.

WHAT IS GENUINELY STRONG HERE, and it is most of the plan. The mechanism was driven against the real
parser before being written down, which is rare and is what made F-03 verifiable rather than
plausible. Two of the backlog item's claims are actively CORRECTED rather than inherited (F-05's
unusable fix, F-06's unreported agy hole), and F-06 in particular means the plan declines the easy
framing of "make oc match agy" that would have left a live instance of the same defect on the host
held up as correct. The scope fence is tight and argued: the dest table is protected, the
de-duplication is refused with a named carrier, and the three `Carrier-Declined` rows each argue from
measurement rather than convenience. F-10 is the kind of finding most plans get backwards, correctly
concluding that a doc needs no edit because the change makes existing prose true. No `V-*` item was
weakened by this review; four were strengthened.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-B01 | HIGH | IN-SCOPE | Rubric A (correctness, dependent writes), D (anti-regression) | plan E-04 and V-04; `runner_shared.apply_run_policy_flags_on_resume` driven at review; `RUN_POLICY_FLAGS` enumerated; the two shipped resume refusals read at the head of `oc_runipd.main`'s resume branch | E-04 placed the resume refusal "before the branch that writes `state["options"]["validate"]`", which is DOWNSTREAM of `apply_run_policy_flags_on_resume`. That helper writes and its caller saves: driven with `resume run-x --no-verify --validate --full-auto` it flipped `options.full_auto` `False -> True`. So a REFUSED resume would durably apply a policy the refusal was rejecting, which is the same class of silent unasked-for decision this plan exists to remove. V-04 could not catch it, because it checked only `options.validate`, the one key that helper leaves alone (`--validate` is not a `RUN_POLICY_FLAGS` row), so the authored evidence would have PASSED on the defective placement. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-04 now names the FIRST statement of the `resume` branch, beside `refuse_frozen_flags_on_resume` and upstream of `apply_run_policy_flags_on_resume`, with the measurement and the reason. V-04 rejects an `options.validate`-only check by name and requires a byte-level `state.json` comparison with `options.full_auto` named. Recorded as F-11; the Scope line, proposed-change 4, and validation item 6 all carry it. |
| PR-B02 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy; Rubric G (executability) | plan E-06 and the gate's STOP CONDITIONS; `agent_workflows/hooks/status_untooled_gate.py`; `check_engine.check_status_untooled` (`_PLANS_PREFIX`, `_is_plan_ipd_path` guard); `check_spec_review_attestation` docstring | E-06 and the gate both cite "the untooled-status pre-commit hook" as what refuses a hand-appended spec history line. It cannot: it delegates to `check_status_untooled`, whose staged diff is scoped to `.aw/records/plans/` and which skips any non-plan-IPD path, so it never reads a `.spec.md`. The one spec-side checker is scoped to `- Status: reviewed` and silent on an `approved` spec. Invoking an absent gate is worse than admitting the gap, because an executor may take a shortcut believing something will catch it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-12. E-06 now states the measurement and that the discipline is the executor's, not a gate's. The gate's STOP CONDITIONS carry the same correction instead of the false claim. |
| PR-B03 | MEDIUM | IN-SCOPE | Rubric C (architecture), F (KISS) | plan E-01; `pyproject.toml:12` `requires-python = ">=3.9"`; a public `argparse.Action` subclass driven to identical results; `grep argparse\._` across `agent_workflows/` | E-01 specified a subclass of the PRIVATE `argparse._StoreTrueAction` across a declared `>=3.9` range, for behavior that is three lines of public API (`setattr(namespace, dest, True)` at `nargs=0`). Driven at review, a public `argparse.Action` subclass records `--no-aud` as `--no-audit` and parses `no_verify=True` identically. This is not a blanket ban: `argparse._SubParsersAction` is used in ten production sites to INSPECT a parser, which has no public equivalent, whereas this case does. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Recorded as F-13. E-01 mandates the public-API subclass and states why; its Expected outcome forbids a private reference; proposed-change 1 matches; V-01 treats a private subclass as a FAILED validation even when it behaves correctly. |
| PR-B04 | MEDIUM | IN-SCOPE | Rubric A (correctness of a resolved decision); Rubric D | plan OQ-02 and E-05; both agy checks driven over six argv cases plus a hand-built partial namespace | OQ-02 resolved "keep both" on the premise that the two agy checks cover DIFFERENT inputs. On a real parse of `--no-verify --validate` both fire, so the premise is half wrong and the CALL ORDER decides the operator-visible message. Two shipped test classes assert on the existing wording, so calling the shared predicate first would change the text they pin while the plan claims to preserve it. The premise's other half is confirmed: a hand-built `Namespace(no_verify=True, validate=True)` is refused only by the retained check. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | OQ-02's rationale corrected with the measurement and the ordering consequence. E-05 specifies the retained namespace check FIRST and names both asserting test classes; it also records that `assert_verification_flags_are_distinct` passes unchanged under the subclass (driven at review). V-05 requires the FULL refusal message text and calls the reverse order a FAILED validation; validation item 4 carries it. |
| PR-B05 | LOW | UNDER-SCOPE | Rubric E (testing), D (anti-regression) | plan E-01, validation items 3 and 5, E-05; `state.json` `options` construction in `runner_shared.initialize_run_core`; per-subcommand spelling walk over both hosts | Four coverage gaps. E-01 never asked whether the recorded namespace key can reach durable state (it cannot today, but the property was unstated, so a future `vars(args)`-based freeze would silently persist a parse artifact). Validation item 3 pinned "same polarity never refuses" on ONE example when three more exist. Item 5 proved the flag surface did not move using only the `start`/`resume` table, which cannot see a spelling gained by another subcommand. E-05 never asked for `assert_verification_flags_are_distinct` to be re-driven under the subclass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 requires an underscore-prefixed key and states the no-durable-leak property with its measurement. Validation item 3 adds the three measured same-polarity forms; item 5 adds the all-subcommand assertion; V-03 requires the full per-subcommand walk with the measured expectation spelled out. E-05 and V-05 require the distinctness guard re-driven. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-04's resume seam lets a refused invocation write durable state. Move the refusal to the head of the branch, or make `apply_run_policy_flags_on_resume` itself refusal-aware? | MOVE THE REFUSAL to the first statement of the `resume` branch. | Making the policy-flag helper refusal-aware: rejected, it is shared by both hosts and its subject is frozen-policy application, not flag contradiction; threading a verification concern into it would put two unrelated decisions in one function and widen this plan's blast radius onto agy's resume path, which registers none of the six spellings. Leaving the seam and merely widening V-04's evidence: rejected, that documents the defect instead of removing it. | `apply_run_policy_flags_on_resume` driven: flips `options.full_auto` and returns `True` on a contradictory-pair invocation; `RUN_POLICY_FLAGS` contains no `validate` row, which is why `options.validate` alone cannot detect it; `refuse_frozen_flags_on_resume` and the `--verify-with` refusal both already sit at the head of the branch before any `load_state`, so the seam is established rather than invented. | yes |
| D-2 | E-06 cites a pre-commit hook that does not cover specs. Drop the claim, or ask for a spec-side gate to be added? | DROP THE CLAIM and state the gap explicitly as executor discipline. | Adding a spec-side untooled-history gate: rejected as clearly OVER-SCOPE. It is a new check-engine rule plus a hook, affecting every spec edit in the repository, and it belongs to whoever owns the spec lifecycle rather than to a plan whose subject is two argparse registrations. Saying nothing: rejected, the plan would then read as if a gate existed. | `status_untooled_gate.py` delegating to `_ce.check_status_untooled`; that function's `_PLANS_PREFIX` diff scope and `_is_plan_ipd_path` guard; `check_spec_review_attestation`'s "SCOPED TO `reviewed` AND NOTHING ELSE" paragraph. | yes |
| D-3 | Is the private `argparse._StoreTrueAction` subclass acceptable given this repo already uses `argparse._SubParsersAction`? | NO for this case; mandate a public `argparse.Action` subclass. The existing private usage is distinguishable and is left alone. | Allowing it for consistency with the ten `_SubParsersAction` sites: rejected, because those INSPECT a parser and argparse offers no public way to do that, whereas a `store_true` action's behavior is three lines of public API. Banning `argparse._*` repository-wide: rejected as over-scope and wrong, it would condemn ten correct sites. | `pyproject.toml:12` `requires-python = ">=3.9"`, so the private name spans five minor versions with no guarantee; a public `argparse.Action` subclass driven to identical results on `--no-aud`; `grep argparse\._` showing the existing sites are all inspection. | yes |
| D-4 | Which agy check should run first now that both fire on `--no-verify --validate`? | THE RETAINED NAMESPACE CHECK FIRST, so the shipped message keeps winning on the pair it already owns. | Shared predicate first: rejected, it would change the operator-visible text that two shipped test classes assert on, inside a plan that explicitly promises to preserve that wording so the existing assertion keeps testing the same contract. Merging the two into one check: rejected, they answer different questions over different inputs (a hand-built namespace versus a real parse), which is the same reason the plan gives for not touching `assert_verification_flags_are_distinct`. | Both checks driven over six argv cases: both fire on `--no-verify --validate`; only the namespace check fires on a hand-built `Namespace(no_verify=True, validate=True)`; only the predicate fires on `--validate --no-validate`; the existing message text located in both asserting test classes. | yes |

No `Reversible: no` decision was taken in this round. OQ-01 and OQ-02 are both `resolved` and
`Blocking: no`, so no open question remains to hold the plan under the 2026-09-10 ruling. No finding
was left `OPEN` or `DEFERRED`, so no escalation to a `- Blocking: yes` question is required.
