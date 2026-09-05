# Review: one shared needs-review predicate and the draft admission gate

- Plan-Id: 6ypimw
- Reviewed-At: 2026-09-04
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `d03316d8`. The target plan was committed at `0ee800f4` and unchanged, so
the pre-review snapshot was correctly skipped. `aw ipd lint` conforming at `--phase author` before
review and again at `--phase review-finalize` after revisions.

THIS PLAN'S MEASUREMENTS ARE THE MOST ACCURATE IN THE SET, and that is worth saying before the
findings. I verified every central claim independently and each one held: `_needs_review` tests
`st == "to-review"` while `determine_action` routes both `to-review` and `draft` to review; diffing the
two selector branches yields exactly one hunk plus comment differences, the `setid`/`_setid` loop
variable, so F-2's "true verbatim duplicate" is precise rather than rhetorical; `all`'s
`actionable_statuses` really does contain `draft`, which corroborates F-3's reading that the divergence
is accidental; every `run_selection_policy` primitive is at the cited line; and `decide` still has zero
callers, so F-7's hazard is live. The plan also correctly anticipated the two things most likely to be
got wrong by an executor, `ACTION_UNDETERMINED` and the terminal-directory exclusion.

TWO FINDINGS WOULD HAVE PRODUCED AN UNSAFE OR UNSHIPPABLE RESULT.

PR-001 is the serious one, and it is a hazard the plan inherited from the spec rather than invented.
E-03 and E-04 require spec 2.5a's interactive `run drafts` confirmation, and this driver may have no
safe surface for an interactive prompt at all. It calls `input()` nowhere. It hands every child process
`stdin=subprocess.DEVNULL` for exactly this reason, and the comment there does not theorize, it
measures: "a nested `aw` sees the operator's TTY, believes it may prompt, and blocks on input()
forever ... Verified: a finalize wedged 1h49m this way". The single shipped prompt,
`_lane_reclaim_prompt`, is wrapped in hard constraints its own docstring enumerates: a global disable
flag, a real TTY required on BOTH stdin and stderr, an unanswered prompt falling through to the
automatic decision rather than blocking shutdown, and the principle that "the content-based decision is
the authority; this only front-runs it". A blocking prompt added to the queue-build path would
therefore risk wedging an unattended run indefinitely, and an unfenced one would be dead code in every
real invocation. The plan said "passing the real TTY state" as though the TTY were the only question;
the real question is whether prompting is permissible here at all. E-04 now forces an explicit choice
and forbids a bare `input()`. Both permitted answers converge on the same outcome for an ungated draft
(excluded, rest proceeds), so no draft is admitted without authorization either way.

PR-002 is a gap between two instructions that are individually right. E-02 says to take completeness as
an INPUT (correct, and F-5 explains why the pure module cannot compute it) and to source it from
`authoring_placeholders_resolved` (correct, and F-6 explains why a second heuristic would diverge from
the `check.ipd-draft-ready-to-review` nudge). But that function takes plan TEXT, and the caller has
none: `build_dynamic_manifest` stores `set`, `file`, `status`, `order`, `dependencies`, `kind`, and
`from_backlog`, with no text and no completeness field. Worse, `expand_selectors`'s `repo` parameter is
`Path | None = None` and the sweep branch never touches it today. So an executor following E-02
literally reaches a point where the answer must come from somewhere and the two obvious improvisations
are both wrong: crash on a `None` repo, or default to "complete" and sweep up the stubs that F-5 exists
to keep out. E-02 now requires reading only `draft`-status candidates and failing safe to not-swept.

FOUR SMALLER CORRECTIONS.

PR-003: "the single point where the queue is built, BEFORE it is frozen" names no actual site, and these
runners have several plausible ones. I pinned it to `initialize_run` immediately after
`expand_selectors`, beside the existing `enforce_dependency_preflight`, which is already the
"refuse before any durable state exists" seam and therefore the site that satisfies spec 2.5a's
before-any-lease-or-session requirement by construction.

PR-004: E-03 was told to keep the module pure but also to "record ... in the run ledger", which reads as
permission to write from the policy module. `MixedTypeRecord`'s docstring already settles this: the
module "RETURNS them; it does not write them", because writing needs a live run's ledger store. Made
explicit so purity is not broken for convenience.

