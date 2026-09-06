# Review: the shared on-disk Set-completeness decision predicate (child 5942n7, Set orchretire)

- Subject-Id: 5942n7
- Subject-Type: ipd
- Reviewed-At: 2026-09-06
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `9afee369`. Structural preflight `aw ipd lint --phase author` conformed before semantic
review and `--phase review-finalize` conformed after the revisions.

DISCLOSURE: I authored this plan in the same session, so this is a SELF-REVIEW, not an independent one.
It is recorded because the repository requires a review record before `to-review -> reviewed`. What
raises it above a rubber stamp is that it was performed by EXECUTING the plan's own premises rather than
re-reading its prose: I called `selectors.resolve` and `ipd_lint.parse` against every live Set and parsed
all five live orchestrators' child tables. That is what surfaced PR-101 and PR-102, two HIGH findings the
authoring pass missed, both of which would have produced a predicate that passed its own tests and
misbehaved on real data.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | UNDER-SCOPE | A. Correctness; spec R-3 | E-03 pre-revision; all five `-00-` plans' tables; `ipd_schema.py:59` | E-03 said "parse the child table for declared Order tokens" as though orchestrators shared a layout. Measured, they do not: `orchretire` `Order\|Id\|Child\|Depends on`; `wslayout` `Order\|Id\|What it does\|Set dependencies`; `runprofile` `Order\|Id\|Child\|Responsibility\|Depends on`; `lanectn` `Order\|Id\|Depth\|Requirements owned\|Prerequisite\|What it delivers`; `rununify` `Order\|What it does\|Depends on` with NO `Id` column. Only the FIRST column is common, so a parser keyed on a named header crashes or vacuously passes on `rununify`, the ONE Set the check exists for (spec 2.5). `rununify` also carries a `last` row token the plan never mentioned beside `03+`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now records all five measured shapes, mandates reading the Order token POSITIONALLY from the first column, forbids requiring an `Id` column, and names `last` alongside `03+`. V-03 requires all four shapes as evidence; E-04 requires them as fixtures; V-04 adds a sabotage (require a named `Id` column -> `rununify` fixture must FAIL) |
| PR-102 | HIGH | IN-SCOPE | A. Correctness | `runprofile` resolves Orders 0-6; its table's last row is `05` | The declared-vs-resolved comparison had no stated DIRECTION. Disk can legitimately hold MORE children than the table declares: `runprofile` declares 01-05 and has six children (`kgpptv`, Order 6, `reviewed`). A symmetric "table must match disk" rule refuses that Set forever, and the refusal is unfixable without editing a plan already in flight | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now states the comparison is ONE-DIRECTIONAL (refuse only when a declared row resolves to nothing) and explains that the reverse direction is R-2's job, since an undeclared extra child is simply not `executed`. Added F-7; V-03 requires `runprofile` NOT to report unauthored rows |
| PR-103 | MEDIUM | IN-SCOPE | Evidence accuracy | F-4 pre-revision; `nna8yz` plan `- Status: approved`; `run-20260905T211011Z-3780617/state.json` | F-4 claimed `nna8yz` "carries `substantially-complete` today". It does not: its PLAN FILE carries `Status: approved`, and `substantially-complete` appears only as a RUN-STATE disposition in one run's queue entry. Since E-01 reads the plans tree, the predicate will never see that value from its own input, so the rationale for the guard was misstated and a test on a synthetic plan file bearing an impossible `Status:` could be mistaken for proof about real data | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-5 stating the run-state-vs-plan-file distinction with both citations; E-02 and V-02 now require the guard to be described as defense against a value arriving from another caller, and V-02 must show `lanectn`'s refusal naming the REAL statuses (`approved`) |
| PR-104 | MEDIUM | UNDER-SCOPE | A. Correctness; B. default-deny | E-02 pre-revision | The status test was framed as rejecting `substantially-complete`, a denylist of known-bad values. A status added to the vocabulary later would then be silently acceptable, and this predicate authorizes a terminal transition, so its default must be deny | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now mandates accepting exactly `executed` as an ALLOWLIST and says why; V-02 requires showing some other non-`executed` status is also refused, which a denylist would not do |
| PR-105 | MEDIUM | UNDER-SCOPE | Execution contract; F. prevent silent failure | gate pre-revision | The gate had the scope prohibition but not the mandated non-halting fence wording, no commit/never-push rule, no shared-checkout staging check, and, more importantly, never stated the ASYMMETRIC FAILURE DIRECTION that is this design's entire basis. The plan asserted the asymmetry in OQ-01's rationale, where an executor reading the gate would not necessarily see it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now carries the fence pointing at finalize's reconciliation, the commit/never-push and staged-set rules, and an explicit paragraph: when the code cannot tell, REFUSE, because a false refusal is the status quo while a false eligibility asserts a completion that never happened |

