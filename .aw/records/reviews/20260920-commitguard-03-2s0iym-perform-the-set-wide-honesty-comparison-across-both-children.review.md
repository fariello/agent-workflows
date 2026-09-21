# Review: perform the Set-wide honesty comparison across both children, child 2s0iym (Set commitguard)

- Subject-Id: 2s0iym
- Subject-Type: ipd
- Reviewed-At: 2026-09-21
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed in an isolated lane worktree at HEAD `cd2e6adb`. `aw ipd lint --phase author` CONFORMING
before semantic review and `--phase review-finalize` CONFORMING after revision, so nothing found here
is structural.

DISCLOSURE: the same agent/model authored this plan, so this is a SELF-REVIEW. Its value therefore
rests on RUNNING the plan's own mechanisms rather than re-reading its prose. Six things were executed
rather than inspected, and five of them produced findings: `merge_aw_block` was CALLED twice (once with
a sentinel appended to the desired section, once against an on-disk copy carrying an injected
`HAND-EDITED` string), which produced the one error-class finding; `pre-commit run --all-files` was run
end to end; the bare suite was run; `tests/test_shared_checkout_contract.py` was run AND its comparison
was re-performed against a deliberately corrupted copy to prove non-vacuity; `engine.py`'s installer
set was enumerated; and the installed-hook path was resolved both ways in a lane worktree.

THE PLAN'S CORE THESIS IS SOUND AND ITS PREMISES REPRODUCE. The orchestrator-coverage problem it
exists to close is real: `ao1rb7` E-03 is a genuine cross-child comparison, and
`ipd_lifecycle.ROLLUP_OMITTED_GATES["pre-transition-ev-checkpoint"]` (`:2989-2999`) confirms verbatim
that retirement skips the E/V checkpoint on the premise that "an orchestrator's items are performed by
NOBODY". The parent has ALREADY been updated to carry this child (`ao1rb7:63` child-table row, `:65`
resolving OQ-02 to option (b)), so the coverage claim is not aspirational. The opt-in partition
re-measures EXACTLY as recorded (0/0 wired, 3/3/2/2 opt-in), `.pre-commit-config.yaml:17` and `:23` are
unchanged, `pre-push` is correctly absent, and `engine.py:1320` still carries the
"immune to this by construction" sentence, so E-02 has a live subject. No finding below disputes the
plan's shape; all ten concern whether its INSTRUCTIONS can actually be carried out as written.

THE ONE SERIOUS FINDING IS THAT A VERIFICATION METHOD COULD NOT DETECT ITS OWN SUBJECT. E-04's check 3
asked the executor to regenerate the managed block and diff it, but in this repository that route is
drift-preserved away: the manifest's recorded hash for `AGENTS.md#aw:pointer` disagrees with disk, so
`_apply_section_consent` takes the user-drift branch and returns the ON-DISK body. An injected
`HAND-EDITED` string SURVIVED a full `merge_aw_block` round trip while the call reported
`action='refreshed'`. A plan whose entire purpose is to catch prose that overclaims what a mechanism
does would have shipped a check that claims to prove no-drift and cannot. It now mandates the shipped
assertion, which bypasses the consent layer and which I verified is non-vacuous.

FOUR FINDINGS WOULD HAVE MADE AN EXECUTOR FABRICATE OR MISREAD EVIDENCE. PR-002's "three sites per
gate" was literally unsatisfiable for the two wired gates (no installer exists for them), so an
obedient executor would have invented two table rows. PR-003 pre-authorized ignoring a `ruff-format`
failure that does not exist, which would have licensed ignoring a real one. PR-005 named
`ipd-executed-gate` as a hook id when it is an `entry:` verb, a trap the repo's own test file
documents at `tests/test_gate_wiring.py:172`. PR-006's `ls .git/hooks` fails outright in the lane
worktree this plan will run in, and reporting that failure as proof of `pre-push` absence would
conflate "absent" with "unreadable".

PR-007 IS THE ONE MOST LIKELY TO STRAND THE PLAN IN PRACTICE. The plan's own predicted outcome is a
ZERO-DIFF run, and `aw ipd finalize` fails closed on precisely that shape: every declared-but-unmodified
`Scope-Paths` entry demands a `--scope-ack`. An executor hitting that refusal with no forewarning has an
obvious bad escape available, namely manufacturing a cosmetic edit so a path looks touched, which would
corrupt the very record this plan exists to produce. E-03 now names the acks explicitly and forbids the
escape.