PR-005: two measurements were stale in ways that matter differently. The policy suite is `65 passed`,
not the 26 the plan claims, which is harmless but signals the citation was not re-run. The population
figure is the one worth fixing: F-9 says 1 plan at `to-review`, and it is now 3, because this Set's own
reviews are generating them. F-9's conclusion is unaffected and honest (still zero draft plans, so the
gate has nothing to gate and the argument is correctness not volume), but a stale count invites an
executor to quote rather than re-measure.

PR-006: the `default=None` instruction is right while its stated reason is not quite. `uyeko5`'s review
established that the shipped `--full-auto` on resume OVERWRITES the frozen option when passed, so
`default=None` buys "an omitted flag cannot clobber", not "a policy-changing flag is refused". Left the
pattern, corrected the property to prove, so nobody extrapolates a refusal this plan does not need.

Zero findings were deferred and zero left open. OQ-01 was already RESOLVED by spec 2.5a with its reason
recorded, and I confirmed the reasoning holds rather than reopening it.

Baselines measured for attribution: `tests/test_run_selection_policy.py` is `65 passed` at `d03316d8`;
3 plans at `to-review`, 0 at `draft`, 2 draft specs.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | C. Operability / B. Safety (an interactive prompt can wedge an unattended run) | `oc_runipd.py:832-835` (`stdin=subprocess.DEVNULL`, "blocks on input() forever ... Verified: a finalize wedged 1h49m this way"), `:1614-1628` (`_lane_reclaim_prompt` HARD CONSTRAINTS: disable flag, TTY on stdin AND stderr, never blocks, unanswered falls through, "the content-based decision is the authority"), `:1617` ("these runs are non-interactive by design and usually unattended"); `grep -n "input(" agent_workflows/oc_runipd.py` finds only those comments, never a call | SPEC 2.5a's INTERACTIVE CONFIRMATION MAY HAVE NO REACHABLE SURFACE ON THIS DRIVER, and the plan assumed it did. E-03/E-04 require the typed phrase `run drafts` in an interactive terminal and describe the wiring as "passing the real TTY state", as if TTY detection were the only question. It is not: the driver deliberately never prompts, and the one shipped prompt is fenced by a never-block rule adopted after a measured 1h49m wedge. A naive blocking prompt at queue build could hang an unattended run indefinitely and silently; an unfenced prompt would be dead code in every real invocation. Either way the plan as written could be "completed" while shipping something unsafe or inert. | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now requires an EXPLICIT stated choice: (a) follow the `_lane_reclaim_prompt` precedent exactly (TTY on both streams, honor the disable flag, never block, unanswered falls through to EXCLUDE, which equals the unattended no-flag outcome so a timeout cannot admit a draft), or (b) ship flag-only and amend spec 2.5a with `aw specs note` recording that the interactive half has no reachable surface here. A bare blocking `input()` is forbidden by the scope fence. V-04 requires proof of whichever applied, and the honesty rule makes non-blocking the third load-bearing evidence item. Recorded as F-10; Scope check and Spec-sync updated so the likely amendment is expected rather than exceptional. |
| PR-002 | BLOCKER | UNDER-SCOPE | A. Correctness (the completeness input has no data source, and both improvisations are wrong) | `oc_runipd.py:2205-2232` (`build_dynamic_manifest` stores set/file/status/order/dependencies/kind/from_backlog, no text), `:2235-2239` (`repo: Path \| None = None`), `:2245-2281` (the sweep branch never reads `repo`); `ipd_authoring.py:122` (signature takes `plan_text`) | E-02's TWO CORRECT INSTRUCTIONS DO NOT CONNECT. "Take completeness as an INPUT" and "source it from `authoring_placeholders_resolved`" are each right, but that function needs plan TEXT and the caller has none: the manifest carries no text and no completeness field, and `expand_selectors`'s `repo` is optional and unused in the sweep branch. An executor reaching that gap has two obvious improvisations and both are defects: crash when `repo` is `None`, or treat unknown completeness as complete and sweep up the incomplete stubs that F-5 exists to exclude. The plan never names the file read it actually requires. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now requires the CALLER to read text for `draft`-status candidates only (not the corpus), keeping the predicate pure, and to fail SAFE to NOT-swept when `repo` is absent or a file is unreadable, never crashing and never optimistically including. V-02 demands both fail-safe cases pasted. Recorded as F-11 and surfaced in the Scope check as an added, justified cost. |
| PR-003 | MEDIUM | IN-SCOPE | G. Plan executability (the call site is unnamed in modules with several plausible ones) | `oc_runipd.py:2553` (`expand_selectors`), `:2554-2566` (`enforce_dependency_preflight` with its "FAIL CLOSED ... before the run directory exists" comment), `:2567-2570` (run dir created after); agy `:1570` | "WIRE IT AT THE SINGLE POINT WHERE THE QUEUE IS BUILT" NAMES NO SITE. Spec 2.5a requires the gate before any lease or session, and these runners have several places that plausibly qualify (selector expansion, preflight, run-dir creation, queue freeze, `run_queue` entry). Choosing wrongly satisfies the words while violating the requirement, for instance gating after the run directory exists, which would leave durable state behind a refused admission. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 pins the site to `initialize_run` immediately after `expand_selectors` and beside `enforce_dependency_preflight`, which is already the established refuse-before-durable-state seam, with both hosts' line references. V-04 requires pasting the call site showing no run directory, lease, or session exists yet. |
| PR-004 | MEDIUM | IN-SCOPE | C. Architecture (an instruction invites breaking the module's stated purity) | `run_selection_policy.py:235-248` (`MixedTypeRecord`: "This module RETURNS them; it does not write them. Writing needs a live run's context (the ledger store)"); `oc_runipd.py:1347` and following (`events.jsonl` append seam) | E-03 IS TOLD TO KEEP THE MODULE PURE AND ALSO TO "RECORD ... IN THE RUN LEDGER". Read together those license a filesystem write from a module whose purity is its documented invariant and the reason every branch is testable. The codebase already resolved this exact tension for the mixed-type gate by returning a typed record for the caller to persist, but the plan does not point at that convention, so an executor could reasonably write from the policy module and believe both instructions were satisfied. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires returning a typed record mirroring `MixedTypeRecord`, citing its return-not-write docstring; E-04 owns persistence via the runner's existing `events.jsonl` seam. The scope fence forbids the policy module writing the ledger, and V-04 requires showing the runner wrote it from the returned record. F-4 extended with the convention. |
| PR-005 | LOW | IN-SCOPE | A. Correctness (two stale measurements, one that invites quoting instead of measuring) | re-measured at `d03316d8`: `python3 -m pytest tests/test_run_selection_policy.py` -> `65 passed` (plan claims 26); `aw find plans --status to-review` -> 3 (plan claims 1), `--status draft` -> 0 (unchanged), draft specs -> 2 (unchanged) | TWO FIGURES ARE STALE AND ONE MATTERS. The test count (26 vs 65) is harmless but shows the citation was not re-run. The population count does matter: F-9 says 1 plan at `to-review` and it is now 3, because this very Set's reviews are producing them, so the number moves during the Set's own lifetime. F-9's CONCLUSION is unaffected and remains honest (zero draft plans, so the gate gates nothing today and the justification is correctness rather than volume), but a stale figure invites an executor to quote it rather than re-measure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-4 and F-9 updated with the re-measured values, the movement explained (this Set generates `to-review` plans), and the executor directed to re-measure. Required-tests records `65 passed` as the pre-change baseline so a regression is attributable. |
| PR-006 | LOW | IN-SCOPE | A. Correctness (a correct instruction with a slightly wrong stated reason) | `oc_runipd.py:6093-6095` (`start`: `BooleanOptionalAction`, `default=False`), `:6168-6170` (`resume`: `default=None`); `uyeko5` PR-002 measured that the resume handler OVERWRITES `state["options"]["full_auto"]` when the flag is passed | THE `default=None` RATIONALE IS INCOMPLETE. The plan says the pattern exists "so an omitted flag cannot clobber frozen state", which is true, but `uyeko5`'s review established that a PASSED `--full-auto` on resume overwrites the frozen option rather than being refused. So the property to verify is specifically the OMITTED case; an executor reading the plan's phrasing as "resume refuses policy-changing flags" could implement a refusal for `--allow-drafts`, diverging from the shipped sibling for no reason this plan needs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-12 with both line references and the cross-reference to `uyeko5` PR-002; E-04 and the Required-tests bullet now state that the property to prove is that an OMITTED flag preserves frozen state, explicitly not a refusal of a passed flag. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001 found spec 2.5a's interactive confirmation may be unimplementable safely here. Should the review CHOOSE between the fenced prompt and flag-only, or require the executor to choose and state it? | REQUIRE THE EXECUTOR TO CHOOSE AND STATE IT, with both options fully specified and the unsafe third option forbidden. | (a) Decide "flag-only" now. Rejected: it would amend an approved spec's requirement from a review, on evidence the executor can verify more cheaply with the code in front of them, and the fenced precedent genuinely exists and genuinely works, so foreclosing it would discard a legitimate option. (b) Decide "fenced prompt" now. Rejected: whether a fenced prompt is worth its complexity depends on whether any real invocation of these drivers has a TTY on both stdin and stderr, which is an execution-time observation, and if the answer is none then the prompt is dead code that must still be maintained. (c) Leave the plan as written. Rejected outright: it points at "the real TTY state" as if TTY detection were the only question, so the most likely implementation is a plain blocking prompt, which is exactly the 1h49m wedge the codebase already paid for once. | `oc_runipd.py:832-835` records the wedge as MEASURED, not theoretical; `:1614-1628` proves a safe fenced pattern exists in-tree with its constraints enumerated; both permitted options converge on EXCLUDE-and-proceed for an ungated draft, so operator-visible safety is identical either way and only the ergonomics differ; the repository's own rule that a spec divergence must be amended with `aw specs note` rather than absorbed silently | yes |
| D-2 | PR-002 requires reading plan text at the selection call site. Should the manifest instead CARRY a completeness field, computed once during discovery? | NO. Read at the call site, bounded to `draft`-status candidates. | (a) Add a completeness field to `PlanRecord` and the manifest. Rejected: `PlanRecord` and `build_dynamic_manifest` are shared discovery structures consumed by both runners and by `runner_shared`, so widening them reaches beyond this plan's fence into the modules `rununify` is consolidating and three other pending plans edit; it would also compute completeness for every plan on every run when only drafts need it. (b) Have the pure predicate read the file itself. Rejected: it destroys the module's documented purity, which is the property that makes every branch testable and which this plan's own fence protects. (c) Cache it in the manifest only when a draft is present. Rejected as the worst of both: a conditionally-present field is a schema ambiguity, and a hand-written manifest (which the repo ships) would silently lack it. | `run_selection_policy.py`'s purity invariant is stated in its module docstring and protected by this plan's scope fence; `oc_runipd.py:2205-2232` shows the manifest is a shared compiled structure; only `draft` needs the check because every other status is answered by `_ACTION_TABLES` alone (`:126-138`); `expand_selectors` already accepts `repo`, so the read needs no signature change | yes |
| D-3 | PR-003 pinned the gate's call site. Should it be `initialize_run` (before the run directory) or `run_queue` (where execution begins)? | `initialize_run`, immediately after `expand_selectors` and beside `enforce_dependency_preflight`. | (a) `run_queue`. Rejected: by then the run directory, state file, and frozen queue all exist, so a refused draft admission would leave durable state behind and spec 2.5a's "before any lease or session" would be satisfied only in the narrowest sense. (b) Inside `expand_selectors`. Rejected: that function is pure selector resolution consumed in several contexts and returns a list of id6s; embedding an operator interaction in it would make selector resolution interactive, which is the kind of hidden side effect the runner has been repeatedly refactored to remove. (c) Leave it unnamed. Rejected: PR-003. | `oc_runipd.py:2554-2566` states the precedent explicitly, failing closed "BEFORE any host session starts (and before the run directory exists, so a refused run leaves no durable state to reconcile)", which is verbatim the property spec 2.5a wants; the run directory is created after, at `:2567-2570` | yes |
| D-4 | F-9 records zero draft plans, so the draft gate gates nothing today. Does that make the gate half of this plan premature, and should it be deferred until something needs gating? | NO. Keep it, and keep the population honestly recorded as not being the argument. | (a) Defer the gate, ship only the shared predicate. Rejected: the predicate change is precisely what MAKES complete drafts sweepable, so shipping it without the gate would silently start promoting `draft` to `to-review` from a status selector, which spec 2.5a explicitly forbids as a lifecycle write the operator did not name. The gate is not an addition to the predicate change, it is the authorization for it. (b) Ship the gate and claim it improves throughput. Rejected: there are zero draft plans, so that claim would be false; the plan already forbids it and the honesty rule repeats it. (c) Widen to spec discovery so the gate has real subjects. Rejected: that is `5slbpi`'s scope and needs `eyh1fu` first. | Spec `25kzda` 2.5a requires the gate for exactly the admission path E-02 creates, so the two are one change; the plan's own F-9 and Scope check already state the population honestly rather than inflating it; `5slbpi` is the named owner of cross-type coverage and depends on `eyh1fu` | yes |
