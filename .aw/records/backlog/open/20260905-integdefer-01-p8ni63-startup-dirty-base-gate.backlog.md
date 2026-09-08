- Id: p8ni63
- Status: open
- Blocks-Release: next
- Set: integdefer
- Priority: high
- Work-Kind: bug
- Summary: both runners start against a dirty main tree without warning, then refuse integration hours later: add a startup dirty-base gate with an explicit override

## Workflow history
- 2026-09-05 created (aw backlog): both runners start against a dirty main tree without warning, then refuse integration hours later: add a startup dirty-base gate with an explicit override

PARTIALLY OBSOLETE 2026-09-08, VERIFIED. READ THIS BEFORE GRADUATING: approved plan `nna8yz`
(`lanectn` Order 02, `- Status: approved`, queued to execute) already delivers a large part of what this
item asks for, and the graduating plan MUST NOT re-implement it. `nna8yz` E-05 adds "a pre-launch guard
that refuses an unattended isolated turn when the target checkout has dirty TRACKED paths, naming them,
before any worker process is spawned", in shared `agent_workflows/lane_containment.py` with both drivers
wired, tested by `tests/test_lane_clean_base.py`.

THAT COVERS THE MOTIVATING INCIDENT, which is the honest and uncomfortable part. Run
`run-20260905T050043Z-639569` was an ISOLATED run (verified: its `state.json` carries
`options.isolate_worktree = true`, and isolation is the default), and the dirt was
`agent_workflows/oc_runipd.py` plus `agent_workflows/agy_runipd.py`, both TRACKED. So `nna8yz` E-05
would have refused before the first worker spawned, roughly 3 hours and $40 earlier than the integration
refusal this item was filed about. Do not graduate a plan whose justification is that incident without
saying so.

WHAT SURVIVES, and it is narrower than the item above describes. Graduate ONLY these:
  1. UNTRACKED DIRT IS DELIBERATELY OUT OF SCOPE FOR `nna8yz`, in as many words: "Untracked files are
     deliberately EXCLUDED (a lane is made from a commit, so untracked content was never silently
     omitted the way an uncommitted tracked edit is, and refusing on it would make an unattended run
     unstartable in any working checkout)." That exclusion is REASONED AND CORRECT for a lane guard, and
     it is precisely the `aw install` case this item names: 130+ files written into the working tree,
     uncommitted, MOSTLY UNTRACKED. So the incident class the maintainer observation calls out is the one
     `nna8yz` will not catch. Any surviving work must justify itself on the UNTRACKED case, and must not
     silently reverse `nna8yz`'s exclusion for the tracked one.
  2. RUN-START versus PER-ITEM PRE-LAUNCH. `nna8yz` guards each isolated turn at spawn; this item asked
     for `initialize_run` (`oc_runipd.py:2769`, `agy_runipd.py:1814`), i.e. ONCE, before the queue is
     frozen and before any cost is incurred. The difference is real but SMALL once E-05 lands (the first
     spawn follows shortly after initialize), so the graduating plan must state plainly what the earlier
     check buys beyond it, or drop this part.
  3. `--no-isolate-worktree` RUNS ARE UNGUARDED BY `nna8yz`. E-05 guards an "unattended ISOLATED turn".
     A run started with `--no-isolate-worktree` shares the main tree and gets no guard at all. That is a
     genuine surviving hole and is the strongest remaining justification here.
  4. THE CONSENT FLAG. `--allow-dirty-base` does not exist at HEAD (grepped: zero hits in
     `agent_workflows/`). Whether `nna8yz` E-05's refusal grows an override, and what it is called, is
     unsettled and is a real deliverable.

WHAT MUST NOT BE GRADUATED: a second whole-tree dirty check in `runner_shared.py` duplicating E-05's,
and any re-statement of the tracked-file case as though it were unaddressed. Sequence the surviving work
AFTER `nna8yz` and cite it, or the two guards will be written twice into the same two drivers, which is
the duplication `cnwy8g` exists to stop.

