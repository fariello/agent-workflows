# Review findings: plan bec7ee

- Subject-Id: bec7ee
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-201 (HIGH, fixed), PR-202 (MEDIUM, fixed), PR-203 (MEDIUM, fixed), PR-204 (MEDIUM, fixed), PR-205 (LOW, fixed), PR-206 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `3868cd45`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
`--phase review-finalize` reports `clean` with zero findings after revision. The plan's own first `- Kind:`
bullet reads `child`, so the `IPD-S407` orchestrator row check does not apply.

THE PLAN'S MEASUREMENT BASE IS UNUSUALLY GOOD AND I RE-DROVE ALL OF IT. Every one of F-1 through F-10
reproduces, and two of them are the kind of correction that improves a Set rather than merely decorating it:

- F-1 reproduces exactly. `tests/test_containment_predicates.py` and `tests/test_wtiso_adversarial.py` are
  both absent, and `git show --stat 19313eed` lists both as deleted (731 and 704 lines). So the backlog
  item's "Pinned by tests/test_containment_predicates.py" is false, and the plan is right that this shrinks
  Order 02 from "retire a pin first" to "delete an unpinned stub".
- F-2 reproduces exactly. An AST walk over every `.py` in the tree except the module itself finds exactly
  ONE import of `wtiso_gate` anywhere: `from agent_workflows.wtiso_gate import AW_MISSING_INPUT as
  _AW_MISSING_INPUT` in `lane_containment`. The module is 443 lines and its entire consumed surface is one
  string constant.
- F-3 reproduces, with a caveat I had to discover the hard way (PR-205). Driven with correctly-typed
  arguments, the nine public predicates split exactly 5 raising `NotImplementedError`
  (`check_lifecycle_role`, `check_hook_bypass`, `check_protected_refs`, `classify_retention`,
  `check_receipt`) and 4 implemented-but-uncalled (`check_scope`, `format_missing_input`,
  `parse_missing_input`, `check_permission_deadline`).
- F-6 and F-7 reproduce verbatim, and F-7 is the most valuable row in the table: `private_file`'s own
  docstring names BOTH the attestation token and the analytics pseudonym salt, so the plan's warning not to
  delete `private_file` alongside the token is correct and prevents a real mistake in a sibling plan.
- F-10's two prior backlog items both resolve (`ikxtkj` graduated, `gia5i7` open), as do `ariaau` and
  `dvonrn`.

THE DOMINANT FINDING IS THAT THE PLAN WAS UNEXECUTABLE AS WRITTEN, and it is exactly the class of defect a
pre-execution review exists to catch, because nothing else in the pipeline would have caught it until
finalize. `- Scope-Paths:` declared `.aw/records/research/20260930-malgate-01-*.md`. The research ordinal is
numbered within the RESEARCH tree's members of the named set, NOT by the authoring plan's `- Order:`, and
Set `malgate` has no research members, so the tool derives `-00-`. Measured by dry-running the real
invocation:

```
$ aw research new --kind survey --set malgate --slug p15-gate-audit --agent
  "changes":[{"kind":"create","path":".../.aw/records/research/20260930-malgate-00-1qufj5-p15-gate-audit.survey.md"}]
```

Two further dry runs also produced `-00-` (`7v1owl`, `tl3vrl`), and `ls .aw/records/research/ | grep malgate`
is empty, confirming the ordinal belongs to the research set. Then, against the shipped matcher:

```
_scope_match(derived, '.aw/records/research/20260930-malgate-01-*.md')  -> False
_scope_match(derived, '.aw/records/research/20260930-malgate-*.md')     -> True
```

The consequence had it shipped is specific: the ONE file the plan produces would be an undeclared
out-of-scope path while the single declared path went unmodified, so `aw ipd finalize`'s two-way scope
reconciliation would have demanded both a `--scope-reason` and a `--scope-ack` from a plan that did exactly
what it intended. The plan's own conventions section records that an earlier draft already tripped
`check.scope-path-target-stale` on this same field and was corrected, which makes this the second iteration
of one mistake and is why I recorded the ordinal rule as a convention rather than only fixing the glob.

I ALSO FOUND THE LATENT HALF OF THE SAME ISSUE (PR-202). `_scope_match` is segment-aware: a single `*`
stays within one path segment. The research README's "States and layout" table shows `todo` and `active`
records live at the hot root while `reference` and `archive` relocate into `YYYYMM` monthly shards. So the
corrected flat-root glob is right for a record born at `todo`, and would silently stop matching if the
record were ever shelved. That is now stated in the plan, and it turned out to be the mechanical key to
OQ-01.

BOTH OPEN QUESTIONS CARRIED `Owner: reviewer`, so they were addressed to me and Step 3 required me to
resolve them rather than hand them on.

