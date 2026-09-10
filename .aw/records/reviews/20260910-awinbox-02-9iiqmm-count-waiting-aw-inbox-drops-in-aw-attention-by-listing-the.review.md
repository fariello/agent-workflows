# Review: count waiting aw inbox drops in aw attention by listing the directory only, child 9iiqmm (Set awinbox)

- Subject-Id: 9iiqmm
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `0cc91fa3`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0 findings)
before semantic review, and `--phase review-finalize` conformed after the revisions. The plan carries no
`- Blocks-Release:`, correctly: backlog `plbkp5` carries none.

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat this as a
near-self-review and worth less than an independent one.

THE PLAN'S CENTRAL SAFETY ARGUMENT IS SOUND AND UNUSUALLY WELL EVIDENCED. The listing-versus-parsing
distinction is real and the author reproduced the hazard rather than citing it; I re-verified `_ID_RE` at
`selectors.py:111` is position-unanchored and used with `.search()`. The `setup_needed` precedent
(`attention.py:1405`) is the right shape and the plan follows it instead of inventing one. The `elif`-chain
trap (F-3) is real, is the single most important implementation detail, and the item does not mention it.
The exit-code reasoning is correct and cited to the code that states it. Six of the plan's ten authored
findings verified exactly as written.

WHAT REVIEW FOUND IS THAT TWO FACTS OUTSIDE THE PLAN'S FIELD OF VIEW EACH DEFEAT A STATED REQUIREMENT.
First, the sibling plan in this SAME Set at Order 01 adds `.aw/inbox/README.md`, so it lands BEFORE this
plan and makes the inbox permanently non-empty; a literal "count anything waiting" counter would then nudge
forever on a drained inbox, which is precisely the noise this plan says trains readers to ignore the footer.
Second, the footer renders on an interactive TTY ONLY, not merely "not JSON": `select_output` routes to the
agent renderer on ANY non-TTY stdout, so a piped `aw attention` never renders a board at all. I ran it. Every
agent in this repository reads attention through a pipe, and agents are a plausible class of drop-forgetter,
so the plan's under-scope statement understated the limit rather than merely omitting a detail.

I DID NOT SIMPLY ADOPT THE OBVIOUS FIX FOR THE SECOND, because measuring it showed a cost. Emitting the
nudge as a WARNING diagnostic follows the `order_notices` precedent exactly, but `to_agent_record` derives
`findings` from `len(diagnostics)` with no severity filter, so a clean repo's record would read `findings: 1`
with `outcome: clean`. I constructed the record and reproduced that. A phantom finding on a healthy repo is a
worse contract break than the invisibility it fixes, so the question went to the maintainer as OQ-04 with
three routes costed, rather than being resolved on my authority.

THE SUITE BASELINE WAS WRONG IN BOTH HALVES, and the correction matters because the real failure invites
destroying a co-worker's work: `opencode-recovery/` is gitignored, holds another party's session transcripts,
and an executor reconciling a wrong baseline has an incentive to delete it. The second failure passes in
isolation and is load-sensitive under `-n auto`, which an executor must know before treating it as their own
regression.

TWO OPEN QUESTIONS THE PLAN LEFT TO ITS EXECUTOR WERE ANSWERED FROM EVIDENCE INSTEAD. The nested-directory
question (OQ-02) is a judgement call with no maintainer content, so it is resolved and written into E-01. The
spec-sync question the plan assigned to its executor is now done: Section 8.1 of the attention spec constrains
classification, the JSON object, the exit contract, and no-write/determinism, and enumerates no footer
advisory lines, which is why the two existing ones needed no amendment. No spec path enters Scope-Paths, and
the determinism invariant is now carried into the fence as a no-mtime rule.