THE DEFECT. Neither runner checks whether the main tree is dirty before starting a run.
`initialize_run` (`oc_runipd.py:2520`, `agy_runipd.py:1540`) validates the git repo, the manifest,
and the dependency graph, and never once looks at working-tree state. The ONLY dirty check in either
runner is `dirty_tree_overlap` (`oc_runipd.py:1849`), which runs at INTEGRATION time, hours later.

MEASURED CONSEQUENCE. Run `run-20260905T050043Z-639569` started at 05:00:43 with
`agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` ALREADY DIRTY in main. The
runner said nothing. It then spent 3 hours and roughly \$40 executing `76gsmv` before discovering
at 08:06:32 that it could not integrate, for a reason that was fully knowable at 05:00:43. Two more
items (`txc9l1` at 10:48, `uyeko5` at 11:47) hit the identical overlap on the identical two files
over the following four hours. The condition was present at startup and stable throughout; only the
discovery was late.

Suspected origin in that incident: another agent ran `aw install` in this repo, which writes many
files into the working tree.

THE FIX. A startup preflight in SHARED code (`runner_shared.py`), called by both
`initialize_run`s, that:
  1. reports the dirty paths in main;
  2. states the consequence plainly - any lane whose changed files overlap these paths WILL be
     refused at integration;
  3. REFUSES to start by default, requiring an explicit `--allow-dirty-base` (or a config default)
     to proceed.

Refuse-with-consent, not warn-and-continue: a warning in a log nobody reads at 05:00 is what we have
today in effect. Put it in `runner_shared.py` with both runners calling it, NOT copy-pasted into
two files; see `cnwy8g` on the 40-symbol import coupling between the two drivers.

ON "KNOW YOUR OWN DIRT" - AN IMPORTANT CORRECTION. The obvious deep fix is to let the runner
distinguish its OWN dirt from a co-worker's, which is what `a8eufb` (open) covers via the
`AW-Run:`/`AW-Item:` commit trailers. That is NECESSARY BUT INSUFFICIENT HERE, and the reason
matters: trailers mark COMMITS. A stray `aw install` writes 130+ files into the WORKING TREE,
uncommitted, carrying no trailer at all. The trailer mechanism would not have caught the incident
that motivated this item. Do not close this item by pointing at `a8eufb`.

MAINTAINER OBSERVATION (2026-09-05), which shapes the design: on at least two occasions an agent did
NOT REALIZE the pollution was its own - including the `aw install` case that added 130+ files. So
ownership cannot be inferred from provenance the runner does not have, and cannot be assumed known
by the agent either. What the runner CAN do is present the facts and require an agent to establish
the answer, exactly as `build_recovery_lane_notice` (`runner_shared.py:493`) already tells a
resuming agent "this is NOT a clean start... Establish the CURRENT state yourself". Startup should
do the same for a dirty base.

HONEST LIMIT, and why the deterministic half must carry the weight: `k1nity` measured that
informing an agent is NECESSARY AND NOT SUFFICIENT (it observed byte-identical duplicate work on 3+
resumed runs despite an explicit prompt notice). So the gate must REFUSE by default, and no amount of
agent reasoning may bypass it without the explicit flag.

WHAT THIS DOES NOT DO. It does not resolve dirt, does not stash, does not reset, does not clean.
This repo's policy for un-owned dirty state is to leave it strictly alone
(`oc_runipd.py:1674`; AGENTS.md shared-checkout rules). The gate reports and refuses; a human
decides.

RELATED. Sibling of the integration-deferral ladder in this Set (the ladder handles dirt that appears
DURING a run; this handles dirt present BEFORE it). `z2isfg` (executed) is prior art for a
begin-time dirty gate and for the lesson that a refusal message must not tell the operator to commit
or stash work AGENTS.md forbids them to touch - reuse that wording discipline here. `a8eufb` (open)
would improve the message quality once ownership is knowable, but is not a substitute.