SCOPE: only this plan was a candidate. Read as evidence: `agent_workflows/engine.py`
(`_apply_section_consent` `:1792-1828`, `merge_aw_block` `:1702-1760`, the four installers `:5429`,
`:5528`, `:5677`, `:5693`, the contract paragraphs `:1305-1330`), `agent_workflows/ipd_lifecycle.py`
(`ROLLUP_OMITTED_GATES` `:2989`, `_reconcile_scope` `:2470-2545`, the scope audit `:2100-2126`, the
refusal `:3450-3464`), `agent_workflows/runner_shared.py` (`:14195-14221`),
`agent_workflows/git_commit_helper.py` (`offer_commit` `:407-437`),
`agent_workflows/manifest.py` via `engine.manifest_mod`, `agent_workflows/hooks/` (all six gate
modules), `.pre-commit-config.yaml` (`:1-100`), `AGENTS.md`, `.aw/system/managed-sections.json`,
`tests/test_gate_wiring.py`, `tests/test_shared_checkout_contract.py:162-171`,
`tests/test_turn_bounds.py:295-315`, sibling plans `ao1rb7`, `y9vpvv` and `kbqpkn`, and backlog
`wjl471`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing and verification | `agent_workflows/engine.py:1792`; `.aw/system/managed-sections.json` | E-04 check 3's `merge_aw_block` no-diff method CANNOT DETECT DRIFT here. The manifest records `AGENTS.md#aw:pointer` as `a9deb5a1...` while the live body hashes `9c9aa08f...`, so `_apply_section_consent` preserves the on-disk body. Measured twice: a sentinel appended to the desired section was ABSENT from the output, and an injected `HAND-EDITED` string SURVIVED, both with `action='refreshed'`. The check would have reported a false pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Check 3 rewritten to mandate `tests/test_shared_checkout_contract.py::NoDriftTests::test_repo_agents_block_equals_generated`, which compares against `agents_managed_block` directly. Verified passing (`10 passed in 0.17s`) AND non-vacuous (the same comparison rejects a corrupted copy). V-04 now refuses a `merge_aw_block` diff as the proof. |
| PR-002 | HIGH | IN-SCOPE | G. Plan executability | `agent_workflows/engine.py:5429,5528,5677,5693` | E-01's "three sites per gate ... for the four opt-in gates and the two wired ones" is UNSATISFIABLE: site (c), the `engine.create_*_hook` docstring, exists only for the four opt-in gates. There is no installer for `executed_transition_gate` or `status_untooled_gate`. An executor obeying the text would fabricate two rows. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 corrected to 3 sites per opt-in gate, 2 per wired gate, plus the two `.pre-commit-config.yaml` comment-block disclosures (`:70-71`, `:75-77`) which are where a wired gate's honest limit actually lives. V-01 now FAILS a table carrying a third row for a wired gate. Also noted `hooks/__init__.py` is not a gate module. |
| PR-003 | HIGH | IN-SCOPE | E. Testing and verification | `pre-commit run --all-files`; `.pre-commit-config.yaml:43` | The validation section pre-authorized a "known pre-existing `ruff-format` failure on `tests/test_cli_output_docs_rollout.py`". It DOES NOT EXIST: all ten hooks pass and that file is "1 file already formatted". Pre-authorizing an absent failure licenses ignoring a real one the executor introduces. The 92-file ambient `ruff format --check` result is a version artifact (ambient 0.16.3 vs pinned `rev: v0.4.4` plus an `exclude:`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Claim removed and replaced with the measured all-pass result, an instruction to judge by RUNNING THE HOOK rather than ambient `ruff`, and an explicit statement that a `ruff-format` failure is now probably the executor's own. |
| PR-004 | MEDIUM | UNDER-SCOPE | G. Plan executability | `.aw/records/plans/pending/...y9vpvv...ipd.md:196`; `agent_workflows/oc_runipd.py:3261` | E-02 read Order 02's half as `engine.py` + `AGENTS.md` only, but `y9vpvv` OQ-03 was resolved to shape (a) AND extended to the four driver prompts, so Order 02 ships prose in the runner files too. A comparison omitting them is not Set-wide. `y9vpvv`'s cited line numbers are STALE; the strings live at `oc_runipd.py:3261`, `agy_runipd.py:2085`, `runner_shared.py:14781`, `:14874`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now reads the four sites, located BY STRING not by line number, and V-02 demands them with real `file:line` and a verdict each. Edit authority deliberately withheld (those paths stay out of `Scope-Paths`); a defect there is reported and routed to E-03's corrective-IPD branch, recorded under Deferred. |
| PR-005 | MEDIUM | IN-SCOPE | A. Correctness | `.pre-commit-config.yaml:78,80,93`; `tests/test_gate_wiring.py:172` | E-04 check 2 named `ipd-executed-gate` as a registered hook id "at line 80". It is the `entry:` VERB at `:80`; the ID is `ipd-executed-transition-gate` at `:78`. The repo's own test file documents this exact trap. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Check 2 now states both ids with correct line numbers and distinguishes id from verb, citing `test_gate_wiring.py:172`. |
| PR-006 | MEDIUM | IN-SCOPE | A. Correctness | measured: `ls .git/hooks` -> exit 2 in this lane | E-04 and the plan's history read the installed-hook set from `.git/hooks`, which FAILS in a lane worktree ("Not a directory": `.git` is a file). Reporting that failure as evidence that no `pre-push` hook is installed conflates "absent" with "unreadable", turning an unverified claim into an apparently proven one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 check 1 now mandates `"$(git rev-parse --git-common-dir)/hooks"` (measuring one `pre-commit`) and explicitly forbids reporting the `.git/hooks` failure as proof. V-04 requires that form. |
| PR-007 | MEDIUM | UNDER-SCOPE | G. Plan executability | `agent_workflows/ipd_lifecycle.py:2108-2112,3461-3464` | The plan's OWN expected outcome is a zero-diff run, and `aw ipd finalize` fails closed on exactly that: each declared-but-unmodified `Scope-Paths` entry demands a `--scope-ack`. Unwarned, an executor hitting the refusal may manufacture a cosmetic edit so a path looks touched, corrupting the record this plan exists to produce. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now names the five `--scope-ack` flags, states the refusal is not a defect, and forbids manufacturing an edit to escape it. Noted that a runner auto-acknowledges (`runner_shared.py:14215-14219`) so this bites the hand-finalize path. |
| PR-008 | MEDIUM | IN-SCOPE | E. Testing and verification | measured bare suite; `tests/test_turn_bounds.py:310` | The validation section told the executor to measure its own baseline but implied the environmental failure would be the `test_reporting_contract.py` one both siblings cite. That did NOT reproduce. The actual lane baseline is `1 failed, 7942 passed, 3 skipped, 2 xfailed`, failing `test_turn_bounds.py::...IS_isolation_scoped` because `OPENCODE_CONFIG_CONTENT` is in the agent session's ambient env. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Measured baseline recorded verbatim with the cause and a note that it reproduces standalone and is unreachable from this plan's fence. Added to Deferred with a carrier declination rather than left as an implied executor task. |
| PR-009 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | plan gate section | The gate carried the commit/never-push and finalize rules but NOT a scope fence stated as a declaration, NOT the "paste the ACTUAL runner output" honesty rule, and it instructed `aw ipd finalize` UNCONDITIONALLY, which is wrong when a runner owns begin/finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now states the fence as a declaration (out-of-scope edits are made then justified, not halted; the one legitimate stop is the spec-contradiction case the spec-sync section names), adds the paste-actual-output hard MUST, and makes finalize ownership conditional on whether a runner is driving. |
| PR-010 | LOW | IN-SCOPE | A. Correctness | `manifest_mod.hash_content` over the parsed pointer body | The `8baff639...` live-hash figure `y9vpvv` E-07 and its review both record is STALE; the section now hashes `9c9aa08f...`. The DRIFT is still live so `y9vpvv` E-07 is still owed, but a plan copying the number would cite a false measurement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-16 in the plan with the correct hash, and the Deferred entry for the manifest reconciliation states that only the cited number is stale while the obligation stands. |
| PR-011 | LOW | IN-SCOPE | F. KISS and honest documentation | `agent_workflows/engine.py:1305-1324`; `git_commit_helper.py:407` | E-02 demanded a verdict on "immune to this by construction" but gave no criterion, inviting a false finding: the obvious reading (immune to hook bypass) is wrong. "This" refers to the preceding paragraph's INDEX-POLLUTION hazard, so the claim is narrow and probably true as scoped. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now names the antecedent, the mechanism to verify it against, and explicit falsification criteria; V-02 requires the verdict to name the antecedent and requires a demonstration for an "inaccurate" verdict. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should E-04 check 3 prove no-drift, given the `merge_aw_block` route is blind here? | Mandate `tests/test_shared_checkout_contract.py::NoDriftTests::test_repo_agents_block_equals_generated` and forbid the `merge_aw_block` diff as the proof. | (a) Have this plan reconcile the manifest first, which duplicates `y9vpvv` E-07 and writes an undeclared path; (b) keep the diff and add a caveat, which leaves a false-pass method in a plan about false claims. | `tests/test_shared_checkout_contract.py:165-170` compares against `agents_managed_block` directly, bypassing consent; verified passing and non-vacuous at review. `y9vpvv:82` (E-07) already owns the manifest fix. | yes |
| D-2 | Are the four driver-prompt files part of Order 02's half, and may this plan edit them? | In E-02's READING subject, but NOT in `Scope-Paths`: judge and report, never edit. | (a) Declare them and allow edits, which widens a read-and-judge plan into four runner files a terminal sibling owns; (b) exclude them entirely, which leaves Order 02's half half-read and breaks E-03's Set-wide claim. | `y9vpvv:196` records the maintainer extending the mandate to the four prompts, so they ARE Order 02's shipped prose; AGENTS.md forbids adding commits to an executed plan, so editing them from here needs a corrective IPD. | yes |
| D-3 | Is the `engine.py:1320` "immune by construction" sentence a Set violation? | Not pre-judged. E-02 now states the narrow antecedent and both verdict criteria, leaving the call to the executor with evidence. | (a) Declare it accurate at review, which performs E-02's work and removes the check; (b) declare it a violation, which is the false finding the wide reading produces. | `engine.py:1320-1324` scopes "this" to the index-pollution paragraph `:1305-1319`; `git_commit_helper.py:407` ("ONLY these are ever staged") supports the narrow claim. | yes |
| D-4 | Does the plan's expected zero-diff outcome need a finalize accommodation? | Yes: name the five `--scope-ack` flags in E-03 and forbid manufacturing an edit. | (a) Narrow `Scope-Paths` to avoid the acks, which would remove the edit authority E-03 needs for a correction it may find; (b) say nothing, which leaves the refusal to be discovered at finalize with a bad escape available. | `ipd_lifecycle.py:3461-3464` refuses headless without an ack per untouched declared path, computed at `:2108-2112`; `runner_shared.py:14215-14219` auto-acks only under a runner. | yes |
| D-5 | Should the `test_turn_bounds.py` failure be treated as this plan's problem? | No: record it as the measured baseline with its ambient-env cause; decline a carrier. | (a) Add an E-item to fix it, which is out of scope and would be fixing another surface entirely; (b) leave it unmentioned, which would make the executor chase it. | Reproduced standalone; `tests/test_turn_bounds.py:310` asserts on `OPENCODE_CONFIG_CONTENT`, which is present in this agent session's environment. Nothing in the plan's fence touches it. | yes |
| D-6 | Is the plan's overall approach sound, or does the coverage-gate premise need re-litigating? | Sound; no REPLAN. Every finding is an instruction-level repair. | REPLAN, rejected because the cross-child comparison is genuine orchestration work no sibling can perform and the parent already carries this child. | `ipd_lifecycle.py:2989-2999` confirms retirement skips the E/V checkpoint; `ao1rb7:63,65` already carries the child row and resolves OQ-02 to option (b). | yes |

No `Reversible: no` decision was made in this round, so no escalation under the irreversible-decision
rule is owed. The plan's single open question (OQ-01) is `Blocking: no` and was NARROWED rather than
resolved: its driver-prompt half is now settled by D-2, and what remains is a policy preference on the
five declared paths that only the maintainer can tighten. No finding was left `OPEN` or `DEFERRED`, so
no finding requires escalation as a blocking question under the gate threshold (`HIGH`).
