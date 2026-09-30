# Review findings: plan mt54wr

- Subject-Id: mt54wr
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-701 (HIGH, fixed), PR-702 (MEDIUM, fixed), PR-703 (MEDIUM, fixed), PR-704 (LOW, fixed), PR-705 (LOW, fixed)

## Round 1

Reviewed at HEAD `c4616e28` in an isolated review lane. The plan file was already committed and unchanged,
so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming`, exit 0, ZERO findings BEFORE semantic review; `--phase review-finalize --agent` reports
`conforming` with zero findings after revision. The plan is `- Kind: child`, so the `IPD-S407`
orchestrator row check does not apply.

THE PLAN'S CENTRAL CORRECTION IS THE MOST VALUABLE THING IN IT AND IT VERIFIES EXACTLY, so I record that
before the findings. The dead string is genuinely gone (`grep -n -i 'unwired|built but'` over the spec
exits 1), line 29 reads what the plan quotes, and there is exactly ONE live citing site in source
(`runner_shared.py` under the `retrywire` header, "Spec `25kzda`'s own preamble concedes it: 'the ledger is
built but UNWIRED'"). More importantly F-2 holds: the item's own REPLACEMENT evidence has rotted, and an
executor following the item literally would install a false citation. `NOTHING PASSES THEM` now appears in
the spec ONLY inside the `2026-09-26 note (aw specs)` history line that records deleting it, `3764` appears
nowhere, and the live text at line 63 says the OPPOSITE ("Re-measured 2026-09-26: SEVERAL DRIVER-SIDE
commit sites pass them"). That history note also already names this very backlog item, so the rot is
acknowledged in-tree exactly as the plan says. F-3's numbers moved again under me, which is the plan's own
point: `849` of `6382` commits carry an `AW-Run` trailer at review, against the plan's 644 of 6054 and the
item's zero of 3764. F-9 holds three ways (0 `ledger.jsonl` files; `grep -c 'run_engine\|RunLedgerStore'`
is 0 in BOTH drivers; Section 6.2 at "### 6.2 Implementation choices still requiring repository-level
definition" still lists "the durable storage location for run ledgers and large captured outputs"), so
E-02's replacement citation is TRUE and not merely different. F-10 holds: the refusal f-string really does
print `NARROWER than spec 25kzda :166`, and the sentence it quotes really does live in `### 2.1 Command
grammar` at line 224. F-7 holds (4 case-insensitive, 2 case-sensitive) and both citing records really are
terminal. `p9y51u`, `cpi6p3` and `yu47nf` all resolve.

THE ONE SERIOUS FINDING IS A MISCOUNT THAT BOTH THIS PLAN AND ITS SIBLING SHARE, WHICH IS WHY NOBODY
CAUGHT IT. That is PR-701. This plan (E-04, F-6, F-10) and `yu47nf` E-07 each enumerate THREE `:166` sites
in `runner_shared.py`; measured, `grep -n ':166' agent_workflows/runner_shared.py` returns FOUR: 15200,
15227, 15376, 16332. The fourth sits inside `expand_dependency_closure`'s docstring ("Spec `:166` and
`:1007` both state the negative: ..."), confirmed by AST to be inside `FunctionDef
expand_dependency_closure`, and I read `yu47nf` E-07 in full to be sure it does not name it - it names only
the rationale comment, the refusal f-string and `enforce_mixed_type_gate`'s docstring. Two consequences.
First, after BOTH plans execute, that anchor survives while two plans' evidence implies the file was swept.
Second, and concretely, this plan's V-04 requires pasting `rg -n ':166'` and seeing "exactly the two
remaining sites", which will show THREE, so a correct execution fails an otherwise-correct validation and
the executor's cheapest escape is to edit the surplus site - putting this plan back inside the comment block
`yu47nf` rewrites, which is the conflict E-04 exists to avoid. Worth noting `yu47nf` is `- Status:
reviewed` with `- Readiness: go-pending-approval`, so it is approval-ready and may genuinely land first;
E-04's no-op-safe drafting is well judged.

PR-702 is a CLI fact the plan's verb design does not account for. `aw check` has ONE shared subparser with
a POSITIONAL type: `cli.py` adds the verb's flags once inside `if _verb == "check":` (the block carrying
`-a`/`--all` and `--strict-setid-length`). So `--source-anchors` will parse on every type, and this is not
speculative - I confirmed the existing precedent leaks the same way, with `aw check specs
--strict-setid-length` and `aw check releases --strict-setid-length` BOTH conforming at exit 0 even though
the flag is meaningless there. E-05 specifies `aw check specs --source-anchors` and E-06 asserts only on
`specs`, so `aw check plans --source-anchors` has emergent behavior nobody decided. The fix is not a CLI
restructure (out of scope) but a stated decision plus one pinning assertion.

PR-703 is that the plan's census total is pattern-dependent and its `29` should not be pasted forward. Two
independent re-counts bracket it rather than confirming it: a strict pattern (offset adjacent to a literal
`25kzda`, plus `` spec `:NNN` ``) finds 22 anchors in 6 files; a broad pattern (any backticked `` `:NNN` ``
plus any `25kzda`-adjacent offset) finds 37 distinct triples in 7 files, including two offsets past the
spec's 1618 lines (`:16624` from `runner_shared.resolve_lane_endpoints`, `:2403` from
`test_orchestrator_retirement.py`'s `TheWorkerRoleIsRefused`) that are plainly citations of a different
file. This does NOT weaken the plan: every strictly-matched anchor did resolve to a heading other than its
prose's subject, so F-4's qualitative claim survives both counts, and the plan already tells E-01 to
re-measure. It does mean the detector's own DEFINITION of a citation is the real deliverable, and that
`p9y51u`'s "28" is equally provisional.

PR-704 is a latent-defect-repeat in E-03's spec enumeration. E-03 says to read `- Id:` out of every
`.aw/records/specs/*/*.spec.md`, a flat one-level glob. The shipped enumerator `specs._spec_files` is
deliberately RECURSIVE and ignored-path filtered, and its docstring records exactly why: a flat glob
previously made specs in lifecycle subdirectories "completely invisible to `aw check specs`, which reported
conformance having examined zero files", and the recursion is coupled to `core.is_ignored_path` so
gitignored specs under `records/*/untracked/` are not indexed. Every spec today sits exactly one level deep,
so a hand-rolled glob works NOW, which is what makes this latent rather than broken: it re-introduces a
defect this repository already paid for, and an unfiltered `rglob` would instead index untracked local
specs. E-03 already says "reuse it if it exposes paths", so this is a sharpening rather than a redirection.

PR-705 IS MY OWN DEFECT. The plan arrived with ZERO lint findings; my first pass at PR-703 cited the two
out-of-range hits as bare `path:line`, and `review-finalize` then reported two fresh `IPD-C801` advisories.
I resolved both to their enclosing symbols by AST and rewrote the citations to lead with the symbol. The
count is back to zero. I record it because this plan is itself a case study in the offsets-expire
convention, so breaking that convention inside its review is worth stating plainly rather than quietly
fixing.

I ALSO CHECKED FOUR THINGS THE PLAN DOES NOT CLAIM, none of which produced a finding. First, whether
`aw check specs --source-anchors` already exists: it does not (`unrecognized arguments`), so the verb is
genuinely new and `agent_workflows/spec_citations.py` and `tests/test_spec_citation_anchors.py` are both
absent as the plan implies. Second, whether E-05's severity reasoning is right: it is, precisely.
`artifact_core.drift_exit_code` returns `1 if any(getattr(d, "severity", "") != "info" ...)`, so `info` is
the ONLY non-failing severity and `warning` would indeed turn a pre-existing census into a red check; the
`check.spec-criteria-uncovered` precedent is real and carries the same `info`/`""` pairing. Third, whether
F-8's `DECISIONS.md` exclusion is sound: it is, the bullet states its own dated limit rather than citing
the spec, and F-9 re-measured the limit true. Fourth, whether the two terminal records exist where named:
both do, under `plans/executed/` and `backlog/done/`.

ONE JUDGEMENT I AGREE WITH. The plan argues `chore` rather than `bug` on the perceptibility test: no
computed behavior is wrong, and the single operator-visible string still names the spec, the flag and the
remedy correctly while mis-citing a section. That is the right reading, and the plan re-argues it from
measurement rather than inheriting it. Both open questions are `Owner: maintainer` and non-blocking, each
with a well-reasoned `Carrier` or `Carrier-Declined`, and I left both open deliberately: OQ-01 turns on
check-noise tolerance and OQ-02 on whether a non-resolving section token is a defect at all, and both are
genuinely the maintainer's to settle rather than facts in the repository.

Bare suite at review HEAD: `3368 passed, 2 skipped, 3 warnings in 60.09s`. Working tree clean; this review
changed only plan and review records and touched no production file.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | Rubric D (anti-regression), E (verification), G (ownership) | `grep -n ':166' agent_workflows/runner_shared.py` -> 4 hits (15200, 15227, 15376, 16332); AST places 15376 inside `FunctionDef expand_dependency_closure`; `yu47nf` E-07 read in full and names only three | THERE ARE FOUR `:166` SITES, NOT THREE, AND THE FOURTH IS OWNED BY NEITHER PLAN. `expand_dependency_closure`'s docstring carries one that both this plan and `yu47nf` omit, so after both execute it survives while both plans' evidence implies a swept file. Concretely, V-04 demands "exactly the two remaining sites" and will see THREE, failing a correct execution and tempting the executor to edit the surplus site - back inside the comment block E-04 exists to avoid. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12. E-04 now names the fourth site, requires leaving it, and requires reporting the MEASURED count; V-04 expects THREE survivors, requires every returned line accounted for and attributed to a carrier, and forbids "fixing" the surplus to make a number match. A new Deferred row routes it to `p9y51u`. F-6 and F-10 corrected. |
| PR-702 | MEDIUM | IN-SCOPE | Rubric C (existing mechanisms), F (UX) | `grep -n 'if _verb == "check"' agent_workflows/cli.py` with `-a`/`--strict-setid-length` beneath it; `type` is positional; measured `aw check specs --strict-setid-length --agent` and `aw check releases --strict-setid-length --agent` both `"outcome":"conforms","exit":0` | `aw check` HAS ONE SHARED SUBPARSER, so `--source-anchors` will parse on EVERY type, not only `specs`. E-05 specifies only the `specs` spelling and E-06 asserts only on it, leaving `aw check plans --source-anchors` with behavior nobody decided. The existing precedent flag already leaks this way, so this is the established shape rather than a bug to fix here. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13. E-05 now records the shared-parser fact with its measurement, requires a STATED decision for a non-`specs` type (report anyway, or refuse naming `specs`), forbids inventing a per-type parser, and requires the choice in `--help`; E-06 gains a third CLI assertion pinning it. |
| PR-703 | MEDIUM | IN-SCOPE | Rubric G (live-artifact criteria) | Strict re-count: 22 anchors / 6 files. Broad re-count: 37 triples / 7 files including `:16624` (in `runner_shared.resolve_lane_endpoints`) and `:2403` (in `TheWorkerRoleIsRefused`), both past the spec's 1618 lines | THE CENSUS TOTAL IS PATTERN-DEPENDENT AND `29` IS ONE MEASUREMENT, NOT THE NUMBER. Two re-counts bracket it at 22 and 37 depending on how a "citation" is defined, and the broad count includes offsets that are plainly citations of another file. F-4's qualitative claim survives both, but the detector's definition of a citation IS the deliverable, and `p9y51u`'s "28" is equally provisional. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14 with both re-counts. E-01 must now state the PATTERN as part of the result, must not try to reproduce `29`, and must flag out-of-range hits as probable foreign citations. The Scope check and F-10 no longer restate a count. |
| PR-704 | LOW | IN-SCOPE | Rubric C (reuse canonical mechanisms), D | `specs._spec_files`'s docstring: a flat glob made subdirectory specs "completely invisible to `aw check specs`, which reported conformance having examined zero files"; recursion coupled to `core.is_ignored_path` for `records/*/untracked/`; measured every spec is exactly one level deep today | E-03's flat `.aw/records/specs/*/*.spec.md` glob re-introduces a defect this repository already paid for. It works today (all specs are one level deep), which is what makes it latent rather than broken; an unfiltered `rglob` would instead index gitignored local specs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires reusing `specs._spec_files(repo_root)` rather than hand-rolling a glob, quotes the docstring's recorded reason for the recursion and the ignored-path coupling, and requires saying so explicitly if the function does not expose what is needed. |
| PR-705 | LOW | IN-SCOPE | Spec `ipd-structure-and-linting` Section 10.2 (`IPD-C801`) | `review-finalize` reported 2 fresh `IPD-C801` advisories after my PR-703 edit; the authored plan had 0 | SELF-INFLICTED AT REVIEW. My first PR-703 text cited the two out-of-range hits by bare `path:line`, introducing two advisories into a plan that arrived clean - and into a plan that is itself a case study in the offsets-expire convention. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved both offsets to their enclosing symbols by AST (`runner_shared.resolve_lane_endpoints`, `TheWorkerRoleIsRefused`) and rewrote the citations to lead with the symbol plus a quoted string. `review-finalize` advisory count back to 0. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The fourth `:166` site (PR-701) is owned by nobody. Add it to E-04, file a new item, or route it to the existing carrier? | ROUTE IT TO `p9y51u` and require E-04 to NAME it in evidence. | (a) Add it to E-04: rejected, it sits in a docstring inside the comment neighbourhood `yu47nf` E-07 rewrites, so touching it recreates the exact conflict E-04 is drafted to avoid, and it has no operator reach so it fails this plan's own stated fence. (b) File a new backlog item: rejected, `p9y51u` already exists for precisely "the non-operator-facing spec 25kzda line anchors" and a second item would split one defect's history. (c) Leave it unmentioned: rejected, that is how it became invisible to two plans in the first place. | `grep -n ':166'` -> 4 hits; AST placing 15376 in `expand_dependency_closure`; `yu47nf` E-07's own enumeration; `.aw/records/backlog/open/20260929-sbh1o1-01-p9y51u-...backlog.md` exists and covers this class | yes |
| D-2 | PR-702: should the review pick the non-`specs` behavior for `--source-anchors`, or require the executor to decide? | REQUIRE A STATED DECISION, naming both acceptable branches, rather than mandating one. | Mandate "run the report regardless of type": tempting and probably right (the detector takes a file set and is indifferent to the records tree), but rejected as a reviewer overreach into a UX choice with no repository precedent either way; what matters is that the behavior is DECIDED, DOCUMENTED in `--help` and PINNED by a test rather than emergent. Mandate "refuse": rejected for the same reason plus it adds a refusal path nothing asked for. | `cli.py`'s single `if _verb == "check":` flag block with a positional `type`; the measured leak of `--strict-setid-length` onto `specs` and `releases`, showing the repository already tolerates the shared shape | yes |
| D-3 | Both open questions are `Owner: maintainer`. Resolve either from evidence? | LEAVE BOTH OPEN; neither blocks. | Resolve OQ-01 myself: rejected, the conditional half is already settled from evidence in the plan (a gating severity is impossible until the tree is swept, because `drift_exit_code` exempts only `info`), and what remains is a judgement about check-noise tolerance, which is the maintainer's. Resolve OQ-02: rejected, its own text concedes the DEFECT half of its measurement is unestablished (some of the 15 section tokens name a section whose heading is merely spelled differently), so resolving it would mint a defect count the measurement does not support. | `artifact_core.drift_exit_code` body; the 2026-09-10 ruling that a non-blocking open question does not make a plan `NO-GO`; both questions carry a `Carrier` or a reasoned `Carrier-Declined` | yes |
| D-4 | Accept `chore`/`low` and the absence of a release gate? | ACCEPT. | Escalate to `bug`: rejected. One citation does reach an operator, but the message still names the spec, the flag and the remedy correctly and only mis-cites a section, so no user waits on a wrong answer; the cost falls on a reader re-verifying a premise. | `AGENTS.md`'s perceptibility test; backlog `sbh1o1` carries no `- Blocks-Release:` and is `low`/`chore`; the refusal string read in full | yes |
