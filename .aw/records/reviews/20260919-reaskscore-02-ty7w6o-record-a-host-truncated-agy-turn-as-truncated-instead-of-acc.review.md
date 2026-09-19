# Review findings: plan ty7w6o

- Subject-Id: ty7w6o
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `9a04b829`. The plan on disk was byte-identical to the sealed lane input (`diff`
reported no difference) and `git status --porcelain` was empty, so no pre-review snapshot was needed.
Structural preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0; after
the revisions `--phase review-finalize` reports only the expected `IPD-Q501` for the blocking question
this review escalated.

THE SIGNAL-ONLY DESIGN IS THE RIGHT CALL AND ITS PREMISES HOLD. Splitting observation from decision is
what keeps this plan's blast radius at "the driver records a fact it was discarding", and I verified
each structural premise against the code rather than accepting its prose. Confirmed: the stream really
does carry the host's own diagnostics, because `popen_kwargs` sets `stdout=subprocess.PIPE` with
`stderr=subprocess.STDOUT`; the every-line seam really does fan each raw line out to five existing
consumers (`statusline.touch`, `watchdog.touch`, `turn_bounds.note_progress`, `runner_stop.poll_stop`,
`missing_input.note_line`) independently of `output_mode`; `MissingInputObserver` really is the
non-blocking per-turn precedent described, with "IT DOES NOT BLOCK THE WORKER" in its own docstring;
`DEFAULT_TIMEOUT` really is `"240m"`; the `--print-timeout` overlap comment really is grep-pinned by
`test_the_overlap_is_documented_in_the_code_naming_which_fires_first` for three literals (and the
wrapped `"EXPECTED\n        # TO WIN"` form is what matches, so the warning not to reflow it is real);
and `q1z9gn`'s falsified history sentence is quoted verbatim and accurately in F-6.

WHERE THIS REVIEW SPENT ITS EFFORT: two of the five items could not have been performed as written, and
one of those fails SILENTLY. Every finding below was measured, two by executing the shipped code.

**1. E-05's mechanism cannot append history and fails silently, so the item would be ticked having
written nothing.** E-05 instructed the executor to append a correction to `x7wfyx` "via `aw backlog
set` so the history entry is tool-written". I ran the real command against a throwaway copy of the item
in a scratch repo:

```text
$ aw backlog set open x7wfyx --message "PROBE same-status history append" --no-commit --yes
- >  backlog     20260918-x7wfyx-01-x7wfyx  [medium]  [blocking]  unchanged

FILE CHANGED? False
PROBE message present in file? False
```

The cause is structural rather than a missing flag. `status_set.apply_status_change` computes
`content_changed` and `path_changed` and returns early when both are false; the `## Workflow history`
write sits AFTER that early return. So a same-status call cannot append history by construction, there
is no `--force`, and `aw backlog` exposes only `new|set|check`. The verb that does exactly what E-05
wants exists for the sibling type and has no backlog twin: `aw specs note` is documented as "Append a
workflow-history record to a spec WITHOUT changing its status. Use to log a decision, review, or
correction." This is the worst shape of defect available to a records-correcting item: the command exits
0, prints a reassuring line, `aw backlog check` still passes, and the correction the item exists to make
does not exist. Escalated as blocking OQ-04 rather than fixed, because the three available routes differ
in what they ASSERT about the item (a body-prose edit asserts nothing; `set graduated` asserts a design
handoff that is only half true, since item A has no plan at all; a new `note` verb is out of scope), and
choosing is the maintainer's call. E-05 now names all three and V-05 now demands a NON-EMPTY `git diff`
plus a statement of which route was used, so whichever is chosen the silent-failure mode is closed.

**2. E-04 had no route to the attempt dict that stays inside its own declared scope.** It required
writing `attempt["host_truncation"]`, and neither obvious route is available here. `run_agy_turn` returns
a fixed 4-tuple `(rc, conv_id, log_path, argv)`, and that shape is TYPED in
`runner_shared.execute_item_core`'s own signature (`spawn_executor` and `spawn_verifier` are
`Callable[..., tuple[int, str | None, Path, list[str]]]`) and is shared with the oc twin, so returning
the record means editing `runner_shared.py`. The `attempt` dict is itself created in
`execute_item_core`. This plan declares neither that file nor a route, so an executor would discover the
gap mid-turn and would most likely edit the shared runner core, colliding with `skn8uk` and `dy9ymn`
which both declare it. Fixed by naming the one in-scope route and verifying it: `item` is already a
parameter of `run_agy_turn`, and `execute_item_core` appends the attempt to `item["attempts"]` BEFORE it
spawns (measured: append at function-relative line 152, `spawn_executor` at 499), so during the turn
`item["attempts"][-1]` IS this turn's attempt, and several `save_state` calls follow the spawn's return
so the mutation persists without a new call site.

