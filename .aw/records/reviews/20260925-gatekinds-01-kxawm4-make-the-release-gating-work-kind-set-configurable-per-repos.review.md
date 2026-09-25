# Review: Make the release-gating work-kind set configurable per repository

- Subject-Id: kxawm4
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `2a3b7ec5`, in the review sweep lane. The target plan was committed and unchanged (the
lane's rev-4 materialized copy is byte-identical to the tracked file), so the pre-review snapshot was
correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent` reported `clean`
with 0 findings before review; `--phase review-finalize --agent` reports `clean` with 0 findings after
every edit below, including the E/V renumbering.

THIS IS THE STRONGEST-AUTHORED PLAN OF THIS SWEEP AND ITS SURVEY IS ACCURATE. I re-derived all four of its
findings independently and every one holds: no gating-kind config key exists, `GATE_DEFAULT_KINDS` has
exactly two consumers, the AGENTS.md sentence is hand-maintained with no generator, and the only other
"unbuilt" statement is the comment above the constant. The `review_findings_gate` precedent it copies is
the right one and its cited properties check out (object form, bare-string tolerance, never raises,
deliberately absent from `CONFIG_SCHEMA` for the documented round-trip reason), as does the
warn-and-fall-back ruling quoted verbatim in `policy_retry_budget`'s section comment. All three
`decide_gate_default` call sites pass `repo_root`, so E-03 needs no signature changes, and `config.py`
imports only stdlib, which makes its no-`backlog`-import caution a real constraint rather than a style
preference. The findings are therefore about completeness and evidence, not about the approach.

F-3 DESERVES SPECIFIC CREDIT AND I RE-PROVED IT RATHER THAN ACCEPTING IT, because the opposite belief is a
measured hazard in this repository. The plan asserts the AGENTS.md text is hand-maintained and cites the
sibling `zqs0px` review, which retracted the identical "emitted from engine.py" claim with four proofs. I
confirmed the boundary myself: the managed block opens at `AGENTS.md:3` and closes at `:123`, the target
sentence sits at `:165`, and `grep -c "configurable per repository" agent_workflows/engine.py` is `0`. So
editing AGENTS.md directly is correct, and following the opposite instruction would export this
repository's release policy to every adopter. One correction to that earlier review's safeguard: the
parity assertion it named in `tests/test_shared_checkout_contract.py` no longer exists (the file was
deleted in `19313eed`'s suite trim), so the marker check is the live guard rather than a test. E-07 now
carries a STOP condition keyed on the marker rather than on trust.

PR-301 IS THE FINDING WITH THE MOST SURFACE: BOTH CONSUMER ITEMS NAME FEWER HARDCODED KIND STRINGS THAN
EXIST, and the leftovers are text a human or agent actually reads. E-03 said "the two notice strings that
say 'this bug'"; there are THREE in `decide_gate_default` (the `done`/`parked` skip notice, the
unresolvable-`next` notice, and the success notice), and the success notice additionally carries "every
live bug gates the next release" and "an ungated bug". E-04 said "the detail text"; the drift record
hardcodes the kind in TWO fields, `detail` and `observed`. Beyond those, `decide_gate_default`'s docstring
numbered condition 1 states "ONLY `GATE_DEFAULT_KINDS` (today `bug` alone) is defaulted ... `security` is
deliberately excluded", which becomes FALSE the moment the key can widen the set, and
`check_live_bug_gate`'s docstring first line plus its `RuleSpec` comment both assert `Work-Kind: bug`
specifically. None of that wording is pinned by any test (I grepped), so generalizing is safe; leaving it
is how a feature ships with documentation that contradicts it. I also required the docstring edit to
PRESERVE the recorded reason the default stays `bug` alone, because that reason (the maintainer measured
agent security classifications in this repository to be overstated) is the justification for the default
itself and deleting it with the stale sentence would lose it.

PR-302: THE `RuleSpec` DETERMINISM TAG MUST NOT CHANGE, and the plan never addressed it. This is the kind
of omission that produces a wrong edit by well-meaning inference: `check.live-bug-ungated` is tagged
`("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07")`, and "this rule now reads a config file"
looks like it should become `DET_HEURISTIC`. It must not. `DET_DETERMINISTIC` is defined as how the
finding's truth was reached, and the rule's own comment says "a literal `- Work-Kind:` / `- Status:` /
`- Blocks-Release:` token test ... No inference". Reading a committed key is still no inference.
Downgrading the tag would weaken a shipped catalog claim for no reason, so E-05 now states it explicitly.

PR-303 IS A VALIDATION THAT CANNOT FAIL. V-01 required `grep -c release_gate_work_kinds
agent_workflows/project_schema.py` to be `0`. That module is not in `Scope-Paths` and this plan never
edits it, so the count is zero regardless of what E-01 does. The property actually worth pinning, matching
the `review_findings_gate` precedent the plan cites, is that the key stays out of `config.CONFIG_SCHEMA`;
V-01 now asserts that and keeps the old grep only as a secondary no-edit check. (This is the second
occurrence of this exact pattern in this sweep, on a different plan and a different module, which is why
it is worth naming rather than quietly fixing.)

PR-304 fixes a method name that would have read as a failed round-trip. E-02 requires asserting the key
"round-trips through `project_schema.parse_portable_policy`". It does, and I verified it: the key lands in
`unknown_fields` and comes back verbatim as `{'kinds': ['bug', 'security']}`. But the serializer is
`to_dict()`, not `as_dict()`, and my first probe called `as_dict`, found no method, and reported
`round-trips back? False`. An executor making the same slip would conclude the mechanism the
"not in CONFIG_SCHEMA" decision depends on is broken, and could reasonably respond by registering the key
in the schema, which is the opposite of the precedent. The correct method is now named in the item.

PR-305 puts the vocabulary-duplication choice on evidence instead of leaving it open. E-01 offers "pass
the vocabulary in, or define the legal set in `config` with a comment". Both are defensible and the
repository has a precedent for the second that is worth knowing before choosing it:
`config.REVIEW_GATE_THRESHOLDS = ("medium","high","blocker","off")` IS a hand-maintained partial copy of
`review_findings.SEVERITIES = ("low","medium","high","blocker")`, cited as its source in the docstring. So
a literal copy would be precedented AND would inherit that precedent's wart, while injection avoids a
second divergence point for a vocabulary whose documented home is `.aw/records/backlog/README.md` plus
`backlog.KINDS`. I recommended injection, allowed the copy with a sourced comment, and recorded why.

PR-306 strengthens a Deferred claim whose reason was stale. The plan says no existing live `security` item
becomes flagged because "this repo keeps the default", which is true but does not establish the stronger
and more useful fact. I drove it: with the set forced to `{bug, security}`, `check_live_bug_gate` returns
ZERO drifts on this tree, because the only live `security` item (`c4yixg`, `graduated`) already carries
`- Blocks-Release: next`. Note `0htqmm` cites `754txs` as the live ungated `security` item and it is now
`- Status: done`, so the item's own example has expired. I also confirmed CI cannot break from a widened
gate anywhere: `aw check release-gates` runs ADVISORY in `tests.yml`, piped to a `::warning::`.

PR-307 resolves OQ-02 rather than spending a maintainer turn, and records F-10 as a pre-existing gap. On
OQ-02, the repository's own recorded posture settles it: `config.py` quotes the 2026-09-10 ruling verbatim
("FALL BACK TO THE DEFAULT AND EMIT A VISIBLE WARNING NAMING THE KEY AND THE BAD VALUE") whose rationale
is that a shared tracked file must not break every run over one typo. Both candidate behaviors warn, so
the only question is how much operator intent survives, and dropping the bad name keeps the valid gates.
`findings_gate_threshold` falls back wholesale but reads a single scalar where there is no partial answer,
so it does not apply to a list. On F-10: the AGENTS.md rule governs a "backlog item, spec, or plan" while
`check_live_bug_gate` iterates `backlog._iter_items` only, so specs and plans are unchecked. That gap
predates this plan and the plan's Scope check names it honestly; I recorded the evidence, deferred closing
it with a reason, and added an instruction that E-07 must NOT narrow the rule's wording to match the
checker, since the rule legitimately governs all three carriers.

Two IPD-Z602 size advisories appeared from my own added clarifications on E-03 and E-05, which I resolved
by splitting each into the code change and the text/test change rather than by trimming the evidence. That
is the better shape anyway: the membership swap and the prose correction are independently verifiable.

Backlog `0htqmm` carries no `- Blocks-Release:`, so no gate is inherited; the gate section says so.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | MEDIUM | UNDER-SCOPE | A. Correctness / F. Honest documentation (stale text contradicting shipped behavior) | `grep -rn "on this bug\|Work-Kind: bug" agent_workflows/backlog.py agent_workflows/check_engine.py` -> three `backlog` notices (skip, unresolvable-`next`, success, the last also carrying "every live bug gates the next release" and "an ungated bug"), two `check_engine` drift fields (`detail`, `observed`), the `check_live_bug_gate` docstring first line, and the `RuleSpec` comment; `decide_gate_default` docstring condition 1 "ONLY `GATE_DEFAULT_KINDS` (today `bug` alone) is defaulted ... `security` is deliberately excluded"; `grep -rn "on this bug\|every live bug" tests/` -> nothing | BOTH CONSUMER ITEMS UNDERCOUNT THE HARDCODED KIND STRINGS, AND THE LEFTOVERS ARE USER-FACING. E-03 names two notices where three exist; E-04 names one drift field where two do. Neither touches the two docstrings or the `RuleSpec` comment that assert `bug` alone is gated, which become FALSE once the key can widen the set. An executor following the items literally ships a configurable gate whose own notices tell a `security` item it is a bug and whose docstring says the feature does not exist. | C:Low; U:Medium (a wrong kind named in the operator's notice); S:Low; F:Low; Overall:Low | FIXED | E-04 (new) owns the `backlog.py` text: all three notices, the docstring condition, and the constant's comment, with an instruction to PRESERVE the recorded reason the default stays `bug` alone. E-05 owns the `check_engine.py` text: both drift fields, the docstring first line, the `RuleSpec` comment. F-6 records the census; V-04 and V-05 require the generalized text pasted. |
| PR-302 | MEDIUM | UNDER-SCOPE | C. Architecture (a catalog claim a well-meaning inference would weaken) | `"check.live-bug-ungated": RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07")`; `DET_DETERMINISTIC = "deterministic"` under "Determinism tags ... how a finding's truth was reached"; the rule's own comment "a literal ... token test ... No inference" | THE PLAN NEVER SAYS WHETHER THE DETERMINISM TAG MUST CHANGE, AND THE OBVIOUS INFERENCE IS WRONG. Routing an `error`-severity, `DET_DETERMINISTIC` rule through a config read looks like it should become `DET_HEURISTIC`. It must not: the tag records that truth was reached without inference, and a literal key read is still a literal test. An unnecessary downgrade would weaken a shipped catalog claim, and the plan gives an executor nothing to decide it with. | C:Low; U:Low; S:Low; F:Medium (a weakened assurance claim on a release-gating rule); Overall:Low | FIXED | E-05 states the tuple stays `("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07")` and forbids the downgrade, with the definition quoted; F-8 records the evidence; V-05 requires the `RuleSpec` line pasted unchanged. |
| PR-303 | MEDIUM | IN-SCOPE | E. Testing (an assertion that passes regardless) | `agent_workflows/project_schema.py` is not in `- Scope-Paths:` and is never edited by this plan, so `grep -c release_gate_work_kinds` there is `0` before and after; the registry the precedent concerns is `config.CONFIG_SCHEMA` | V-01 ASSERTS AGAINST A MODULE THIS PLAN NEVER TOUCHES. "`grep -c release_gate_work_kinds agent_workflows/project_schema.py` = 0 (not registered)" conflates two different things: the key must be absent from `config.CONFIG_SCHEMA` (the documented precedent), not from `project_schema.py` (which holds no config keys at all and would report zero whatever E-01 did). The property meant to be pinned goes unchecked. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now asserts `[k for k in config.CONFIG_SCHEMA if 'release_gate' in k] == []`, keeps the old grep only as a secondary no-edit check, and states why it proved nothing; E-01 records the verified precedent. |
| PR-304 | LOW | IN-SCOPE | E. Testing (a correct claim an executor will mis-verify) | Driven: `parse_portable_policy({...,"release_gate_work_kinds":{"kinds":["bug","security"]}})` -> `unknown_fields == {'release_gate_work_kinds': {'kinds': ['bug','security']}}` and `.to_dict()` returns it verbatim; `ProjectPolicySchema` exposes `to_dict`, NOT `as_dict` | THE ROUND-TRIP IS REAL BUT EASY TO "DISPROVE" BY CALLING THE WRONG METHOD. E-02 names the parse function but not the serializer. I called `as_dict` first, got no method, and read `round-trips back? False`. An executor making the same slip would conclude the mechanism the not-in-schema decision depends on is broken, and the natural remedy would be to register the key in `CONFIG_SCHEMA`, inverting the precedent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names `to_dict` explicitly, records that a probe calling `as_dict` reads as a failed round-trip and that this happened at review; V-02 requires the assertion through `to_dict`; a conventions bullet records the serializer and the `unknown_fields` mechanism. |
| PR-305 | LOW | IN-SCOPE | C. Architecture / F. KISS (an open implementation choice with an unstated precedent) | `config.py` imports only stdlib; `backlog` and `status_set` import `config` locally inside functions; `config.REVIEW_GATE_THRESHOLDS = ("medium","high","blocker","off")` versus `review_findings.SEVERITIES = ("low","medium","high","blocker")`, the former citing the latter as its source; `backlog.KINDS` plus `.aw/records/backlog/README.md` as the vocabulary's documented home | E-01 LEAVES THE VOCABULARY CHOICE OPEN WITHOUT THE EVIDENCE NEEDED TO MAKE IT. It offers injection or a config-local copy. The repository already has a precedent for the copy (`REVIEW_GATE_THRESHOLDS` duplicates `review_findings.SEVERITIES`), which both legitimizes the option and shows its cost: a second place for one vocabulary to drift. Without that stated, the choice is made by whichever is easier to type. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 recommends INJECTION with the reason (the caller already imports `config` locally, so the cycle is the caller's to avoid), permits the copy only with a comment naming `backlog.KINDS` and the precedent, and records the precedent's wart; V-01 requires the chosen route to be stated; two conventions bullets added. |
| PR-306 | LOW | IN-SCOPE | D. Anti-regression (a true claim resting on a stale reason) | Driven: `check_live_bug_gate(".")` -> 0 drifts with `{bug}` and 0 with `{bug, security}`; the only live `security` item is `c4yixg` (`graduated`, `- Blocks-Release: next`); `0htqmm`'s cited `754txs` is now `- Status: done`; `tests.yml`: "release-gates is currently ADVISORY (report-only), NOT fail-closed" | THE "NOTHING BECOMES FLAGGED" CLAIM IS TRUE FOR A WEAKER REASON THAN THE AVAILABLE ONE. The plan rests it on "this repo keeps the default", which does not show what happens if someone widens the set here. Measured, widening to `{bug, security}` flags ZERO items, because the one live `security` item already carries a gate. The backlog item's own example (`754txs`) has since closed, so a reader checking the cited evidence finds it stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Deferred entry now carries the driven measurement and notes `754txs` has closed; F-7 and F-9 record the zero-drift result and the advisory-CI bound; V-06 requires a before/after `aw check release-gates` count as the no-status-moved evidence. |
| PR-307 | LOW | IN-SCOPE | G. Plan executability (an open question the repository answers, plus an unevidenced gap) | `config.py`'s run-policy comment quoting the 2026-09-10 ruling verbatim, with its shared-tracked-file rationale; `findings_gate_threshold` falling back wholesale on a single scalar; `for f in _backlog._iter_items(repo_root):` and `_iter_items`'s "Every backlog item file under either layout's status dirs"; AGENTS.md "a backlog item, spec, or plan whose `- Work-Kind:` is `bug`" | OQ-02 ASKS THE MAINTAINER WHAT THE RECORDED POSTURE ALREADY DECIDES, AND F-10's GAP HAS NO EVIDENCE. The unknown-kind question is settled by the fall-back-and-warn ruling plus the observation that both options warn, so only the surviving intent differs. Separately, the Scope check's honest note that specs and plans are unchecked carries no citation, so a reader cannot tell whether this plan introduces the gap or inherits it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 resolved as "drop the unknown name and warn" with the ruling quoted, the scalar-versus-list distinction, and a requirement that the warning NAME the dropped kind; E-02 tests that case. F-10 records the specs-and-plans gap with both citations, a Deferred entry declines to close it with a reason, and E-07 is instructed not to narrow the rule's wording to match the checker. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-02: an unknown kind name in the list - drop just it, or reject the whole value? | Resolve it myself as "drop the unknown name and warn, naming the dropped kind". | (a) Ask the maintainer as the plan proposed - rejected: the repository answers it, since `config.py` records the fall-back-and-warn ruling verbatim with its shared-tracked-file rationale, and the rule is not to ask what the repository answers. (b) Whole-value fallback, following `findings_gate_threshold` - rejected: that reader takes a single scalar where there is no partial answer to preserve, so it does not generalize to a list; applying it here would silently discard a `security` gate the repository asked for over one typo. | the 2026-09-10 ruling quoted in `config.py`; `findings_gate_threshold`'s scalar shape; both candidates warn, so only surviving intent differs | yes |
| D-2 | Should the `RuleSpec` determinism tag change now that the rule reads config? | No: keep `DET_DETERMINISTIC` and say so explicitly in the item. | (a) Downgrade to `DET_HEURISTIC` - rejected: the tag records how the finding's truth was reached, and a literal key read involves no inference, so a downgrade would weaken a shipped catalog claim about a release-gating rule for no gain. (b) Leave it unmentioned - rejected: that is what invites the wrong inference, since "reads a config file" superficially reads as heuristic. | `DET_DETERMINISTIC`'s definition under "Determinism tags"; the rule's own "No inference" comment | yes |
| D-3 | E-01 leaves the vocabulary source open. Pick injection, pick a copy, or leave it to the executor? | Recommend injection, permit a copy only with a sourced comment, and record the precedent either way. | (a) Mandate injection - rejected: a local copy is genuinely precedented here (`REVIEW_GATE_THRESHOLDS` duplicates `review_findings.SEVERITIES`) and forcing one shape over a working alternative exceeds what the evidence supports. (b) Leave it fully open as authored - rejected: without the precedent stated, the choice gets made by convenience and the duplication cost is invisible. | `config.py` importing only stdlib; `backlog`/`status_set` importing `config` locally; the `REVIEW_GATE_THRESHOLDS` duplication and its docstring citation | yes |
| D-4 | F-10: the rule text covers specs and plans but the checker reads backlog items only. Widen the checker here, or record it? | Record it with evidence, decline to close it, and forbid narrowing the rule's wording to match. | (a) Widen `check_live_bug_gate` to iterate specs and plans - rejected: it predates this plan and is orthogonal to configurability, and widening a shipped `error`-severity rule's reach in the same change that alters its membership test makes any regression unattributable to either. (b) Narrow the AGENTS.md sentence to "backlog item" so text and checker agree - rejected as the wrong direction: the RULE legitimately governs all three carriers, and weakening a policy statement to match an implementation gap is how a contract quietly shrinks. (c) File a backlog item from this review - rejected: a review must not create the work it then cites. | `_iter_items`'s docstring and the loop over it; AGENTS.md's "backlog item, spec, or plan" | yes |
| D-5 | Two IPD-Z602 advisories appeared on E-03/E-05 from my own added clarifications. Trim the evidence or split the items? | Split each into the code change and the text/test change. | (a) Trim my clarifications to silence the advisory - rejected: the added detail is exactly what an executor needs (the undercounted strings, the determinism tag), so removing it to satisfy a count would trade real guidance for a clean lint. (b) Leave the advisories - rejected: they are the linter correctly observing multi-concern items, and the split also makes the membership swap and the prose correction independently verifiable. | `IPD-Z602` details naming three clauses in each item; the resulting E-01..E-08 conforming with 0 findings | yes |