No finding was DEFERRED, left OPEN, or marked REPLAN, so no escalation to a `- Blocking: yes` question
was required.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-101/PR-102 could be read as "the child-table approach is unsound; REPLAN with an explicit metadata field". Repair in place or REPLAN? | Repair in place: bound the parser defensively (positional token, refuse the unparseable, one-directional comparison). | REPLAN onto an explicit `Child-Set-Complete:` field, REJECTED because the maintainer already considered and rejected exactly that in spec `77tr3o` OQ-2 (it would need backfilling to every existing orchestrator, and until then an unbackfilled parent is indistinguishable from an incomplete one). Substituting my judgement for a recorded maintainer decision is not the reviewer's call. | spec `77tr3o` OQ-2 (lines 228-236); `plan-review.md:226-229` | yes |
| D-2 | Should the four real column shapes be REQUIRED fixtures, or is one synthetic shape plus a note enough? | Required fixtures, copied from the real tables. | A single synthetic uniform table plus a warning comment, REJECTED because the shapes are the defect: a parser validated on this plan's own format is validated on the one layout guaranteed not to break it, and PR-101 exists precisely because prose about the table was trusted over the tables. | measured layouts of all five `-00-` plans; `plan-review.md:459-463` (production-equivalent dependencies where differences matter) | yes |
| D-3 | Is PR-101 a BLOCKER? | HIGH. | BLOCKER, REJECTED: the failure direction is a FALSE REFUSAL (crash or vacuous pass on `rununify`), which leaves an orchestrator lingering exactly as today rather than retiring a Set that is not done. No data loss, no invariant violated in the durable record. It is a material correctness and required-coverage gap. | `plan-review.md:504-509`; spec OQ-2's "worst case is a FALSE REFUSAL ... never a false retirement" | yes |
| D-4 | Readiness value. | `go-pending-approval`. | `go`, REJECTED (`Status` is `reviewed`, no human sign-off). `no-go`, REJECTED (no open question, no unfixed BLOCKER/HIGH; the workflow reserves it for genuine not-ready conditions). | `plan-review.md:531-546`; `.aw/records/plans/README.md:45-51` | yes |

No `Reversible: no` decision was taken.

### Verified claims

Re-measured by execution, not by re-reading. `selectors.resolve(Path('.'),'plans',<setid>)` plus
`ipd_lint.parse(...).meta_fields` for every live Set:

- `wslayout`: 6 paths -> 5 children Orders 1-5 all `executed`, orchestrator `rh5tt6` Order 0 `approved`.
  Matches E-01's stated outcome exactly.
- `lanectn`: 7 paths -> `cqx5v7`/`lhmrhx`/`y5od1h`/`604wra` `executed`; `nna8yz` (Order 2) and `xdr83v`
  (Order 5) `approved`; orchestrator `h0zljh` `approved`. Matches E-02's stated outcome.
- `rununify`: 3 paths -> `2r306y`/`818uru` `executed`, orchestrator `5e4sb6` `approved`. Confirms spec
  2.5's guard: a naive "all existing members executed" rule WOULD retire it.
- The `03+` row exists as claimed, and so does a `last` row the plan never mentioned.
- `runprofile`: 7 paths, Orders 0-6, with `kgpptv` at Order 6 `reviewed` and only Orders 01-05 declared
  in the table. This is PR-102's counter-example.
- The `## Child IPDs, sequence, and dependencies` HEADING is identical in all five orchestrators and is
  schema-enforced (`ipd_schema.py:59` `H_CHILD_IPDS`, in `ORCHESTRATOR_H2_ORDER`), so keying on the
  heading is safe even though keying on the table body is not. This is why the fix bounds the parser
  rather than abandoning the approach.
- `selectors.resolve` returns a `Resolution` namedtuple (`paths`, `kind`, `rejected_kind`, `selector`),
  and the paths INCLUDE the orchestrator, so a naive path count over-counts children by one. V-01 now
  requires showing the reader separates them by `Kind`/`Order`.
- `nna8yz`'s lane facts hold: `aw/lane/nna8yz` tip is `396ddebf` and
  `git merge-base --is-ancestor aw/lane/nna8yz HEAD` returns false, so its work is genuinely unintegrated.
- `substantially-complete` is in `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:274`) as the plan says, and
  keeping that out of scope is correct per spec Section 4.
- The cited `4517 passed, 3 skipped, 4 xfailed` baseline is explicitly framed as stale and
  must-be-re-measured, with node-id comparison mandated. Correct as written; not a finding.

### Right-sizing and conceptual density

Four E-items, each one concern: a membership reader, an eligibility predicate, a row-authoring check, and
tests. E-03 grew the most in this review but remains a single deliverable (one parser) with one
test-surface. `Scope-Paths` is two files. No split recommended.

### Not verified, and stated as such

I did not implement the predicate or run the suite. Every code and data claim above is either a read of a
named `path:line` or the output of a read-only Python call against the plans tree at `9afee369`. The
plan's own V-items must produce the runtime evidence.