**3. The classifier would fire on an agent that merely quotes the host's wording, and this Set makes
that concrete.** E-01 specified substring matching with no guard on the line's provenance. The stream is
the merged stdout+stderr, carrying JSONL event envelopes whose payloads hold the agent's assistant text
and tool output, so `{"event":"assistant","text":"terminating 2 background task(s) on exit"}` would
classify as a host truncation. That is not hypothetical here: `dy9ymn` and `svacmz` reproduce the host's
lines verbatim in text an executing agent reads and may echo. The separation is clean because the host's
diagnostics are BARE TEXT that does not parse as JSON while every echo arrives inside an envelope, and
the driver already reads the stream that way (`render_agy_event` parses and falls through on
`json.JSONDecodeError`). I also measured that `root agent idle` matches BOTH the truncating and the
waiting form and therefore cannot discriminate; the unambiguous discriminators are `waiting up to`,
`bounded by --print-timeout` and `terminating`. Fixed in E-01 and pinned by a new V-01 control.

**4. The evidence the classifier's design rests on is not reproducible from the tree.**
`.aw/records/runs/` is empty in a lane worktree and a fresh clone, so neither cited run directory exists
and F-1, F-2, F-4, F-5 and F-7 cannot be re-verified. F-4 is the one that matters: its 3-waiting-against-
8-truncating ratio is the whole justification for the WAITING branch, and an executor who cannot find a
waiting-form example might reasonably conclude the branch is speculative and drop it, which would
reintroduce exactly the false-positive-on-healthy-turns failure the branch prevents. Recorded in
Required tests as a historical measurement not to be re-derived, along with the note that the plan's own
text is now the only tracked source of the three line forms (plus the `terminating` line in the existing
test docstring), so they must be copied from here and not tidied.

**5. Three citations are wrong, and the pattern is informative.** `agy_runipd.py:2709` is cited for the
`MissingInputObserver` construction and is actually `_raise_if_forced`; both `runner_shared.py`
citations have drifted. Every other citation in the plan (`agy_runipd.py:536`, `:712`, `:2726`, `:2894`,
`lane_containment.py:1846`, `tests/test_turn_bounds.py:357`, `:853`) is accurate. The asymmetry matches
what I measured on the two sibling plans: `runner_shared.py` grew after authoring while the other files
did not, so its offsets are the ones that rot. Re-anchored by symbol.

**6. The test docstring the plan asks to correct states the falsified premise twice, not once.**
Required tests says the `TestTheAgentIsToldNotToOutliveItsOwnCommands` docstring "should be corrected
where it says the agent chose to background". It says it in two places: "the agent started `python3 -m
pytest` as a BACKGROUND task" and, separately, "NO bound fired and none could have: the agent chose to
stop." Both are the premise F-1 falsifies. Named explicitly so a partial correction does not leave the
second sentence asserting the wrong cause.

