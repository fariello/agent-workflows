- Id: 3wofej
- Status: done
- Graduated-To: 3wofej
- Set: 3wofej
- Priority: low
- Work-Kind: chore
- Summary: Managed AGENTS.md instruction text says addopts supplies -m 'not slow' but the actual value is -m 'not slow and not livecorpus'

## Workflow history
- 2026-10-01 set (aw backlog): closed by aw oc run: IPD zb81ah executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-3wofej-01-zb81ah-correct-the-managed-suite-instruction-s-stale-marker-filter.ipd.md); evidence .aw/records/plans/executed/20260930-3wofej-01-zb81ah-correct-the-managed-suite-instruction-s-stale-marker-filter.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053053Z-3200037: zb81ah
- 2026-09-28 created (aw backlog): Managed AGENTS.md instruction text says addopts supplies -m 'not slow' but the actual value is -m 'not slow and not livecorpus'

FILED AS THE CARRIER FOR FINDING `F6` OF PLAN `kmzude` (set `testlocality`, from backlog `5mc38x`), which found this while measuring how the default test run treats deselected and skipped tests. Out of scope there: that plan's `- Scope-Paths:` covers `GUIDING_PRINCIPLES.md`, `CONTRIBUTING.md` and one test file, while this fix lands in `agent_workflows/engine.py`, whose text installs into EVERY managed repository.

THE DEFECT. The managed instruction paragraph `HOW TO RUN THE SUITE` tells every agent that "`pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`". The ACTUAL value in `pyproject.toml` is:

    addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"

So a second marker category is deselected that the instructions never mention. The string literal to correct is in `agent_workflows/engine.py` (the `-m 'not slow'` fragment inside that paragraph's text); `AGENTS.md` is GENERATED from it and must NOT be hand-edited, or the next install overwrites the fix.

WHY IT MATTERS, and why it is `chore` rather than `bug`: no shipped behavior is wrong and no user waits on anything, so it fails the user-perceptible-impact test for `bug`. The cost is that an agent trusting the instruction does not know `livecorpus` tests were deselected, and the `livecorpus` marker exists precisely because those tests are the ones an agent authoring a plan can turn red. An agent that does not know the category exists cannot reason about it. `tests/deselect_notice.py` does announce the deselection at run time, which limits the harm.

SHAPE OF THE FIX: correct the literal to match `addopts`, and consider stating the two categories by NAME so a future third category is a visible omission rather than a silent one. Check whether any other managed text repeats the stale filter before assuming a single site.
