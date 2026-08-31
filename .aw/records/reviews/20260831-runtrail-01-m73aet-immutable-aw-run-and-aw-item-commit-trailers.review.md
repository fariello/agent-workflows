# Review: Immutable AW-Run and AW-Item commit trailers on the shipped commit helper

- Plan-Id: m73aet
- Reviewed-At: 2026-08-31
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE

## Round 1

All claims verified at HEAD `381dbd5c1c313c16b4a833ed5c3541939872ee42`, working tree clean, target plan
committed and unchanged (pre-review snapshot correctly skipped per the workflow's Step 1). Structural
preflight `aw ipd lint --phase author` reports `conforming`.

NO DEFECTS FOUND. This is the strongest of the three `detrun` successors and I could not break it. Every
material claim verified TRUE, and two of them I verified by EXECUTION rather than by reading:

- `offer_commit` really is at `git_commit_helper.py:133`, and the single message-consuming git invocation
  really is `_git(repo_root, ["commit", "-m", message, "--", *our_staged])` at `:245`.
- `work_cmd.run_commit` really is at `:360`.
- `AW-Run:` and `AW-Item:` really are ZERO-hit across `agent_workflows/` and `tests/`, so the deliverable
  is genuinely unbuilt.
- E-02's case (b) hazard is REAL and I reproduced it. Appending a trailer after a blank line to a body
  that already ends in a trailer block makes git's own parser DROP the earlier trailers: given a body
  ending `Co-authored-by: x <x@y>`, the naive form yields `git interpret-trailers --parse` output of ONLY
  `AW-Run: r1`, silently losing the co-author. Done correctly (joining the existing block) the parse
  returns both. So the plan's most subtle requirement is correctly diagnosed, not speculative.
- E-02's chosen verification method WORKS in this environment: `git interpret-trailers --parse` is
  available and behaves as the plan assumes, so V-02's evidence is collectable rather than aspirational.

Three judgements deserve explicit endorsement, because each is the kind of restraint that usually has to
be added at review:

1. THE BLAST RADIUS IS CORRECTLY IDENTIFIED AND CORRECTLY HANDLED. `offer_commit` has 23 call sites across
   at least 10 modules including both runners, `status_set`, `specs`, `engine` and `cli`. The plan names
   this leaf-module risk explicitly, requires the parameter to DEFAULT EMPTY so every existing caller is
   byte-for-byte unaffected, and forbids touching the path-scoping, the `--no-verify` prohibition, the
   no-push rule and the index snapshot/rollback logic. That is exactly right for the one function
   `AGENTS.md` names as immune to index pollution by construction.
2. E-03's "STOP and report rather than adding a flag whose only caller does not exist yet" is a
   well-placed guard, and I verified the premise behind it: `work_cmd` has no access to a run id today, so
   a `--trailer` CLI flag really would have no consumer. "A flag with no consumer is a public contract
   taken on for nothing" is the correct instinct.
3. E-04 requires the trailer assertions to be made through GIT'S OWN parser rather than by string
   comparison, with the reason stated ("a string assertion would pass on a malformed block that git does
   not recognize"). My reproduction above is precisely why that matters: the malformed case produces a
   string that LOOKS right and parses wrong.

The plan is deliberately narrow (one optional parameter, one pure composition function, one thread-through,
additive tests) and that narrowness is the point: its predecessor `k7o7el` proposed a `commit_gateway.py`
that would have FORKED this same helper, and its own second review cut it from three items to this one.
Retiring rather than re-scoping was the right call and the residue was inherited faithfully.

Sequencing note, not a defect in this plan: the checklist records that `m73aet` must land BEFORE `wlxkoz`
(4 of the 13 `RUN-*` codes depend on these trailers). That ordering is real, but it lives only in prose:
both plans carry `- Item-Dependencies: none`. The finding is raised against `wlxkoz`, which is the
dependent side and therefore the correct owner of the edge.

### Findings

NONE. No actionable defect was found, so the findings table is deliberately empty rather than carrying a
placeholder row (a row with non-enum `Severity`/`Decision` values makes the artifact malformed and
unparseable, which `aw ipd lint` correctly reports as `REV-P002`/`REV-P003`).

Every material claim was verified, including two verified by EXECUTION rather than reading: the case-(b)
trailer-parsing hazard is real and reproducible (the naive form makes git's own parser drop a preceding
`Co-authored-by`), and `git interpret-trailers --parse` is available in this environment, so the plan's
chosen verification method is collectable rather than aspirational.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The checklist requires `m73aet` to land before `wlxkoz`, but neither plan declares the edge. Should the ordering be fixed in THIS plan? | NO. Fix it on the DEPENDENT side (`wlxkoz`), where it is raised as PR-001's resolution. | Adding an edge or a note here. Rejected because an `- Item-Dependencies:` edge is declared BY the dependent artifact and points AT its prerequisite; recording it on the prerequisite points the wrong direction and would not be read by the tooling that evaluates edges. | Both plans carry `- Item-Dependencies: none`; `ipd_schema.py` edge grammar is declared by the dependent (`executed:<id6>` names the prerequisite) | yes |
| D-2 | Should the plan's zero-defect result be reported as APPROVE, or should something be manufactured to look thorough? | APPROVE with an explicitly EMPTY findings table, plus a written account of what was verified BY EXECUTION so the absence of findings is auditable rather than asserted. | Recording a cosmetic LOW finding to appear diligent. Rejected: the workflow states "Do not invent findings", and a padded table makes a genuinely clean plan indistinguishable from a lightly-read one. | plan-review workflow Step 2.2 ("Do not invent findings"); the two execution-verified claims are recorded in the Round 1 prose above | yes |
