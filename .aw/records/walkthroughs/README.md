# .aw/records/walkthroughs/

Narrative execution walkthroughs documenting the implementation, verification, and testing results of executed plans.

Named with the uniform artifact grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>.walkthrough.md` (the legacy `YYYYMMDD-HHMM-NN-<slug>-walkthrough.md` form is still read). Walkthroughs dated at/after the repository's `walkthrough_id6` cutover must use the clustered grammar, a programmatic walkthrough (`set_records.write_walkthrough`) mints its own id6 and records the plan as `Target-Id:`, and the 11 pre-cutover legacy names stay valid. The `<id6>` in the filename identity slot is the walkthrough's OWN unique identity (DECISIONS.md D140): a walkthrough MUST mint its own id6 there and MUST NOT reuse the id6 of the plan it documents. To link a walkthrough to the plan it documents, use the typed frontmatter field `Target-Id: <plan-id6>` (the canonical directional reference), never the identity slot. `aw check`/`aw doctor` enforce this via the `check.id6-identity-slot` rule.

SETID LENGTH IS BOUNDED (catalog invariant I-17, spec `2lcqno` N8). A setid of 14 characters or
fewer is strongly preferred, a setid over 14 characters is a WARNING, and a setid over 24 characters
is REFUSED: the `--set`-taking verbs (`aw ipd scaffold`, `aw backlog new`, `aw research new`,
`aw group`) reject an over-length value, and `aw check` reports `check.setid-length-warn` /
`check.setid-length-error`. Grandfathering is PER ARTIFACT against the `cutovers.setid_length`
boundary stamped into `.aw/config/project.json` on install or update, so an artifact older than that
boundary keeps its long setid while a NEW artifact is judged. The intended consequence is that a new
artifact may NOT join an existing long-setid topic after the cutover; regroup the topic under a
shorter setid instead.

A walkthrough MAY declare `- Set:`. Doing so is not a collision because a setid is a shared cross-type topic label (DECISIONS D153 / spec `2lcqno` N1), so a walkthrough and a plan on the same topic legitimately share the token. The programmatic helper (`set_records.write_walkthrough`) does not write the field, so an author adds it by hand when grouping by Set is desired.


Walkthroughs are OPTIONAL and are not expected per executed plan. Most executed plans do not have one, and that is fine: the authoritative evidence that a plan was implemented and validated lives in the plan's own verification items (with pasted runner output), the run ledger, and the commit history, not here. Write a walkthrough only when a narrative of what actually happened during an execution adds material value beyond those records (for example, notable deviations from the plan, surprises, or a sequence worth preserving for handoff). Do not create one by default.

When a walkthrough is written, it may capture command logs, test results, and screenshots or recording paths. If an agent drafts a walkthrough in a private, hidden, or tool-internal scratch or "brain" space, the tracked copy here is the source of truth (see AGENTS.md); the private copy is disposable.

## Walkthroughs are never durable carriers

A walkthrough carries no lifecycle status and is not tracked in the attention contract (`tracked=False`). It is filename-only checked and nothing scans its contents for outstanding work, so an obligation recorded only in a walkthrough is invisible to every gate and will never be revisited.

Consequently, `Carrier-Evidence` explicitly refuses paths under the walkthroughs tree (both `.aw/records/walkthroughs/` and legacy `.agents/docs/walkthroughs/`). Leftover work, defects, or follow-ups discovered during execution must be handed off to an open backlog item (`aw backlog new`) or a child or follow-up plan, never parked in a walkthrough.

## Attention contract and Phase 3 admission verdict

Walkthroughs remain excluded from `aw attention` (`tracked=False`).

The implemented attention spec (`20260808-1945-01`) Phase 3 requires four criteria for admission into the tracked attention view:
1. A real owner verb
2. A closed native status contract
3. A history contract
4. An exhaustive mapping from native status to attention class

The walkthroughs tree fails three measured criteria:
- No owner verb: no `aw walkthroughs` command exists to own writes or manage lifecycle transitions.
- No closed native status contract: 22 of 25 files carry no `- Status:` line at all, while the 3 files that mention status carry unparseable prose or quoted transcripts (`IN PROGRESS - Stage 1...`, `PROPOSAL for maintainer review...`, and a quoted `approved <- unchanged`).
- No history contract: exactly 1 of 25 files carries a `## Workflow history` heading (a heading match; a substring search returns 3 of 25, of which 2 merely mention the phrase in body prose).

The fourth criterion (an exhaustive mapping) fails as a direct consequence of having no closed native status contract to map over.

Because walkthroughs are excluded from the attention board, running `aw attention <id6>` for a walkthrough artifact does not fail as a missing artifact or typo. Instead, `aw attention` identifies that the selector resolves to an artifact in an excluded tree, reports the exclusion reason, and points the operator to `aw find <id6>` to view the artifact.
