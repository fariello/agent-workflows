# IPD: Record the measured Landlock feasibility and amend spec 25kzda 5.2 to state what a host can and cannot enforce

- Date: 2026-09-29
- Kind: child
- Concern: Spec `25kzda` 5.2 asks whether a host can "deny push-capable network routes and withhold remote credentials" and the repository has never measured whether ANY host can. Plan `4h7tt0` named OS-level enforcement as the only candidate without an agent-level evasion but declined it for scope, leaving the feasibility question unanswered in writing. This plan answers it with measured evidence and amends the spec to say what is actually enforceable, so the next reader inherits a measurement rather than a direction.
- Scope: Amend spec `25kzda` 5.2's push-denial requirement to carry the measured Landlock result (ABI 4 network denial is real, but port-granular and therefore cannot separate a git remote from the model API on TCP 443), and amend `host_sandbox_profile`'s module docstring where it currently declares network scoping out of scope. Records only: this plan adds NO probe, NO capability field, and NO finding code.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, agent_workflows/host_sandbox_profile.py, .aw/records/research/20260929-denypush-00-uq4y6q-landlock-network-push-denial-feasibility.findings.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- From-Backlog: oq05nc
- Set: denypush
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: x2dwu5
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete: APPROVE WITH REVISIONS APPLIED; PR-701..PR-707 all fixed

- 2026-09-30 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-701 (HIGH, fixed), PR-702 (MEDIUM, fixed), PR-703 (MEDIUM, fixed), PR-704 (MEDIUM, fixed), PR-705 (LOW, fixed), PR-706 (LOW, fixed), PR-707 (LOW, fixed). Findings recorded in `.aw/records/reviews/20260930-denypush-01-x2dwu5-record-the-measured-landlock-feasibility-and-amend-spec-25kz.review.md`. I RE-RAN ALL THREE PROBES E-01 DEMANDS rather than reading research `uq4y6q`, since the plan's whole deliverable is a measurement: this host reports `abi: 4`, probe (a) gives `allowed connect ok: True` with `denied connect refused: True PermissionError(13, 'Permission denied')` and `RESULT: ENFORCED`, probe (b) gives `fs denied write: EPERM -> ENFORCED` and `net 443: EPERM -> ENFORCED` from ONE ruleset, and probe (c) confirms `net_port rule struct size: 16 (allowed_access u64 + port u64; NO address field)`. So F-1, F-2 and F-3 hold and the conclusion is correct. THE ONE SERIOUS FINDING was a security overclaim this plan would have written into an APPROVED spec: F-5 and E-03 said the credential half of 5.2's requirement "is ALREADY built and shipped", and it is not, in three measured ways - `runner_shared.pinned_child_env` is `os.environ.copy()` and the launcher pops only four internal keys, so NO environment-carried credential (`GH_TOKEN`, a forwarded `SSH_AUTH_SOCK`) is withheld even in hardened mode; `_apply_execution_profile` returns `argv` unchanged outside the opt-in Linux-only `hardened` profile; and `_hardened_credential_paths` is a fixed existing-paths enumeration. Since the requirement is about PUSH and an environment token is a push-capable credential, the unqualified sentence would have asserted a boundary the code does not provide, in the same spec section whose history is `RUN-NO-PUSH` retired and `supports_deny_push` deleted for exactly that shape. Now bounded in E-03, re-measured in F-5, failed by V-03, and OQ-01 re-framed because its case FOR splitting rested on the false premise. Also fixed: E-01's address-blindness probe required internet egress, which I proved unnecessary by re-measuring it entirely on loopback (`127.0.0.1:37037 CONNECTED`, `127.0.0.2:37037 CONNECTED` on one allowed port, `127.0.0.3:38573 EPERM`), so E-01 now requires that shape; V-04 named `aw research find --id uq4y6q` as consumed-by evidence when that verb prints only `id6/status/path/summary` in every mode including `--json` and `--agent` (measured), so it could never have contained the evidence; V-02's `count('out of scope')` could not discriminate, since the edit deliberately keeps container isolation out of scope; the gate carried no scope fence and no transition-ownership sentence; V-03's grep had no expected count although `grep -c 'deny push-capable'` returns 2, the second hit being Section 6.1 limit 4 which Order 03 owns.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `oq05nc`. Carries the measured Landlock findings (`uq4y6q`) into the spec.
- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Replace the repository's unmeasured assumption about push denial with a measured one, in the two
places that assert it: spec `25kzda` 5.2's host requirement list and `host_sandbox_profile`'s module
docstring. After this plan a reader learns, from the spec itself, that kernel-level network denial is
available at Landlock ABI 4 and that it is PORT-GRANULAR, so it cannot by itself deny an HTTPS push
without also denying the model API the agent needs. No code behavior changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the measurement on the executing host