OQ-01 asked whether to file the audit "as a decision record under `reference/`, or as a plain research
report". The question contains a category error, and acting on it as posed would have produced a
non-conforming record. `--kind` and `status:` are two different axes. `--kind` is a mandatory naming facet
drawn from a validated enumeration, measured at 17 values, where an unknown value exits 2 with
`error: unknown kind`. `reference/` is not a kind at all: it is where the tool RELOCATES a record whose
tool-owned `status:` becomes `reference`. So "file it under `reference/`" is not available at creation time,
and choosing it would also move the file outside this plan's declared scope per PR-202. Resolved to
`--kind assessment` (the vocabulary's term for a judgement rendered over an existing surface, which is what
a keep/simplify/delete audit is), with `findings` and `survey` acceptable alternates if the choice is
recorded, `reference-research` explicitly excluded to avoid colliding with the status axis, and the record
left at its born `todo` status.

OQ-02 asked whether a KEEP should be re-examined when its neighbourhood changes. Resolved NO, with a
stronger basis than the plan's authored one. The plan argued the mechanism is "a larger design than this
plan's deliverable justifies", which is a cost argument and therefore not a valid basis on its own under the
Fix Bar. The real basis is shape: a staleness marker on an audit record cannot read the code it judged, so
it could only fire on elapsed time, which is precisely the warning-generator shape THIS PLAN ALREADY
REFUSES in its own Deferred section for the anti-malice-justification detector. Accepting one while refusing
the other would be inconsistent. What carries the obligation instead is P15's standing duty at the next
touch, made cheap by E-02's recorded deciding test and honest by E-04's limits section. The residual risk is
now named and accepted in the plan rather than implied.