Six findings, all FIXED in place, no deferrals. E-item and V-item counts are unchanged at five each.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | IN-SCOPE | F. UX; G. executability | `lznpv6` E-06 (`.ipd.md:100-105`); Order fields (`lznpv6` Order 1, this plan Order 2); this plan grepped for README -> 0 hits | **The sibling plan in this same Set makes the inbox permanently non-empty, so the nudge as specified would fire forever on a drained inbox.** `lznpv6` E-06 adds `.aw/inbox/README.md` and executes FIRST (Order 01 vs 02), and is already `reviewed`/`go-pending-approval`. A counter that counts "anything waiting" then reports at least one entry on every machine forever, defeating this plan's OWN stated rule that a nudge must not fire when there is nothing to nudge about ("noise that trains readers to ignore it"). Neither the backlog item nor the plan mentions the interaction | C:Low; U:High; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now excludes `README.md` and `.gitkeep` by name and requires the exclusion plus its reason in the comment; the narrowing of the item's literal hidden-files-count wording is justified in place so it is not silently reverted; V-01 and V-04 require a README-and-`.gitkeep`-only case returning ZERO. New F-11 |
| PR-602 | HIGH | UNDER-SCOPE | C. architecture; F. UX | `attention.py:2795-2953` (footer inside the final human `else`); `result_types.py:75-76`; ran `aw attention` piped and got the agent JSONL record, not a board | **The line reaches an interactive terminal and nothing else, including no pipe, and the plan describes it as visible in `aw attention`.** `select_output` routes to `OutputMode.AGENT` on `--agent` OR ANY NON-TTY STDOUT, so `--agent`, `--check`, the `--paths`/`--id6-only`/`--filenames` early return, and every piped or redirected invocation show nothing. Since `AGENTS.md` directs agents to consume `aw attention` rather than re-scan the tree, the reader class likeliest to leave a drop sitting is the class that cannot see the count | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | FIXED AS SCOPE HONESTY PLUS A COSTED QUESTION, NOT by adding the surface. Under-scope rewritten to state the TTY-only reach as measured fact rather than "only the human board"; E-02 carries the surface limit; V-02 requires pasting the `--agent` run showing the line ABSENT; new OQ-04 puts the audience decision to the maintainer with three routes costed. Deliberately not self-resolved: see D-2 and PR-603 for why the natural fix is not free. New F-12 |
| PR-603 | MEDIUM | IN-SCOPE | B. security/contract; E. testing | `result_types.py:398-400` (`findings` = `len(self.diagnostics)`, no severity filter); constructed the record and ran it | **The obvious remedy for PR-602 would put a phantom finding on a healthy repo.** Emitting the nudge as a WARNING `Diagnostic` follows the `order_notices` precedent (`attention.py:2752-2760`) and does not touch the exit code, but `to_agent_record` counts diagnostics regardless of severity, so a clean record becomes `findings: 1` with `outcome: clean`. Measured. The `Evidence`-key alternative does not inflate `findings` but is sanitized to the bare key name in the compact record, so the number is visible only under `--verbose` | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Recorded as F-13, costed inside OQ-04 so the maintainer sees why route (b) is not free, and added to the deferred list AND the scope fence as an explicit do-not-touch (`result_types.py`), since fixing the severity-blind count is a repo-wide agent-protocol change and not this plan's business |
| PR-604 | MEDIUM | IN-SCOPE | E. testing; D. anti-regression | measured bare: `2 failed, 5957 passed, 3 skipped, 2 xfailed` at HEAD `0cc91fa3`; `test_orchestrator_retirement.py` -> `112 passed`; `test_runner_backlog_close.py` -> `47 passed`; `.gitignore:49` | **The suite baseline is wrong in both halves and the real failure invites destroying another party's work.** The plan cites `1 failed, 5648 passed` naming `test_orchestrator_retirement`, which PASSES. The actual failures are the reporting-contract parity test, which fails because a GITIGNORED `opencode-recovery/` tree of another party's session transcripts quotes the contract prose, and a SIGINT test that passes in isolation and fails on a 30-second subprocess timeout under `-n auto`. An executor reconciling the mismatch has a live incentive to delete the directory | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Conventions list carries the re-measured baseline with both real node ids and the load-sensitivity note, plus an explicit prohibition on touching `opencode-recovery/`; the fence repeats it; V-05 requires comparison against the corrected baseline and forbids greening a pre-existing failure. New F-15 |
| PR-605 | MEDIUM | UNDER-SCOPE | G. executability; spec sync | spec `20260808-1945-01` Sections 8.1/8.3/8.5; `gate_warnings` and `order_notices` added without amending it | **The plan deferred a spec question to its executor; review answered it, and also found the invariant the plan should carry instead.** Section 8.1 constrains the classification, the JSON object, the `--check` exit contract, "Writes NOTHING to disk", and byte-determinism; it enumerates no footer advisory lines, which is why the two existing ones needed no amendment. So no spec path enters Scope-Paths. But determinism IS bound and IS touchable here: a line including mtime would break Section 8.5, and the plan permits reading mtime in E-01 | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section rewritten with the answer and its citations rather than a pre-execution check, naming the two invariants the executor must confirm (no-write, determinism); the fence gains an explicit no-mtime-in-the-line rule |
| PR-606 | LOW | IN-SCOPE | F. UX; Evidence accuracy | `attention.py:2944-2950` (existing footer lines are imperative and name a remedy); `:2509-2510` (F-10's cited lines had drifted by two); `lznpv6` PR-501 (no `.tgz`; nine `.md` files) | **Three small accuracy and polish gaps.** (a) The item's sketched `inbox: 3 files waiting` does not match the house footer voice, and needs singularization for a count of one, or the footer reads in two voices. (b) F-10's line citation had drifted. (c) OQ-02's argument for walking a nested directory rests on a `.tgz` in the inbox that the sibling plan's own review measured away (nine `.md` files, no archive), so the extracted-archive case is hypothetical here | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 requires the house imperative form and correct singularization, V-02 requires the singular case pasted; F-10 re-cited to `:2509-2510` and re-verified; OQ-02 resolved with the weakened archive premise stated. New F-14 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The sibling README (PR-601) makes the inbox permanently non-empty. Exclude bookkeeping files, or accept a permanent count of one? | EXCLUDE `README.md` and `.gitkeep` by name, and justify the narrowing of the item's literal wording in the plan so a later reader does not "fix" it back | Accept the permanent 1 (rejected: it defeats the plan's own no-noise rule and would make the nudge worthless within one Set run); add an `Item-Dependencies` edge on `lznpv6` (rejected: the counter must be correct whether or not the README exists, and an edge would not make it so); count only `*.md` (rejected: the item explicitly wants non-`.md` drops counted) | The item's intent is "something is WAITING", and a README explaining the lane is not waiting for anyone; the item's own "a nudge, not a typed inventory" framing | yes |
| D-2 | The nudge is invisible to every agent (PR-602). Add the agent surface, or state the limit and ask? | STATE THE LIMIT as measured fact and raise OQ-04 for the maintainer with three routes costed. Did NOT add the surface | Add a WARNING diagnostic following the `order_notices` precedent (rejected for THIS plan: measured, it inflates `findings` 0 -> 1 on a clean record because the count is severity-blind, so it trades invisibility for a phantom finding, and fixing that is a repo-wide contract change outside two declared files); add an `Evidence` key (rejected as near-useless: sanitized to the bare key name unless `--verbose`); say nothing (rejected: the plan claimed visibility in `aw attention` and that claim is wrong for every piped reader) | Ran both the piped invocation and the constructed agent record; `result_types.py:75-76`, `:398-400`; the `order_notices` precedent at `attention.py:2752-2760` | yes |
| D-3 | OQ-02 (nested directory: one entry or walked?) was left to the executor. Resolve it or leave it? | RESOLVE as one entry, not walked, and write it into E-01 so it is no longer a per-executor choice | Leave it open (rejected: it carries no maintainer content, and an unresolved cosmetic choice is exactly what "resolve from evidence rather than asking" is for); walk it (rejected: the truer-count argument rested on a `.tgz` the sibling review measured away, and walking is unbounded for no gain to a nudge) | Both answers satisfy the item; `lznpv6` PR-501 measured nine `.md` files and no archive; a single `os.scandir` is trivially bounded | yes |
| D-4 | Does the attention spec constrain the output surface, which would make this a spec amendment? | NO for footer lines, and the answer is written into spec-sync with citations instead of left as a pre-execution check. Also carried the determinism invariant the spec DOES bind into the fence as a no-mtime rule | Add the spec to Scope-Paths defensively (rejected: declaring an edit the plan will not make misreports scope in the other direction, the same error flagged on the sibling plan); leave the check to the executor (rejected: a wrong answer means a silent contract change, and the evidence was available at review) | Spec `20260808-1945-01` Sections 8.1/8.3/8.5; `gate_warnings` and `order_notices` exist as footer/advisory output with no spec amendment | yes |