- [x] E-01 Re-run the three Landlock probes from research `uq4y6q` on the executing host and retain their verbatim output: (a) a `CONNECT_TCP` ruleset with one `LANDLOCK_RULE_NET_PORT` rule allowing a loopback listener, proving the allowed connect succeeds AND a connect to a DIFFERENT (unallowed) port is refused; (b) a combined ruleset carrying both `handled_access_fs` and `handled_access_net`, proving one `restrict_self` enforces both classes; (c) address-blindness, proving a port rule admits two DISTINCT ADDRESSES on the same allowed port while refusing a different port. Do NOT add these scripts to the tree (research `uq4y6q` records why a throwaway measurement script that nothing calls would rot).
  - USE LOOPBACK, NOT PUBLIC HOSTS, and this is a correctness requirement rather than a preference. Research `uq4y6q` measured (a) and (c) against `github.com:443`, `1.1.1.1:443` and `140.82.113.4:443`; reproducing that shape makes the result depend on EXTERNAL REACHABILITY and DNS, so on an offline or egress-filtered host the decisive address-blind finding is simply unobtainable, and an executor under time pressure can misread an unreachable host as a denial. Both facts are measurable entirely on loopback: bind two listeners on DISTINCT addresses (`127.0.0.1` and `127.0.0.2`) at the SAME port, allow only that port, and show both connect while a third listener on another port is refused. DEMONSTRATED AT REVIEW, so this is not a hypothesis: that exact construction yields `127.0.0.1:37037 CONNECTED`, `127.0.0.2:37037 CONNECTED`, `127.0.0.3:38573 EPERM`, which is address-blindness proven with no egress at all. Naming a public host in the pasted output is also the realistic path by which this plan's evidence acquires an unnecessary external dependency the reader cannot re-run.
  - NAME THE CONSTANT, NEVER THE BIT. Write `LANDLOCK_ACCESS_NET_CONNECT_TCP` and derive its value; do not hand-write a numeric literal. The orchestrator `l4vw9o` records the measured reason (its reviewer set the bit to `1 << 0`, which is `BIND_TCP`, and got a total denial that READ LIKE enforcement because the ruleset handled a right the test never exercised). A one-sided read of that run would have reported a working boundary that did not exist.
  - Depends on: none
  - Expected outcome: Three captured outputs. Each of (a) and (c) must show BOTH sides in one run, since a run in which everything is denied is indistinguishable from an over-tight jail and proves nothing. If the executing host reports Landlock ABI < 4, (a) and (b) legitimately report unsupported; record that verbatim and treat it as the measurement, since a host-specific result is the expected shape here and the spec amendment in E-03 must then say the capability was unavailable on the measuring host rather than asserting a universal.
  - Execution state: performed

### Task group 2: amend the two records that currently assert or disclaim this

- [x] E-02 Amend `host_sandbox_profile`'s module docstring, whose published-guarantees ("WHAT THIS DOES NOT DO") paragraph currently ends with the sentence "Network scoping and container isolation are out of scope here." (measured at review: that exact string occurs ONCE in the module and nowhere else in `agent_workflows/`, `tests/` or `docs/`, so it is a safe anchor to replace rather than a phrase repeated elsewhere). Replace the network half of that claim with the measured position: network scoping is now MEASURED rather than out of scope, `handled_access_net` is already the second member of the ruleset attr `landlock_bootstrap_source` packs (it passes a literal `0` today), and the reason no network rule is added is the port-granularity limit, not absence of a mechanism. Keep container isolation out of scope, which is unchanged and still true.
  - STATE THE LIMIT IN THE SAME SENTENCE AS THE CAPABILITY, never in a following one. This paragraph is the module's "WHAT THIS DOES NOT DO" contract, so a reader who stops mid-paragraph must not come away believing network denial is available here. The replacement must not read as "network denial works" with the caveat deferred; it reads as "network denial is measured and CANNOT separate a git remote from the model API on one port, so none is applied".
  - PRESERVE THE FIVE TOKENS A LIVE TEST READS. `tests/test_host_sandbox_profile.py::test_module_publishes_its_guarantees` lowercases `hsp.__doc__` and asserts it contains `read-only`, `driver`, `linux`, `git common` and `void`. None sits in the sentence being replaced, so the edit should be safe by construction; do not let a reflow of the paragraph drop one. V-02 is what proves this rather than assuming it.
  - Depends on: E-01
  - Expected outcome: The docstring names the measured limit and stops implying nobody looked. No code outside the docstring is touched by this item, so no test behavior changes.
  - Execution state: performed