ONE THING I CHECKED AND DID NOT FLAG. The plan adds no test, which normally draws an UNDER-SCOPE finding.
It is correct here and the plan's reasoning is sound: the deliverable is a records-tree document, and
asserting on its prose would be the text pin P16 forbids. The plan's own F-1 is the worked example of what
such a pin rots into, which is an unusually honest argument to make against yourself.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | IN-SCOPE | Rubric G (executability) | Plan `- Scope-Paths:`; `aw research new --kind survey --set malgate --slug p15-gate-audit --agent` dry run -> `20260930-malgate-00-1qufj5-...`; `ipd_lifecycle._scope_match` False vs True; `ls .aw/records/research/ \| grep malgate` empty | The declared glob `20260930-malgate-01-*.md` CANNOT match the file E-03 creates: the research ordinal is the research set's, not this plan's `- Order:`, and derives to `-00-`. The plan would produce an undeclared out-of-scope path while its one declared path went unmodified, so finalize would demand both a `--scope-reason` and a `--scope-ack` from a correctly-executed plan. Second iteration of one mistake: the conventions section records an earlier draft tripping `check.scope-path-target-stale` on this same field. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Scope-Paths:` widened to `.aw/records/research/20260930-malgate-*.md`; E-03 now states the ordinal rule with the dry-run measurement and forbids "correcting" the tool's ordinal; a new conventions bullet records that the research ordinal and the plan Order are different numbers; new finding row F-11; V-03 now requires the derived path be pasted beside the glob and shown to match. |
| PR-202 | MEDIUM | IN-SCOPE | Rubric A/G (correctness, latent trap) | `.aw/records/research/README.md` "States and layout" (`todo`/`active` -> hot root, `reference`/`archive` -> `YYYYMM` shard); `_scope_match('.../active/...', '.../20260930-malgate-01-*.md')` -> False | The scope glob is flat-root only, because `_scope_match`'s single `*` does not cross a path segment. Correct for a record born `todo`, and a latent trap: shelving the record to `reference` would relocate it into a monthly shard the declaration cannot match. Unstated, so an executor could shelve it and break scope reconciliation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New finding row F-12; the Scope check now states the glob is deliberately flat-root and forbids shelving in this plan; V-03 requires confirming `status: todo` and a root location; the resolution of OQ-01 carries the same rule. |
| PR-203 | MEDIUM | IN-SCOPE | Step 3 (resolve open questions), Rubric G | Plan OQ-01; `research_contract.KINDS` (17 values); `aw research new --kind bogus-kind` -> exit 2 `error: unknown kind`; research README "States and layout" | OQ-01 was `Status: open` with `Owner: reviewer` and contains a category error: it treats `reference/` (a tool-owned `status:` shelf position that RELOCATES the file) as if it were a `--kind` (a validated 17-value naming facet). An executor following it literally would either pass an invalid kind or shelve the record out of declared scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 resolved from evidence: the two-axis confusion named, `--kind assessment` chosen with `findings`/`survey` as recordable alternates, `reference-research` excluded, and the born `todo` status required. E-03 and V-03 updated to carry the answer; a conventions bullet records the orthogonality. |
| PR-204 | MEDIUM | IN-SCOPE | Step 3, Fix Bar reasoning | Plan OQ-02; the plan's own Deferred row refusing a detector because it "would be a warning generator, not a gate" | OQ-02 was `Status: open` with `Owner: reviewer` and rested on "a larger design than this plan's deliverable justifies", which is a COST argument and not a valid basis on its own. It also left the residual risk implied rather than accepted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 resolved NO on a shape argument rather than cost: a staleness marker cannot read the code it judged and could only fire on elapsed time, the same warning-generator shape this plan already refuses for its own detector, so accepting it would be inconsistent. P15's next-touch duty plus E-02's deciding test and E-04's limits section carry the obligation; the residual risk is explicitly named and accepted. |
| PR-205 | LOW | IN-SCOPE | Rubric E (expected evidence) | V-01(b) as authored; my own first probe passing placeholder strings mismeasured `check_hook_bypass` as `TypeError` and `check_scope`/`check_permission_deadline` inconsistently | V-01(b) asks for a per-predicate raise/return result for all nine without saying the call must use arguments of the DECLARED types. A placeholder-string probe raises `TypeError` before reaching the body, mismeasuring an implemented predicate as failing and a raising one as neither. I hit this myself and had to redo the measurement, so an executor will too, and a wrong result here is the evidence Order 02's deletion rests on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01(b) now requires declared-type arguments, names the measured trap, and cites `check_hook_bypass`'s `(Path, str, Sequence[str])` signature as the concrete case. |
| PR-206 | LOW | IN-SCOPE | Step 1 citation discipline | `rg -i "malicious same-user" agent_workflows/host_sandbox_profile.py` -> line 31 (wrapped); `attention_contract` line 507 reads "NOT anti-malicious crypto" not "anti-malice crypto"; `orchestrate_isolation`'s E-04 line has the word order transposed | Three F-4/F-5 quoted strings do not match the source as written (one line-wrapped, one paraphrased, one transposed), though every anchor resolves by symbol and every classification is correct. Batched as ONE low finding per the citation-drift rule. Material only because the phrase census IS the audit's evidence, so a paraphrased quote is not a measurement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New finding row F-13 recording all three with the resolving anchors and stating no disposition changes; V-01(c) now requires the deciding words be quoted AS THEY APPEAR in the source rather than re-quoted from this plan. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should the unmatched research-path declaration be fixed: name the real ordinal, or make the glob ordinal-agnostic? | Ordinal-agnostic: `.aw/records/research/20260930-malgate-*.md`. | (a) Hardcode `-00-`. REJECTED: it is right only until another `malgate` research record lands first, at which point the next ordinal is `-01-` and the declaration silently breaks again; the plan has already broken this field twice. (b) Declare the whole `.aw/records/research` directory. REJECTED: `_scope_match` would then admit any edit anywhere in the research tree, which is a real loss of fencing for a plan whose entire deliverable is ONE file. | Dry runs deriving `-00-` three times; `_scope_match` results for all three candidate patterns; the plan's own record of an earlier `check.scope-path-target-stale` failure on this field. | yes |
| D-2 | OQ-01: which `--kind`, and is `reference/` a kind? | `--kind assessment`, and `reference/` is NOT a kind: it is a `status:` shelf position. Record stays at born `todo`. | (a) `reference-research`. REJECTED: it reads as the `reference` status axis and would mislead a reader about where the record lives. (b) `survey` or `findings`. ACCEPTED AS ALTERNATES rather than rejected, since both are defensible for an enumeration-plus-judgement document and the question's real requirement is that the choice be recorded. (c) Shelve to `reference` for durability. REJECTED on mechanism: it relocates the file into a monthly shard outside the declared scope glob. | `research_contract.KINDS` (17 values); `aw research new --kind bogus-kind` -> exit 2; `.aw/records/research/README.md` "States and layout" table; `_scope_match` segment behavior. | yes |
| D-3 | OQ-02: add a staleness mechanism for KEEP decisions? | No, with the residual risk named and accepted. | Add a re-examination schedule or staleness marker. REJECTED on shape, not cost: it cannot read the code it judged, so it could only fire on elapsed time, which is the warning-generator shape this plan itself refuses one section earlier for the anti-malice detector. Accepting one and refusing the other would be incoherent. | GUIDING_PRINCIPLES P15's next-touch obligation; the plan's own Deferred row ("a warning generator, not a gate"); E-02's deciding-test requirement and E-04's limits section. | yes |
| D-4 | Should the three drifted F-4/F-5 quotes be treated as evidence failures or as drift? | Drift: one batched LOW finding, no disposition changed. | Raise each as a real evidence finding at the severity of the claim it supports. REJECTED per the workflow's costlier-error rule: every anchor RESOLVES by symbol and every classification is correct, so rejecting citations I had merely failed to re-locate verbatim would be the worse error, and the measured precedent (`si24ia` PR-305) is exactly that mistake. | Each anchor located by symbol in its own module; the plan-review Step 1 disposition rule for a resolving anchor whose line or wording moved. | yes |
| D-5 | Is "this plan adds no test" an UNDER-SCOPE finding? | No. | Flag it and require a test. REJECTED: the deliverable is a records-tree document, and asserting on its prose is the text pin GUIDING_PRINCIPLES P16 forbids; the plan's own F-1 is the worked example of such a pin rotting into a false citation. The behavior-affecting work sits in Orders 02 and 03 with their own obligations. | GUIDING_PRINCIPLES P16; the plan's "Required tests / validation" reasoning; F-1's measured outcome. | yes |

No decision in this round is `Reversible: no`, so none requires escalation beyond this record. No finding
was left `OPEN` or `DEFERRED`, so no `- Blocking: yes` escalation is owed under the gate threshold.
