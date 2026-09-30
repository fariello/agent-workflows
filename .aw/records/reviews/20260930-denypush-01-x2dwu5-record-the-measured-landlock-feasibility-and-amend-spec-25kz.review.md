# Review findings: plan x2dwu5

- Subject-Id: x2dwu5
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-701 (HIGH, fixed), PR-702 (MEDIUM, fixed), PR-703 (MEDIUM, fixed), PR-704 (MEDIUM, fixed), PR-705 (LOW, fixed), PR-706 (LOW, fixed), PR-707 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file was committed and byte-identical to the lane input
(`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review; `--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:`
bullet reads `child`, so the `IPD-S407` orchestrator child-row check does NOT apply and the bounded
repair loop was never entered.

I RE-RAN ALL THREE PROBES THIS PLAN'S E-01 DEMANDS rather than reading research `uq4y6q`, because the
plan's entire deliverable is a measurement and a review that trusts the measurement reviews nothing.
Every load-bearing claim holds on this host:

- Probe (a), two-sided: `abi: 4`, `create_ruleset fd: 4 errno: 0`, `add_rule(NET_PORT) rc: 0`,
  `restrict_self rc: 0`, `allowed connect ok: True`, `denied connect refused: True
  PermissionError(13, 'Permission denied')`, `RESULT: ENFORCED`.
- Probe (b), one ruleset both classes: `combined create_ruleset fd: 3 errno: 0`, `fs allowed write: OK`,
  `fs denied write: EPERM -> ENFORCED`, `net 443: EPERM -> ENFORCED`.
- Probe (c), address-blindness: `net_port rule struct size: 16 (allowed_access u64 + port u64; NO
  address field)`.

So F-1, F-2 and F-3 are sound and the plan's conclusion (ABI-4 TCP denial is real and two-sided, and
port-granular so it cannot separate a git remote from the model API) is correct.

I ALSO RE-DERIVED THE ADDRESS-BLINDNESS FINDING IN A FORM THE PLAN DID NOT ASK FOR, and that became
PR-702. Research `uq4y6q` and this plan's E-01 both measure it against public hosts
(`github.com:443`, `1.1.1.1:443`, `140.82.113.4:443`), which makes the decisive finding depend on
internet egress. It does not need to: with two listeners bound on DISTINCT loopback addresses at the
SAME port and only that port allowed, I measured `127.0.0.1:37037 CONNECTED`, `127.0.0.2:37037
CONNECTED`, `127.0.0.3:38573 EPERM -> KERNEL DENIED`. That is address-blindness proven with no egress
at all, so the external dependency in the authored E-01 was gratuitous.

THE ONE SERIOUS FINDING IS A SECURITY OVERCLAIM THIS PLAN WOULD HAVE WRITTEN INTO AN APPROVED SPEC
(PR-701). F-5 and E-03 asserted that the credential half of 5.2's requirement "is ALREADY built and
shipped". I checked the code rather than the claim, and it is not true as stated, in three measured
ways. FIRST, only credential FILES are withheld: `runner_shared.pinned_child_env` is
`os.environ.copy()` plus a PYTHONPATH pin, and the child-env block in `oc_runipd.run_opencode` pops
exactly four internal keys (`DRIVER_ATTEST_ENV`, `EXECUTION_ROLE_ENV`, `RUN_ID_ENV`, `ITEM_ID6_ENV`),
so a `GH_TOKEN`/`GITHUB_TOKEN` or a forwarded `SSH_AUTH_SOCK` reaches the worker untouched even in
hardened mode. That matters specifically here: the requirement being amended is about PUSH, and an
environment token is a push-capable credential. SECOND, `_apply_execution_profile` returns `argv`
UNCHANGED unless `state["options"]["execution_profile"]` is `hardened`, so the DEFAULT profile
withholds nothing. THIRD, `_hardened_credential_paths` returns `[str(p) for p in candidates if
p.exists()]`, a fixed enumeration rather than a boundary over all credentials. The plan's own stated
purpose is to stop the spec asserting things nobody measured; writing "the credential half is shipped"
into `25kzda` would have replaced one unmeasured claim with a stronger and newly false one, in the very
section whose history is `RUN-NO-PUSH` being retired and `supports_deny_push` being deleted for exactly
this shape of overclaim. Fixed by bounding the required wording in E-03, rewriting F-5 with the three
measured bounds, failing V-03 on an unqualified sentence, and re-framing OQ-01 (whose case FOR
splitting rested on the false premise that one half was done).

TWO VALIDATION ITEMS COULD NOT HAVE BEEN SATISFIED AS WRITTEN. V-04 required
`aw research find --id uq4y6q` "showing the consumed-by provenance"; measured,
`research_index.run_find` prints exactly `id6 <TAB> status <TAB> path <TAB> summary` and carries no
outcome or consumed-by column in ANY mode, including `--json` and `--agent` (I ran all three and got
the identical four-field line). An executor would have pasted a line that does not contain the thing
being verified and marked the item passed. And V-02's evidence was
`m.__doc__.count('out of scope')`, which cannot discriminate: the E-02 replacement deliberately KEEPS
container isolation out of scope, so a nonzero count is the CORRECT post-edit result.

THE GATE WAS MISSING TWO OF THE FIVE EXECUTION-CONTRACT ELEMENTS (PR-704): no scope fence and no
lifecycle-transition ownership. Both matter more than boilerplate here. The fence is what stops this
plan doing Order 02's work (F-6 and F-7 record that adding a capability or a finding code here would
break `DenyPushRemovedTests` or trip `run_evidence.validate_finding_table`'s `RC-COUNT`, which I
verified is a live hard-fail on `len(RUN_FINDING_CODES) != 12`), and the transition sentence is what
stops a runner-driven executor invoking `aw ipd finalize` the runner owns.

I VERIFIED THE PLAN'S OTHER CITATIONS AND THEY HOLD. The docstring anchor "Network scoping and
container isolation are out of scope here." occurs ONCE in the module and nowhere else in
`agent_workflows/`, `tests/` or `docs/`. `_hardened_credential_paths` enumerates exactly the ten paths
F-5 lists and is passed as `build_sandbox_plan(credential_paths=...)`, which folds them into the
INACCESSIBLE class. `landlock_bootstrap_source` does pack `struct.pack("=QQ", ALL, 0)` with the literal
`0` in the `handled_access_net` position. `DenyPushRemovedTests` is live with its assertions intact.
`RUN_FINDING_CODES` holds 12. The gitignore claim is correct in substance though cited by line number
(the entries are anchored `records/research/INDEX.json`/`INDEX.md`), which I restated by path per this
repository's own anti-line-number rule; that rule is one the plan itself invokes in its conventions
section, and the line-number citation was the single place it did not follow its own advice.

ONE THING THE PLAN GETS RIGHT THAT IS WORTH RECORDING, because it is the failure mode the Set exists to
prevent: E-01 refuses to inherit `uq4y6q`'s numbers and re-measures on the executing host, and the
ABI < 4 branch is written to record an unavailable result rather than paste a universal claim. That is
the correct shape and I did not weaken it.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | B. Security / A. Correctness (a fail-OPEN claim written into the contract of record) | F-5 and E-03 said the credential half "is ALREADY built and shipped". Measured: `runner_shared.pinned_child_env` is `os.environ.copy()` plus a PYTHONPATH pin; the child-env block in `oc_runipd.run_opencode` pops only `DRIVER_ATTEST_ENV`, `EXECUTION_ROLE_ENV`, `RUN_ID_ENV`, `ITEM_ID6_ENV`; `_apply_execution_profile` returns `argv` unchanged unless the profile is `hardened`; `_hardened_credential_paths` returns `[str(p) for p in candidates if p.exists()]` | **The plan would have written an unqualified "the credential half is shipped" into approved spec `25kzda` 5.2, and it is not true as stated.** Only credential FILES are withheld, only under an OPT-IN Linux-only profile, and NO environment-carried credential is withheld at all, so a `GH_TOKEN`/`GITHUB_TOKEN` or forwarded `SSH_AUTH_SOCK` reaches the worker in hardened mode. The requirement being amended is about PUSH and an environment token is a push-capable credential, so the sentence would assert a boundary against a class the code does not touch. This is the same fail-OPEN inference that got `RUN-NO-PUSH` retired and `supports_deny_push` deleted, in the same spec section, in a plan whose stated purpose is to stop the spec asserting unmeasured things | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | F-5 rewritten with the three measured bounds and the consequence. E-03 now requires the credential sentence to state all three bounds explicitly and forbids the unqualified form by name. V-03 FAILS a diff asserting it. OQ-01 re-framed: its title and its case FOR splitting both rested on the false premise that one half was done, and the corrected premise (one-partly-done-one-not) weakens that case, which the maintainer should know before ruling. Spec-sync section records that the amendment only reduces risk if the sentence is bounded |
| PR-702 | MEDIUM | IN-SCOPE | E. Testing (the decisive measurement depends on an external network) | Research `uq4y6q` Finding 3 and this plan's E-01 measure address-blindness against `github.com:443`, `1.1.1.1:443`, `140.82.113.4:443`. Reviewer re-measurement on loopback only: two listeners on DISTINCT addresses at the SAME port with only that port allowed yields `127.0.0.1:37037 CONNECTED`, `127.0.0.2:37037 CONNECTED`, `127.0.0.3:38573 EPERM -> KERNEL DENIED` | **E-01's address-blindness probe required internet egress to produce the finding the whole spec amendment rests on.** On an offline or egress-filtered host the result is simply unobtainable, and worse, an unreachable host can be misread as a denial, which is the one-sided-measurement trap in the exact area where it is most expensive. The property is fully measurable on loopback with no external dependency, so the egress was gratuitous | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now REQUIRES loopback (two distinct loopback addresses, same allowed port, third on another port refused) and states the measured reviewer construction and its output so the executor reproduces a known-good shape. E-01 also now requires the constant be named (`LANDLOCK_ACCESS_NET_CONNECT_TCP`) and never written as a numeric bit, citing the orchestrator's recorded `1 << 0` incident. V-01 requires confirmation that the pasted output names no public host. F-3 records the loopback re-measurement beside the original |
| PR-703 | MEDIUM | IN-SCOPE | E. Testing (a validation item whose named command cannot contain the evidence) | V-04 required `aw research find --id uq4y6q` "showing the consumed-by provenance". `research_index.run_find` prints `f"{e.id6}\t{e.status}\t{e.path}\t{e.summary}"` and nothing else; run at review in default, `--json` and `--agent` modes, all three emit the identical four-field line with no outcome or consumed-by | **The command V-04 names cannot evidence what V-04 asks for.** An executor would paste a line that does not contain the provenance and mark the item verified, which is the unfalsifiable-check shape. E-04 also did not state that `aw research set-outcome` is PREVIEW-ONLY without `--apply`, nor that `--to adopted` REQUIRES a non-empty `--consumed-by` (`research_index` reports `outcome: adopted requires a non-empty consumed-by`), so the step could silently write nothing or write a state the checker rejects | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-04 now requires the doc's own `outcome:`/`consumed-by:` front-matter lines or its `INDEX.json` entry, and states the measured reason `aw research find` is not acceptable evidence. E-04 gives the exact invocation with `--apply`, names the both-flags-in-one-call requirement and the two checker rules that enforce it |
| PR-704 | MEDIUM | UNDER-SCOPE | G. Plan executability (missing execution-contract elements) | The gate carried the commit rule, never-push, the paste-output rule and the lint gate, but NO scope fence and NO lifecycle-transition ownership. Verified the constraints a fence would carry are real: `run_evidence` hard-fails `len(RUN_FINDING_CODES) != 12` with `RC-COUNT`; `DenyPushRemovedTests` is live; the orchestrator `l4vw9o` assigns Section 6.1 limit 4 to Order 03 | **Nothing in the gate declared what this plan must not touch, in a Set where the adjacent plan owns the capability and the audit plan owns the spec's second push-denial site.** The runner reconciles edits against a declared fence, so an undeclared fence means an out-of-scope edit is neither prevented nor explained. The transition sentence was absent too, so a runner-driven executor had no instruction not to invoke `aw ipd finalize` the runner owns | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate gains a scope fence written as a DECLARATION (not a stop directive) with three named negative constraints (no probe/capability/finding code, no `def`/signature/constant change, no Section 6.1 edit) each carrying its measured reason, plus the make-then-justify route via `--scope-reason`/`--scope-ack`. Gate also gains the conditional transition-ownership paragraph, the shared-checkout staged-set verification, and the explicit statement that `oq05nc` must not be set `done` |
| PR-705 | LOW | IN-SCOPE | E. Testing (evidence that cannot discriminate) | V-02 asked for `python3 -c "... print(m.__doc__.count('out of scope'))"`. E-02 deliberately KEEPS container isolation out of scope, so a nonzero count is the CORRECT post-edit result. Measured: `test_module_publishes_its_guarantees` asserts `hsp.__doc__` contains `read-only`, `driver`, `linux`, `git common`, `void` | **The named evidence command cannot distinguish the edited docstring from the unedited one**, and V-02 omitted the one docstring risk that is real: a paragraph reflow dropping one of the five tokens a live test asserts | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now requires a command printing BOTH that the replaced sentence is absent AND that all five asserted tokens survive, forbids the bare `count('out of scope')` with the reason, and E-02 records the token list as a preservation requirement plus the measured uniqueness of the anchor sentence |
| PR-706 | LOW | IN-SCOPE | A. Correctness (a grep whose expected count was unstated) | `grep -c 'deny push-capable'` on spec `25kzda` returns **2**: 5.2's requirement bullet and Section 6.1 limit 4 ("deny push-capable network/credentials"). V-03 asked for a grep proving three artifacts byte-unchanged without stating any expected count | **V-03's grep would surface a second hit the plan never mentions, with nothing telling the executor it is expected or who owns it.** The orchestrator `l4vw9o` resolved limit 4 as DO-NOT-AMEND and assigned the recorded judgement to Order 03, but this child carried none of that, so its executor could read a two-hit result as a drift to fix, which would break the byte-unchanged invariant Order 03 re-greps at Set end | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 now states the expected counts as numbers to be RUN and reported (2 for `deny push-capable`, 1 each for the full bullet and the `"deny_push"` packet string), names the second hit as Section 6.1 limit 4, records that Order 03 owns it, and states that a one-hit report means the grep was wrong. The gate's fence forbids editing it |
| PR-707 | LOW | IN-SCOPE | G. Plan executability (a citation by line number, against the plan's own stated rule) | The Scope check cited `.aw/.gitignore` "lines 47-48". The plan's own conventions section opens by requiring citation by symbol or quoted string "with a line number only appended to one of those and never alone", and offers itself as a case study of stale offsets | **The plan violated the citation rule it opens by stating**, in the one place a stale offset would mislead a reader checking whether a generated path is really gitignored. The Scope check also did not record why the plan's OWN file needs no declaration, which is the other question a reader of a three-path fence asks | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Citation restated by anchored path (`records/research/INDEX.json`, `records/research/INDEX.md`) with no line numbers. Scope check now records that `ipd_lifecycle._is_implicitly_allowed` grants `.aw/records/plans/**` as an implicit lifecycle allowance, verified at review, so the plan's own file is correctly undeclared |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-701: the credential claim is materially overstated. Drop it, bound it, or split the spec bullet as OQ-01 proposes? | BOUND it: require the sentence to state files-only, environment-not-withheld, and opt-in/Linux-only | (a) Drop the credential half from E-03 entirely and amend only the network half; (b) apply OQ-01's split now, giving the credential half its own bullet; (c) leave the unqualified wording and let the executor judge | Option (c) is the finding: an unqualified sentence in an APPROVED spec is a durable fail-OPEN claim, and `01reg8` deleted a field and `4h7tt0` retired a finding code for precisely this shape in this section. Option (a) loses real information, because the file-based withholding IS built and shipped and an amendment that omits it leaves the next reader re-deriving it, which is the cost this plan exists to remove. Option (b) is not mine to take: OQ-01 is `Owner: maintainer`, carried by backlog `wcbpqf`, and turns on how a partial guarantee reads, which `wcbpqf` records as a risk-appetite judgement. Bounding is the only option that adds what is true, refuses what is not, and leaves the maintainer's question open. I also re-framed OQ-01 rather than answering it, because its case FOR splitting rested on the premise I just measured false; leaving that premise in place would have had the maintainer rule on bad information | yes |
| D-2 | PR-702: E-01 measures address-blindness against public hosts. Keep the authored shape, or require loopback? | REQUIRE loopback, and cite the reviewer's measured loopback output in the plan | (a) Keep the public-host shape, matching research `uq4y6q` exactly; (b) allow either, at the executor's discretion | Option (a) makes the Set's single most decisive finding conditional on internet egress, and the failure is not merely a skip: an unreachable host raises a connection error that an executor can record as a denial, which is the one-sided trap the orchestrator already documents costing its own reviewer a false positive. Option (b) is worse than either, since discretion here means the weaker shape gets chosen under time pressure. I did not assert loopback would work: I ran it (`127.0.0.1:37037` and `127.0.0.2:37037` both CONNECTED on one allowed port, `127.0.0.3:38573` EPERM), so the requirement is demonstrated rather than reasoned, which is the standard this workflow sets for a HOW resolution | yes |
| D-3 | PR-703: `aw research find` cannot show consumed-by. Substitute different evidence, or add the column to the verb? | SUBSTITUTE the evidence (front matter or `INDEX.json`) | (a) Extend `research_index.run_find` to print outcome/consumed-by, and keep V-04 as written; (b) drop the provenance evidence from V-04 | Option (a) is a code change to a shipped verb's output format, which is out of this plan's scope by construction (it is records-only and declares no `agent_workflows/research_index.py`), and would be a public output-shape change made to satisfy one validation item. If the verb SHOULD carry those columns that is a separate backlog item, not a silent widening here. Option (b) discards a real check: the consumed-by link is the whole point of E-04 and is what makes the research doc findable as provenance rather than an orphan. The front matter and `INDEX.json` both carry the field verbatim, so substituting them costs nothing and is directly falsifiable | yes |
| D-4 | PR-706: spec Section 6.1 limit 4 is the second push-denial site. Should THIS child own it? | NO: leave it unedited, name it in V-03, and point at Order 03 | (a) Amend limit 4 here, since this child is the one amending the spec's push-denial prose; (b) say nothing, as authored | Option (a) would duplicate a decision already recorded: the orchestrator `l4vw9o`'s Cross-IPD row resolved limit 4 as DO-NOT-AMEND (it is already accurate) and assigned the recorded judgement to Order 03's audit, and Order 03's V-02 re-greps the byte-unchanged invariant after the last amendment. A second plan editing it would break that check and re-open a settled call. Option (b) is the finding: the executor meets an unexplained second grep hit and may "fix" it. Naming it as expected, with its owner, is the minimum that makes the non-amendment survive contact with an executor | yes |