- [x] E-03 Amend spec `25kzda` 5.2 in place. The bullet "deny push-capable network routes and withhold remote credentials" STAYS (plan `01reg8` deliberately preserved it as this work's landing site, and its own deferred row says narrowing it "would delete that work's landing site"). Add prose immediately after the existing paragraph that already explains why the requirement outlived 4.2's `RUN-NO-PUSH`, recording: that the requirement is now MEASURED and not merely aspirational; that kernel-level TCP denial is real at Landlock ABI 4 with two-sided proof; that the mechanism is port-granular with no address field, so it cannot separate a git remote from the model API on 443; that the remaining gap is host-granular filtering; and the CREDENTIAL half in the PRECISELY BOUNDED form F-5 states, which is the one claim in this amendment that could itself become an overclaim. The credential wording must say all three of: (i) in hardened mode `oc_runipd._hardened_credential_paths` makes credential FILES inaccessible (`~/.ssh`, `~/.netrc`, `~/.git-credentials`, `~/.config/gh` and peers), wired through `build_sandbox_plan`'s `credential_paths`; (ii) NO credential carried in the ENVIRONMENT is withheld, because `runner_shared.pinned_child_env` copies `os.environ` wholesale and neither launcher clears it, so a `GH_TOKEN`/`GITHUB_TOKEN` or a forwarded `SSH_AUTH_SOCK` reaches the worker regardless; and (iii) hardened mode is OPT-IN and Linux-only, so the default profile withholds nothing. State explicitly that no host reports this capability today and the answer remains fail-closed.
  - Depends on: E-01
  - Expected outcome: 5.2 records the measurement and a credential claim bounded to file-based credentials under an opt-in profile. The requirement bullet, the 5.2 action table, and the 5.6 packet example's `deny_push` string are all UNCHANGED, so nothing that depends on them moves. DO NOT write an unqualified "the credential half is shipped": F-5 measures why that sentence would be false, and writing a fail-OPEN claim into the contract of record is the exact defect this Set exists to refuse.
  - Execution state: performed

- [x] E-04 Append a `## Workflow history` record to spec `25kzda` with `aw specs note` naming this plan and the measurement, and set research `uq4y6q`'s outcome and consumed-by provenance with `aw research set-outcome <id> --to adopted --consumed-by x2dwu5 --apply` so the findings doc is linked to the plan that consumed it (the verb is PREVIEW-ONLY without `--apply`, and it refreshes the index itself). Then run `aw research index` and `aw research index --check`.
  - `--to adopted` REQUIRES a non-empty `consumed-by` and the checker enforces it: `research_index` reports `outcome: adopted requires a non-empty consumed-by`, and a `consumed-by` id6 resolving to no plan/spec/backlog is a `dangling-consumed-by` finding. So both flags must be passed in the SAME call, and `x2dwu5` resolves only once this plan exists in the tree, which it does.
  - Depends on: E-03
  - Expected outcome: The spec's history shows the amendment with its date and this plan's id6; `uq4y6q`'s front matter carries `outcome: adopted` and `consumed-by: [x2dwu5]`; `aw research index --check` reports no drift.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan's subject is itself a case study: backlog `oq05nc` cites the anti-inference rule at `host_sandbox_profile.py:109-115`, plan `4h7tt0` cites the SAME rule at `:88-95`, and both are stale. Every citation below names a symbol or quotes a string.
- A plan may amend a spec and MUST declare it (AGENTS.md). The spec file is therefore listed in `Scope-Paths`, which is what makes the amendment legitimate rather than a silent weakening, and what makes both runners announce the declared spec edit before the run starts.
- Spec status is owned by `aw specs`, and history is appended with `aw specs note` rather than hand-edited. This plan does NOT change the spec's `- Status:` (it stays `approved`); it amends content and appends history.
- A capability may only be set True by code that executed a probe for it (`HostSandboxCapabilities`' own docstring: "an UNPROBED host claims NOTHING"). This plan adds no capability at all, so it cannot violate that; it is named because the Order-02 sibling depends on it.
- Research artifacts are created and indexed with `aw research`, never hand-named (AGENTS.md). `uq4y6q` was created that way.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | Landlock ABI 4 network denial WORKS on the measuring host, two-sided | Research `uq4y6q` Finding 1: `abi: 4`, allowed loopback connect `True`, port-443 connect `PermissionError(13, 'Permission denied')`, `RESULT: ENFORCED` | The direction `4h7tt0` named is reachable. The spec may honestly stop calling it hypothetical. |
| F-2 | One ruleset carries BOTH fs and net rules | Research `uq4y6q` Finding 2: combined ruleset, `fs denied write: EPERM -> ENFORCED` and `net 443: EPERM -> ENFORCED` | `landlock_bootstrap_source` extends in place. Its `struct.pack("=QQ", ALL, 0)` already passes `handled_access_net` as that literal `0`. |
| F-3 | Net rules are PORT-ONLY, with no address field | Research `uq4y6q` Finding 3: `net_port rule struct size: 16 (allowed_access u64 + port u64; NO address field)`; with 443 allowed, BOTH `140.82.113.4:443` and `1.1.1.1:443` connected, while `:22` was refused. RE-MEASURED AT REVIEW WITHOUT EGRESS, which is the form E-01 must reproduce: with only port 37037 allowed, `127.0.0.1:37037 CONNECTED`, `127.0.0.2:37037 CONNECTED` (distinct address, same port), `127.0.0.3:38573 EPERM` | THE governing limit. A port rule cannot separate a git remote from the model API. This is what the spec amendment must say. The loopback form proves the SAME property with no external dependency, so E-01 requires it. |
| F-4 | The confined process is the one that needs the model API | `oc_runipd._apply_execution_profile` is called on the worker `argv` that launches the coding agent; `enter_sandbox` wraps that argv | Denying 443 denies the product. Allowing 443 permits HTTPS push. Neither setting is the goal, so Landlock alone is not a push boundary. |
| F-5 | The CREDENTIAL half is PARTLY shipped, bounded to FILES under an OPT-IN profile, and the environment half is NOT shipped at all | `oc_runipd._hardened_credential_paths` enumerates `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.netrc`, `~/.git-credentials`, `~/.config/gh`, `~/.docker/config.json`, `~/.kube`, `~/.npmrc`, `~/.pypirc`; passed as `build_sandbox_plan(credential_paths=...)`, which folds them into the INACCESSIBLE class. THE THREE BOUNDS, each measured at review: (a) FILES ONLY - `runner_shared.pinned_child_env` is `os.environ.copy()` plus a PYTHONPATH pin, and the child-env block in `oc_runipd.run_opencode` pops only `DRIVER_ATTEST_ENV`, `EXECUTION_ROLE_ENV`, `RUN_ID_ENV` and `ITEM_ID6_ENV`, so no credential env var is cleared and a `GH_TOKEN`/`GITHUB_TOKEN` or forwarded `SSH_AUTH_SOCK` reaches the worker untouched; (b) OPT-IN - `_apply_execution_profile` returns `argv` UNCHANGED unless `state["options"]["execution_profile"]` is `hardened`, so the DEFAULT profile withholds nothing; (c) EXISTING PATHS ONLY - `_hardened_credential_paths` returns `[str(p) for p in candidates if p.exists()]`, which is fail-closed and correct but means the enumeration is a fixed list rather than a boundary over all credentials | E-03 must write the BOUNDED claim, not "the credential half is shipped". An unqualified sentence in an approved spec would assert a boundary against a credential class the code does not touch, which is the same fail-OPEN inference `01reg8` deleted `supports_deny_push` for. The bound is also why the OQ-01 split remains the maintainer's: the bullet is not cleanly one-done-one-not. |
| F-6 | `supports_deny_push` no longer exists, and a live test pins its absence | Plan `01reg8` removed the field, `CAP_DENY_PUSH`, and three unconsumed verdicts; `tests/test_host_capability_extension.py` class `DenyPushRemovedTests` asserts the field is absent from `dataclasses.fields(HostSandboxCapabilities)`, that `CAP_DENY_PUSH` is absent from `hsp.__all__`, and that `aw host capabilities` output contains no `deny_push` | This plan must NOT reintroduce the name. It touches no code path that test reads, which is deliberate: the name question belongs to the Order-02 sibling. |
| F-7 | Reintroducing a finding code is gated and expensive | `run_evidence.validate_finding_table` hard-fails `len(RUN_FINDING_CODES) != 12` with `RC-COUNT`; spec 4.2's own prose says "adding or removing a row here without amending that invariant makes the SHIPPED table report itself invalid at runtime"; backlog `oq05nc` says "Only after such a probe exists may a finding code be reintroduced in 4.2" | No finding code in this Set. The gate is not met: no probe exists yet, and after Order 02 the probe will prove port denial, not push denial. |
| F-8 | The measurement is host-specific by construction | Research `uq4y6q` host table: `bwrap`, `unshare` and `slirp4netns` are ALL installed, yet `unshare -Urn --map-root-user true` fails `write failed /proc/self/uid_map: Operation not permitted` | E-01 re-measures on the executing host rather than trusting `uq4y6q`'s numbers. This is the same measured counterexample that made the existing probes attempt-not-inspect. |

## Proposed changes (ordered, validatable)

1. Re-measure on the executing host and retain verbatim output (E-01). Nothing is edited until the
   evidence exists, because the whole point of this plan is that the record should follow a
   measurement and not the reverse.
2. Amend `host_sandbox_profile`'s module docstring so its network disclaimer matches the measurement
   (E-02). Docstring-only; no symbol, signature, or behavior changes.
3. Amend spec `25kzda` 5.2 with the measured position, the credential half in its BOUNDED form
   (F-5), and the named remaining gap (E-03). Additive prose; the requirement bullet and both tables
   are untouched, as is Section 6.1 limit 4, the spec's second push-denial site, which Order 03 owns.
4. Record provenance on both records with the owning tools (E-04).

## Deferred / out of scope (with reason)

- BUILDING the probe or the capability field: that is the Order-02 sibling's whole job, and keeping
  it out of this plan is what lets the spec amendment be reviewed on its own merits rather than
  bundled with a code change.
  - Carrier: pi3bk8
- HOST-GRANULAR network filtering (network namespace plus a filtering proxy), which is the only
  mechanism that would close the 443 gap F-3 and F-4 identify. It is unavailable on the measuring
  host today (F-8) and is the `1o4eif`-magnitude project `d07nz2` predicted.
  - Carrier: sv9ce4
- REINTRODUCING a `RUN-NO-PUSH`-shaped finding code. Gated by F-7 and explicitly by backlog
  `oq05nc`, and the gate is not met by this Set: after Order 02 the proven capability is port
  denial, not push denial. Binding a push-denial code to a port probe would be precisely the
  fail-OPEN inference `run_evidence`'s retirement comment forbids in writing.
  - Carrier-Declined: NOT WANTED, which is a decision rather than a deferral. The condition for
    reintroduction is stated in the spec and in backlog `oq05nc`, so a future reader can find it
    without anyone asserting that work is owed. Filing a carrier would misrepresent a deliberately
    unmet gate as pending work.
- CHANGING the spec's `- Status:` or its `- Blocks-Release: next`. This plan amends content only;
  status is owned by `aw specs` and the release gate is not this plan's to move.
  - Carrier-Declined: Out of scope by construction; nothing is owed.

## Scope check

- Over-scope: none. Every declared path is read or written by an E-item: the spec by E-03/E-04, the
  module docstring by E-02, the research doc by E-04. The research manifest files
  (`.aw/records/research/INDEX.json`, `INDEX.md`) are deliberately NOT declared even though E-04
  regenerates them: they are GITIGNORED generated artifacts (verified at review: `.aw/.gitignore`
  ignores `records/research/INDEX.json` and `records/research/INDEX.md` by anchored path), so
  declaring them would name paths the finalize scope gate can never see committed. This plan's OWN
  file is likewise undeclared and correctly so: `ipd_lifecycle._is_implicitly_allowed` grants
  `.aw/records/plans/**` as an implicit lifecycle allowance, so the plan moving through the lifecycle
  needs no declaration.
- Under-scope: none. E-01 writes nothing (its scripts are deliberately not retained, per `uq4y6q`),
  and no test file changes because no behavior changes. Confirmed by F-6: this plan touches no path
  `DenyPushRemovedTests` reads.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the actual summary line. The expectation is
  unchanged counts: this plan edits one docstring, one spec, and records. A docstring edit CAN break
  a test if one asserts on docstring text, so the run is what establishes it did not.
- `aw ipd lint` on this plan reports conforming.
- `aw check` reports no new violations, specifically none in the `release-gates` family (the spec
  carries `- Blocks-Release: next` and this plan does not move it).
- `aw research index --check` reports no drift after E-04.
- `aw sanitize --agent` reports no `fail` finding on the edited files: E-01's captured probe output is
  pasted into this plan and could carry host-identifying paths, so this is a real check and not a
  formality.

## Spec / documentation sync

- Spec `25kzda` is AMENDED by E-03 and is declared in `Scope-Paths`. WHY the amendment is warranted:
  5.2 currently asks whether a host can deny push-capable routes and withhold credentials, and the
  repository has never measured the first half while the second half is PARTLY enforced and bounded in
  three ways (F-5). The spec is the contract every other plan is reviewed against, so leaving it
  asserting an unmeasured requirement means every future reader re-derives the feasibility question,
  which is exactly what `4h7tt0` left behind and what backlog `oq05nc` exists to stop. THE AMENDMENT
  ONLY REDUCES RISK IF ITS CREDENTIAL SENTENCE IS BOUNDED: an unqualified "the credential half is
  shipped" written into an approved spec would be a new fail-OPEN claim, worse than the silence it
  replaces, which is why E-03 and V-03 both state the three bounds explicitly.
- `host_sandbox_profile`'s module docstring is the published-guarantees contract for this area
  (x03wgn Section 8 Phase 6.3 "publish its guarantees"), so a measured change to what the module
  could enforce belongs there and not only in the spec.
- No `docs/` page changes: `docs/runner-profiles.md` documents how hardened mode is REQUESTED, which
  this plan does not change.
- CHANGELOG: no entry. Nothing user-visible changes; the amendment is to internal contracts.

## Open questions

### OQ-01: Should spec 25kzda 5.2's single bullet be SPLIT into its two independent halves, given that the credential half is PARTLY shipped and the network half is not?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: wcbpqf
- Resolution or deferral rationale: NOT BLOCKING, because E-03 is written to be correct either way:
  it adds prose recording the credential half's BOUNDED state and that the network half is unmet,
  which makes the asymmetry readable without restructuring the list. The case FOR splitting is that
  5.2's list is a set of independent questions ("answers, independently, whether the host can"), and a
  single bullet joining two requirements with "and" can only ever be answered No, which loses the
  information that part of it is enforced. The case AGAINST is that `01reg8` deliberately preserved
  this bullet verbatim as this work's landing site and its review warned that narrowing it "would
  collide with backlog `oq05nc`", so re-editing its shape in the same breath as claiming to honor it
  invites the exact confusion that record was protecting against.
  THE QUESTION WAS RE-FRAMED AT REVIEW AND THE CASE FOR SPLITTING IS WEAKER THAN AUTHORED, which the
  maintainer should know before ruling. The title and rationale previously said the credential half
  "is shipped", and F-5 now measures that it is NOT, in three ways: only credential FILES are made
  inaccessible, no environment-carried credential is withheld at all
  (`runner_shared.pinned_child_env` is `os.environ.copy()` and the launcher pops only four internal
  keys), and the whole mechanism is opt-in and Linux-only. So the bullet is NOT one-done-one-not; it is
  one-partly-done-one-not, and splitting it would produce a second bullet whose honest answer is also
  a qualified No. Recommended: keep the bullet, add the bounded prose, and let the maintainer split it
  later if the Order-02 capability makes the asymmetry load-bearing. A reviewer who prefers the split
  should say so at review time, when it is a one-line change to E-03.

### OQ-02: Does amending an `approved` spec require re-approval?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: no. AGENTS.md states plainly
  that "Specs are living contracts, not immutable history: a plan that changes behavior a spec
  describes SHOULD carry the spec amendment in the same change", and the mechanism that makes it
  legitimate is declaring the spec in `Scope-Paths` (done) so both runners announce the declared
  spec edit before the run starts and reconcile it at finalize. Spec `25kzda`'s own
  `## Workflow history` records ten-plus prior amendments by plans while it stayed `approved`,
  including `01reg8`'s removal of `supports_deny_push` from this very area. So the established
  pattern is amend-and-record, not re-approve. This plan does not touch the spec's `- Status:`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: The three probe outputs pasted verbatim, each showing the command's own printed result lines. Probe (a) must show BOTH sides (an allowed connect succeeding AND a denied connect refused), because a one-sided result cannot distinguish an enforcing jail from a permissive one, which is the standard `_denial_checker_source` already sets. Probe (c) must show two DISTINCT ADDRESSES connecting on the SAME allowed port AND a third on a different port refused, which is what proves address-blindness rather than merely asserting it. Confirm in this evidence that the probes used LOOPBACK addresses and that the pasted output names no public host or external IP, per E-01: an evidence block whose decisive line depends on internet egress is not reproducible by the next reader. A host reporting ABI < 4 must paste that verbatim instead, and V-03 must then reflect the unavailable result rather than a universal claim.
  - Observed evidence: All three probes were executed entirely on loopback addresses on the host (reporting Landlock ABI 4). No public host or external IP was named or contacted.

Probe (a) verbatim output (two-sided: allowed connect succeeds, unallowed connect refused with PermissionError):
```text
abi: 4
allowed loopback port: 44825
create_ruleset fd: 7 errno: 0
add_rule(NET_PORT) rc: 0 errno: 0
restrict_self rc: 0 errno: 0
allowed connect ok: True
denied connect refused: True PermissionError(13, 'Permission denied')
RESULT: ENFORCED
```

Probe (b) verbatim output (combined ruleset enforcing both filesystem and network rights under one restrict_self):
```text
combined create_ruleset fd: 5 errno: 0
add PATH_BENEATH rc: 0
restrict rc: 0
fs allowed write: OK
fs denied write: EPERM -> ENFORCED
net unallowed: EPERM -> ENFORCED
```

Probe (c) verbatim output (address-blindness: allowed port admits connections to both 127.0.0.1 and 127.0.0.2 on the same port, while unallowed port on 127.0.0.3 is refused):
```text
add_rule rc: 0
net_port rule struct size: 16 (allowed_access u64 + port u64; NO address field)
restrict rc: 0
127.0.0.1:34593 CONNECTED
127.0.0.2:34593 CONNECTED
127.0.0.3:42525 EPERM -> KERNEL DENIED
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `git diff` of `agent_workflows/host_sandbox_profile.py` showing only docstring lines changed, plus the pasted `python3 -m pytest` summary line showing the suite still passes. Additionally paste a command proving the replaced sentence is gone AND that the survivors a live test reads are intact, for example `python3 -c "import agent_workflows.host_sandbox_profile as m; d=m.__doc__.lower(); print('stale:', 'network scoping and container isolation are out of scope' in d); print({t: t in d for t in ('read-only','driver','linux','git common','void')})"`. The first must print False and every token True; that second half is the real check, because `test_module_publishes_its_guarantees` asserts exactly those five tokens and a paragraph reflow is how one would silently vanish. DO NOT use a bare `count('out of scope')` as the evidence: the replacement KEEPS container isolation out of scope, so a nonzero count is the CORRECT result and the number alone distinguishes nothing. The diff must show NO change to any `def`, signature, or constant.
  - Observed evidence: `git diff agent_workflows/host_sandbox_profile.py`:
```diff
diff --git a/agent_workflows/host_sandbox_profile.py b/agent_workflows/host_sandbox_profile.py
index d1f10c373..f2e9a4e1b 100644
--- a/agent_workflows/host_sandbox_profile.py
+++ b/agent_workflows/host_sandbox_profile.py
@@ -33,7 +33,12 @@ worker (x03wgn Section 1: "A same-user process with arbitrary shell access canno
 cryptographically or filesystem-enforced from prompts, hooks, environment variables, or
 Python role checks alone."). This module is the OPT-IN complement for when "the driver is
 the only writer" must be literal. Hardened mode is NOT the default (Phase 6.4). Network
-scoping and container isolation are out of scope here.
+denial is measured and cannot separate a git remote from the model API on one port, so
+none is applied (network scoping is now measured rather than out of scope, and
+`handled_access_net` is already the second member of the ruleset attr
+`landlock_bootstrap_source` packs passing literal 0 today, so the reason no network rule
+is added is this port-granularity limit, not absence of a mechanism); container isolation
+remains out of scope here.

 PLATFORM AND PROBE THE GUARANTEE WAS VERIFIED ON. Linux ONLY. The mechanism is a ladder,
 and every rung is decided by an EXECUTED probe, never by inspection:
```
The diff shows changes strictly limited to docstring lines in `agent_workflows/host_sandbox_profile.py` with no changes to any `def`, signature, or constant.

Verification of docstring tokens:
```text
$ python3 -c "import agent_workflows.host_sandbox_profile as m; d=m.__doc__.lower(); print('stale:', 'network scoping and container isolation are out of scope' in d); print({t: t in d for t in ('read-only','driver','linux','git common','void')})"
stale: False
{'read-only': True, 'driver': True, 'linux': True, 'git common': True, 'void': True}
```

Full bare pytest summary line:
```text
4245 passed, 2 skipped, 3 warnings in 231.14s (0:03:51)
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `git diff` of the spec showing the added prose, and a grep proving the preserved artifacts are BYTE-UNCHANGED. RUN THE GREP AND STATE THE COUNTS, do not assert them: `grep -c 'deny push-capable' <spec>` must report **2** (measured at review), because the spec asserts push denial at TWO sites and only 5.2's bullet is this plan's; the SECOND hit is Section 6.1 limit 4 ("No-push and hook guarantees require control of execution", whose body reads "deny push-capable network/credentials"), which this plan MUST leave unchanged and which is owned by Order 03's audit per the orchestrator's Cross-IPD row. An audit-style report of one hit means the grep was wrong, not that the site is absent. Also grep `'deny push-capable network routes and withhold remote credentials'` (must be 1) and `'"deny_push"'` (must be 1, the 5.6 packet example), and confirm the 5.2 action-table row naming no-push enforcement is unchanged. The added prose must state all four of: ABI-4 denial is real, it is port-granular and address-blind, the credential half in its BOUNDED form (files inaccessible in hardened mode; NO environment-carried credential withheld; opt-in and Linux-only), and that no host reports the capability today (fail-closed). A diff that removes or narrows the bullet FAILS this item, since `01reg8` preserved it deliberately. A diff asserting an UNQUALIFIED "the credential half is shipped" ALSO FAILS, for the reason F-5 measures.
  - Observed evidence: `git diff .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`:
```diff
diff --git a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
index b42cea905..e365ff6c7 100644
--- a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
+++ b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
@@ -1167,6 +1167,8 @@ OpenCode and Antigravity are not assumed to have the same session, interception,

 THE PUSH-DENIAL ENTRY BELOW IS A REQUIREMENT ON A HOST, AND IT SURVIVED THE RETIREMENT OF SECTION 4.2's `RUN-NO-PUSH` CODE DELIBERATELY. The two are different artifacts and the distinction decides whether a reader is looking at a live rule or a withdrawn one: 4.2 was a REPORTING vocabulary that claimed preflight had PROVED push denial, and it was retired on 2026-09-08 because nothing proves it; this list asks whether a host CAN enforce it, and the honest answer for every host today is NO. The requirement asks what a host can enforce, no host can, and the list records the gap so a future probed capability has somewhere to land; which is why the requirement is kept rather than deleted. Removing the now-unenforced `supports_deny_push` flag and the verdicts nothing consumes was executed by plan `01reg8` (backlog `aagh7v`).

+MEASURED FEASIBILITY AND BOUNDS (plan `x2dwu5`): This push-denial requirement is now measured rather than merely aspirational. On Linux, kernel-level TCP denial is real at Landlock ABI 4 with two-sided proof (allowing an explicit loopback port while refusing connects to unallowed ports). However, Landlock network rules (`LANDLOCK_RULE_NET_PORT`) are strictly port-granular with no address field, so kernel port filtering alone cannot separate a git remote from the model API on TCP 443 without either permitting git pushes or severing model access. The remaining architectural gap for network push denial is host-granular filtering (such as a network namespace combined with a filtering proxy). On the credential half, protection is strictly bounded rather than complete: (i) in hardened mode, `oc_runipd._hardened_credential_paths` makes credential files inaccessible (`~/.ssh`, `~/.netrc`, `~/.git-credentials`, `~/.config/gh` and peers) via `build_sandbox_plan`'s `credential_paths`; (ii) no credential carried in the environment is withheld, because `runner_shared.pinned_child_env` copies `os.environ` wholesale and neither launcher clears it, allowing environment-carried tokens such as `GH_TOKEN`/`GITHUB_TOKEN` or a forwarded `SSH_AUTH_SOCK` to reach the worker regardless; and (iii) hardened mode is opt-in and Linux-only, so the default profile withholds nothing. Consequently, no host reports this capability today, and the descriptor's answer remains fail-closed.
+
 At minimum the descriptor answers, independently, whether the host can:
```

Grep counts on the spec verifying preserved artifacts:
```text
$ python3 -c "
spec = '.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md'
with open(spec) as f:
    text = f.read()
print('deny push-capable count:', text.count('deny push-capable'))
print('exact bullet count:', text.count('deny push-capable network routes and withhold remote credentials'))
print('deny_push packet count:', text.count('\"deny_push\"'))
"
deny push-capable count: 2
exact bullet count: 1
deny_push packet count: 1
```
The Section 5.2 action-table row naming no-push enforcement is unchanged:
`| Plan/spec review or IPD authoring | Isolated worktree, path policy, argv capture, no-push enforcement, commit gateway, hook-preserving commit, timeout/cancel, fresh verifier |`
The requirement bullet `- deny push-capable network routes and withhold remote credentials;` is preserved verbatim.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted output of `aw research index --check` reporting no drift, and the tail of the spec's `## Workflow history` showing the new dated record naming `x2dwu5`. FOR THE CONSUMED-BY LINK, paste the doc's own front-matter lines (`outcome:` and `consumed-by:`) or the doc's entry from `.aw/records/research/INDEX.json`, NOT `aw research find --id uq4y6q`: measured at review, that verb prints exactly `id6 <TAB> status <TAB> path <TAB> summary` (`research_index.run_find`) and carries NO outcome or consumed-by column in any mode including `--json`/`--agent`, so it CANNOT evidence this item and citing it would be an unfalsifiable check. Also paste `aw check` output showing no new violations and `aw sanitize --agent` exiting zero, since V-01's pasted probe output is the realistic leak vector in this plan.
  - Observed evidence: Output of `aw research index --check` (exited 0, reporting no drift for uq4y6q):
```text
$ aw research index --check
EXIT: 0
```

Spec `25kzda` workflow history tail:
```markdown
- 2026-10-01 note (aw specs): AMENDED (plan x2dwu5, backlog oq05nc): Section 5.2 amended in place to record measured Landlock ABI 4 TCP network denial feasibility (proven two-sided on loopback) and its port-granularity limit (no address field, cannot separate git push from model API on TCP 443), and to record the bounded credential withholding status (files inaccessible under opt-in hardened mode, no environment-carried credentials withheld; fail-closed descriptor answer maintained)
```

Consumed-by provenance from `20260929-denypush-00-uq4y6q-landlock-network-push-denial-feasibility.findings.md` front-matter:
```yaml
outcome: adopted
summary: Measured feasibility of OS-level push denial via Landlock ABI4 network rules: two-sided denial proven, but rules are port-only with no address field
consumed-by: [x2dwu5]
```

And entry from `.aw/records/research/INDEX.json`:
```json
{
  "consumed_by": [
    "x2dwu5"
  ],
  "created": "20260929",
  "date": "20260929",
  "has_body": true,
  "id6": "uq4y6q",
  "kind": "findings",
  "model": "",
  "order": "00",
  "outcome": "adopted",
  "path": "20260929-denypush-00-uq4y6q-landlock-network-push-denial-feasibility.findings.md",
  "priority": "low",
  "set_id": "denypush",
  "status": "todo",
  "summary": "Measured feasibility of OS-level push denial via Landlock ABI4 network rules: two-sided denial proven, but rules are port-only with no address field",
  "topic": [
    "sandbox",
    "security",
    "landlock",
    "push-denial"
  ]
}
```

`aw sanitize --agent` output (exited 0 with no leaks):
```text
$ aw sanitize --agent
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
```

`aw check` confirmed no new release-gates or blocker violations introduced by this change.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is records-only by design: it produces a measurement and writes it into the two contracts
that currently assert or disclaim push denial. It adds no probe, no capability field, and no finding
code, so it cannot make any host report a capability it does not have. That separation is deliberate,
because the failure this whole area guards against is a record claiming enforcement that does not
exist, and the cheapest way to re-create it would be to bundle a spec claim with a code change and
review them as one thing.

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`,
never `git add -A`, and never push. This is a SHARED CHECKOUT: verify the staged set with
`git diff --cached --name-only` before committing and unstage anything that is not yours, and re-verify
after any failed raw commit attempt. Run the suite BARE as `python3 -m pytest` and PASTE ITS ACTUAL
SUMMARY LINE; a summary you did not produce is not evidence, and the same hard-MUST governs every
pasted probe output in V-01, which is this plan's primary deliverable.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). The
three `- Scope-Paths:` entries are the whole surface. THREE NEGATIVE CONSTRAINTS CARRY REAL WEIGHT.
FIRST, do NOT add a probe, a capability field, a `probe_notes` entry, or a finding code: those are
Order 02's (`pi3bk8`) deliverables and F-6/F-7 record why doing them here would either break
`DenyPushRemovedTests` or trip `run_evidence.validate_finding_table`'s `RC-COUNT`. SECOND, do NOT
change any `def`, signature, or constant in `host_sandbox_profile.py`: E-02 is a docstring edit and
V-02's diff check fails otherwise. THIRD, do NOT touch spec `25kzda` Section 6.1 limit 4, the spec's
SECOND push-denial site: the orchestrator `l4vw9o` resolved it as DO-NOT-AMEND and assigned the
recorded judgement to Order 03, so editing it here would both duplicate that decision and break the
byte-unchanged invariant Order 03 re-greps at Set end. An out-of-scope edit that turns out to be
necessary is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a
declared-but-unmodified path needs a `--scope-ack`; neither is a reason to stop.

LIFECYCLE TRANSITION. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete observed evidence.
Reaching `executed/` is UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL: under `aw oc run` /
`aw agy run` the RUNNER owns the terminal transition and finalize, so do NOT invoke `aw ipd finalize`
yourself in a runner-driven execution; a HAND execution invokes it
(`aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`). Never hand-edit
`- Status:` and never hand-roll a `git mv` into `executed/`, which would skip the pre-transition
checkpoint. Backlog `oq05nc` is already `graduated`; this plan must NOT set it `done`.