**7. No scope fence was present**, and this plan needs one more than most: the two natural routes for
E-04 both land in `runner_shared.py`, which two siblings also declare. Added in declaration form, naming
that file specifically.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. correctness; G. executability | Ran `aw backlog set open x7wfyx --message ...` against a throwaway copy in a scratch repo: printed `unchanged`, file byte-identical, message absent. `status_set.apply_status_change` returns early when `not content_changed and not path_changed`; the `## Workflow history` write is after that return. `aw backlog` exposes only `new/set/check`; `aw specs note` ("Append a workflow-history record ... WITHOUT changing its status") has no backlog twin | E-05's mechanism cannot append history without a status change, and it fails SILENTLY: the command exits 0, prints a reassuring line, and `aw backlog check` still passes, so an executor would tick E-05 having written no correction at all. The worst shape available to a records-correcting item | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium-High | FIXED | RESOLVED 2026-09-19 BY THE MAINTAINER (`/askme`), who chose ROUTE (a), the body-prose edit, on the ground that it asserts ONLY the correction. Routes (b) and (c) were declined: `graduated` would assert a half-true handoff since item A has no plan, and adding a `note` verb is separate release-blocking work this correction must not wait behind. NO EDIT TO E-05 WAS NEEDED, because it already named (a) as its preferred route and `V-05` already demanded a non-empty `git diff` plus a statement of which route was used; the answer removed the choice, not the instruction. Re-measured at resolution time rather than trusted: the same-status call still printed `unchanged` with the file's md5 unchanged at `03436eff23acf67f690cb026931f0f30` and `grep -c PROBE` at 0, and the declined (b) was confirmed to work mechanically (file moved, history 2 -> 3, `Blocks-Release` preserved), so it was declined on what it asserts and not on whether it functions. The underlying tooling defect stays filed as backlog `x6tk1u` and `hg2oop`, both `open`, high, and release-blocking |
| PR-002 | HIGH | IN-SCOPE | C. architecture; G. executability | `run_agy_turn` returns `tuple[int, str \| None, Path, list[str]]`, typed in `execute_item_core`'s `spawn_executor`/`spawn_verifier` params and shared with the oc twin; the `attempt` dict is created in `execute_item_core`. Measured: the attempt is appended to `item["attempts"]` at fn-rel 152, `spawn_executor` is called at fn-rel 499 | E-04 required writing `attempt["host_truncation"]` but both obvious routes (widen the return tuple, or create the observer where the attempt is created) require `runner_shared.py`, which this plan does not declare and which `skn8uk` and `dy9ymn` both edit. An executor would hit the gap mid-turn and most likely widen scope into the shared runner core | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now names the in-scope route (`item["attempts"][-1]`, verified reachable because the append precedes the spawn, with downstream `save_state` persisting it), requires the resulting host asymmetry be commented at the write site, and confirms the 4-tuple stays unchanged. The host-neutral alternative recorded as non-blocking OQ-05 |
| PR-003 | HIGH | IN-SCOPE | A. correctness; B. trust-boundary input | The stream is merged stdout+stderr (`stderr=subprocess.STDOUT`) carrying JSONL envelopes with agent text and tool output; `{"event":"assistant","text":"terminating 2 background task(s) on exit"}` matches a naive substring test. `dy9ymn` and `svacmz` quote the host lines verbatim. Host diagnostics are bare text and fail `json.loads`; `render_agy_event` already splits the stream that way. Measured: `root agent idle` matches BOTH line forms | E-01 had no guard against classifying an AGENT's echo of the host's wording as a host truncation, which is a live path in this Set because two sibling plans reproduce those lines in text an executing agent reads. It also invited a `root agent idle` trigger, which cannot discriminate truncating from waiting | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | E-01 now refuses any JSON-parseable line (reusing the driver's own reading of the stream) and requires the three measured-unambiguous discriminators rather than the shared prefix; V-01 gains the agent-echo negative control with two concrete envelopes |
| PR-004 | MEDIUM | IN-SCOPE | E. testing; honest evidence | `.aw/records/runs/` is empty in this lane; neither cited run directory exists. The three line forms survive only in this plan's own text and the `terminating` line in the `TestTheAgentIsToldNotToOutliveItsOwnCommands` docstring | F-4's 3-vs-8 ratio is the sole justification for the WAITING branch and is not reproducible, so an executor who cannot find a waiting-form example may conclude the branch is speculative and drop it, reintroducing the false-positive-on-healthy-turns failure it prevents | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required tests now states the runs tree is absent, names the two tracked sources of the literals, flags F-4 as a recorded historical measurement not to be re-derived, forbids weakening the WAITING branch for lack of an example, and warns against tidying the strings since the plan is now their provenance |
| PR-005 | MEDIUM | IN-SCOPE | E. testing; G. executability | `agy_runipd.py:2709` is `_raise_if_forced`, not the `MissingInputObserver` construction; both `runner_shared.py` citations drifted. `agy_runipd.py:536`, `:712`, `:2726`, `:2894`, `lane_containment.py:1846`, `tests/test_turn_bounds.py:357`, `:853` all verified accurate | Three citations point at unrelated code, including the one an implementer would follow to find the construction pattern E-02 is modeled on. None is out of range, so none announces itself | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three re-anchored by symbol (the `MissingInputObserver(state["repo"])` construction, `perform_defect_reask`'s docstring, and the FOREGROUND prompt sentence, whose presence I verified); a conventions note records that only `runner_shared.py` offsets rot and why |
| PR-006 | LOW | IN-SCOPE | D. anti-regression; honest documentation | The docstring states the falsified premise twice: "the agent started `python3 -m pytest` as a BACKGROUND task" and "NO bound fired and none could have: the agent chose to stop" | Required tests asked for the correction in the singular ("where it says the agent chose to background"), so a literal reading corrects one sentence and leaves the other asserting the wrong cause | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Proposed changes item 6 now names both sentences explicitly |
| PR-007 | LOW | UNDER-SCOPE | G. executability; execution contract | Gate carried the honesty rule, the path-scoped commit rule, the backlog note and the lifecycle move, but no scope fence | No fence declared the intended surface for finalize-time reconciliation, and this plan is unusually exposed because both natural E-04 routes land in a file two siblings also declare | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fence added in declaration form (make the edit and justify it at finalize, never "stop and report"), naming `runner_shared.py` specifically and why |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-05's command cannot do what the item asks (PR-001). Pick a replacement route myself, or escalate? | ESCALATE as blocking OQ-04, naming three routes with a recommendation, and harden V-05 so the silent failure cannot pass whichever is chosen. | (a) Silently switch E-05 to `aw backlog set graduated`: rejected, `graduated` asserts the design is handed off, and that is only half true here since item A (the turn budget) has no plan at all, so I would be authoring a false status claim on a release-blocking item. (b) Switch it to a body-prose edit on my own authority: this is my recommendation and is probably right, but it changes what the record ASSERTS about provenance (hand-written rather than tool-written), which the item deliberately chose, so the maintainer should confirm. (c) Add a `note` verb to `aw backlog`: correct long-run fix, but a signal-recording plan is the wrong place to grow the CLI. (d) Leave E-05 as authored: rejected outright, it fails silently. | Ran the real command against a throwaway copy: printed `unchanged`, file byte-identical, message absent. `status_set.apply_status_change` early-returns before the history write. `aw backlog --help` lists only `new/set/check`; `aw specs note --help` documents the exact missing capability for the sibling type. | yes |
| D-2 | E-04 cannot reach the attempt dict from its declared scope (PR-002). Widen `Scope-Paths` to include `runner_shared.py`, or find an in-scope route? | FIND THE IN-SCOPE ROUTE: mutate `item["attempts"][-1]` from `run_agy_turn`, and record the resulting asymmetry as OQ-05. | (a) Add `runner_shared.py` to `Scope-Paths`: rejected, it would put a third concurrent hand in the file `skn8uk` and `dy9ymn` both edit, and would widen a signal-only plan into the shared runner core it was scoped to avoid. (b) Widen `run_agy_turn`'s return tuple: rejected, the shape is typed in `execute_item_core`'s signature and shared with the oc twin, so it is a cross-host contract change disguised as a one-file edit. (c) Leave the route unspecified: rejected, that is the finding; an executor would discover it mid-turn and pick (a) or (b) under time pressure. | `run_agy_turn` signature returns `tuple[int, str \| None, Path, list[str]]`, matching `execute_item_core`'s `spawn_executor`/`spawn_verifier` Callable types; measured that `item.setdefault("attempts", []).append(attempt)` precedes the `spawn_executor` call, and that several `save_state` calls follow it. | yes |
| D-3 | The classifier can fire on an agent echoing the host's wording (PR-003). Accept the risk as remote, or require a guard? | REQUIRE the JSON-refusal guard and pin it with an agent-echo negative control. | (a) Accept it as remote: rejected, and specifically wrong in this Set, since `dy9ymn` and `svacmz` quote the host lines verbatim in text an executing agent reads and may echo, so the trigger is in the corpus the classifier will run against. (b) Match the whole sentence instead: rejected, it does not help (an echo quotes the whole sentence) and it contradicts OQ-01's already-reasoned choice of a stable substring core. (c) Require the line to come from a specific fd: rejected, impossible, since `stderr` is merged into `stdout` by construction. | `popen_kwargs` sets `stderr=subprocess.STDOUT`; host diagnostics fail `json.loads` while agent echoes arrive inside envelopes; `render_agy_event` already parses and falls through on `json.JSONDecodeError`; measured that `root agent idle` matches both line forms while `waiting up to`, `bounded by --print-timeout` and `terminating` each match exactly one. | yes |
| D-4 | The cited run directories are gone, so F-4's ratio cannot be re-derived (PR-004). Drop the WAITING branch as unevidenced, or preserve it? | PRESERVE it and label F-4 a recorded historical measurement, forbidding an executor from weakening the branch for lack of a reproducible example. | (a) Drop the WAITING branch: rejected, it is the control that stops the classifier flagging healthy turns, and absence of an example in a gitignored tree is not evidence the form does not occur. (b) Ask the maintainer to restore the run directories: rejected, they are gitignored by design and a review should not request unshippable evidence. (c) Say nothing: rejected, an executor meeting an unverifiable finding needs to know whether to trust it, and this one should be trusted while not re-derived. | `.aw/records/runs/` empty in this lane; the three line forms present only in this plan and in the `TestTheAgentIsToldNotToOutliveItsOwnCommands` docstring; the WAITING branch's purpose stated in E-01 and V-01 as the load-bearing negative control. | yes |
