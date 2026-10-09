# IPD: Route the noun-verb backend adapter through resolve_verb_repo_root so bare index/group/rename/archive climb

- Date: 2026-10-07
- Kind: child
- Concern: Found at `/plan-review` of orchestrator `axozpe` (finding PR-001): there is a SEVENTH resolver bypass, spelled differently from the six Order 03 `sjsb04` fixes and therefore missed by its exact-string census. `cli._nv_backend_args` builds the args namespace handed to every noun-verb backend (`artifact_types.TYPE_BACKENDS`: `index`, `find` for plans/research, `rename`, `group`, `archive`, plus `_run_check`'s fallback backend) and sets `sub.dir = getattr(args, "dir", None) or os.getcwd()`. That turns a BARE invocation into an EXPLICIT `--dir <cwd>`, and the resolver deliberately never climbs an explicit `--dir` (`resolve_verb_repo_root` docstring, `lmyeas` OQ-01). So a bare `aw index research --check` from a project subdirectory surveys the subdirectory. Measured at review in an AW project checkout, lane HEAD `ad22ff70a`: from the root `aw index research --check --agent` gives `"outcome":"findings","exit":1` with 179 findings; from `docs/` it gives `"outcome":"conforms","exit":0,"verified":true` with 2 findings (only `check.stale-index-missing`). That is a false clean answer reachable with no flag, the exact defect class this Set exists to remove.
- Scope: Make the adapter stop inventing an explicit `--dir`. IN: change `cli._nv_backend_args` so that when the operator gave no `--dir`, the namespace it builds carries `dir=None` (OQ-01), so each backend's own `resolve_verb_repo_root(getattr(args, "dir", None))` call climbs; and add a subprocess regression test pinning the bare-cwd climb for the read-class `index <type> --check` path and the write-class `group`/`rename`/`archive` preview paths. OUT: adding a refusal to any verb (the read-class backends `plans_index.run_index`/`research_index.run_index` are reached through helpers `rlhmt9` F-02 measured as single-class WRITE, and refusals on write verbs are excluded Set-wide by `lmyeas` OQ-01); making an explicit `--dir` climb; changing `resolve_verb_repo_root`'s body or docstring; touching the six `sjsb04` sites; touching any backend module.
- Scope-Paths: agent_workflows/cli.py, tests/test_nv_backend_args_climb.py
- Item-Dependencies: executed:sjsb04
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: rgl2d4
- Blocks-Release: next
- Set: dirsilent
- Order: 5
- Highest E allocated: 02
- Author: opencode uri/its_direct/pt3-claude-opus-5.5-1m-us
- Id: pua92o
- Approval: 2026-10-09, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-09 approved (aw set): status set to approved
- 2026-10-08 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 FIXED
- 2026-10-08 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, fixed: OQ-01 reversed to dir=None, demonstrated), PR-002 (MEDIUM, fixed: preview no-write proof covers gitignored INDEX and archive), PR-003 (LOW, fixed: no-project control), PR-004 (LOW, fixed: commit-root agreement and $HOME property stated). Record: `.aw/records/reviews/20261007-dirsilent-05-pua92o-route-the-noun-verb-backend-adapter-through-resolve-verb-rep.review.md`.
- 2026-10-07 to-review (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): authored during the `axozpe` coverage-correction turn to own PR-001 (the seventh bypass site `cli._nv_backend_args`). GATE NOTE: inherits `- From-Backlog: rgl2d4` and `- Blocks-Release: next`. Depends on `sjsb04` because both edit `cli.py`'s resolution logic, and this plan's test reuses that plan's fixture shape; the runner isolates worktrees, so the edge is about meaning rather than file contention.

## Goal

A bare `aw index|group|rename|archive <type>` run from a project subdirectory operates on the project root, the same as its siblings, so `aw index research --check` stops reporting `conforms` over a tree it never examined. An explicit `--dir` keeps its verbatim, non-climbing meaning.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: stop inventing an explicit --dir

- [x] E-01 CHANGE `cli._nv_backend_args` SO A BARE INVOCATION REACHES THE BACKEND AS BARE. Replace `sub.dir = getattr(args, "dir", None) or os.getcwd()` with `sub.dir = getattr(args, "dir", None)`, so an explicit `--dir` is preserved verbatim and a bare call carries `None` (OQ-01). Do NOT substitute the resolved root string: that would make every bare call look EXPLICIT to any backend that branches on `bool(getattr(args, "dir", None))`, which is exactly what siblings `jei45f` (`specs.run_check`/`backlog.run_check`, reachable here through `_run_check`'s fallback) and `rlhmt9` (read verbs) do to pick the bare-vs-explicit refusal text. First re-derive every backend reachable through `_nv_backend_args` from `artifact_types.TYPE_BACKENDS` and from `_run_check`'s fallback, and confirm by reading each that it reads the directory only via `resolve_verb_repo_root(getattr(args, "dir", None))` or another `None`-tolerant form (measured at review: all 23 backend entries' modules do; none reads `args.dir` as a bare string). Remove the function-local `import os` (nothing else in the function uses it).
  - Depends on: none
  - Expected outcome: with no `--dir`, the namespace carries `dir=None` and each backend climbs through its own resolver call; with an explicit `--dir`, it carries exactly what the operator passed; no backend module is edited.
  - Execution state: performed

### Task group 2: pin it

- [x] E-02 ADD `tests/test_nv_backend_args_climb.py`, driving the real CLI in a SUBPROCESS (`python3 -m agent_workflows`, `PYTHONPATH` at the checkout, `AW_NO_REEXEC=1`) against a `tempfile` git project installed with `--records-backend repository` and seeded with at least one plan and one research record that produce a NONZERO observable at the root (for example an `index <type> --check` that reports a stale or missing index entry, or a `group plans` preview that names a real plan). Assert: (a) bare `index plans --check` and `index research --check` from `<root>/src/deep` give the SAME outcome, exit and finding count as from `<root>`; (b) a bare `group`/`rename`/`archive` PREVIEW (no `--apply`) from `<root>/src/deep` proposes the same paths as from `<root>` and writes nothing, proven by a byte-and-mtime snapshot of the whole `.aw/records/` tree before and after (NOT `git status` alone: `INDEX.json`/`INDEX.md` are gitignored by `.aw/.gitignore`, so a regenerated index would be invisible to it); (c) explicit `--dir <root>/src/deep` still does NOT climb (its result differs from the root's, the preserved `lmyeas` OQ-01 rule); (d) a bare `index plans --check` run from a directory OUTSIDE any AW project (with `HOME` pointed at a temp dir that is not an AW root) behaves exactly as before the change (the no-project path is not altered); (e) every `--agent` record validates with `agent_schema.validate_agent_record` and contains no absolute fixture path. The test must not read source files, use `inspect`/`ast`, or assert on the `os.getcwd` string (GUIDING_PRINCIPLES P16).
  - Depends on: E-01
  - Expected outcome: the new file passes; reverting E-01 makes assertion (a) fail.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The resolver rule is recorded in `project_context.resolve_verb_repo_root`'s docstring: an explicit `--dir` is honored verbatim with no climb; a bare call climbs via `find_project_root`. No spec governs it (`sjsb04` F-08).
- Noun-verb dispatch: `cli._run_noun_verb` routes `search`/`check`/`find` to their own runners and every other verb through `at.resolve_backend(t, verb)` called with `_nv_backend_args(args, t)`. `_run_check` also calls `_nv_backend_args` on its fallback path.
- Fixture trap (`sjsb04` F-07): a non-interactive install without `--records-backend repository` writes records under `$HOME`, making a root control vacuous.
- Cite code by symbol; line numbers drift.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `cli._nv_backend_args` converts a bare invocation into an explicit `--dir <cwd>`, so no backend reached through it climbs. | `agent_workflows/cli.py` `_nv_backend_args` "`sub.dir = getattr(args, "dir", None) or os.getcwd()`"; `resolve_verb_repo_root` "`if explicit_dir: return Path(explicit_dir).expanduser().resolve()`" |
| F-02 | It is user-visible as a false clean answer. Bare `aw index research --check --agent` gives `findings, exit 1, 179` at the root and `conforms, exit 0, verified:true, 2` from `docs/`. | measured at `axozpe` review, HEAD `ad22ff70a` |
| F-03 | `sjsb04`'s census missed it because it matched the exact string `Path(getattr(args, "dir", None) or os.getcwd())`; this site has no `Path(...)` wrapper. | `sjsb04` F-01 and its Deferred row "AUDITING FOR OTHER RESOLUTION EXPRESSIONS" |
| F-05 | The dispatch site's self-commit offer in `cli._run_noun_verb` ALREADY resolves the root with `resolve_verb_repo_root(getattr(args, "dir", None))` from the ORIGINAL args, so today a bare `group`/`rename --apply` resolves the backend at cwd but the commit root at the climbed root. E-01 makes the two agree. | `cli._run_noun_verb` "`repo_root = resolve_verb_repo_root(getattr(args, "dir", None))`" after the backend loop |
| F-04 | The backends behind it include write verbs (`plans_refs.run_mv`, `run_set_assign`, `plans_archive.run_archive`, the research equivalents). For a bare call, their target moves from cwd to the project root. This is the same bare-climb behavior every sibling write verb already has, so it adds no new hazard class, but it is a behavior change and is pinned in preview only. | `artifact_types.TYPE_BACKENDS`; `plans_index._dirs` / `research_index._roots` calling the resolver |

## Proposed changes (ordered, validatable)

1. E-01: the one-expression change in `cli._nv_backend_args`.
2. E-02: the subprocess regression test.

## Deferred / out of scope (with reason)

- ADDING A REFUSAL TO `index <type> --check` FOR AN EXPLICIT non-surveyable `--dir`. Its helpers are single-class write per `rlhmt9` F-02, so a refusal at the helper would refuse write verbs too, which `lmyeas` OQ-01 excludes. The bare case is the defect fixed here.
  - Carrier-Declined: excluded by the Set's write-side policy (`lmyeas` OQ-01, `rlhmt9` F-02); a split of those helpers is `rlhmt9`'s documented remedy if a read-only caller is later added
- A COMPLETENESS CLAIM about other differently-spelled bypasses. E-01 re-derives the backends behind this one adapter; it does not audit the whole package.
  - Carrier-Declined: no further measured site; the Set states its census limits

## Scope check

- Over-scope: none.
- Under-scope: none known. The adapter is the single choke point for every noun-verb backend, so one change covers all of them.

## Required tests / validation

- `python3 -m pytest tests/test_nv_backend_args_climb.py tests/test_resolver_bypass_sites_climb.py tests/test_explicit_dir_subdir_resolution.py tests/test_explicit_dir_non_project.py` for the focused surface.
- `python3 -m pytest` BARE per the repository contract, judged on the DELTA OF FAILING NODE IDS against a baseline YOU measured on a clean tree before editing. The baseline will include Orders 01 to 04's changes.

## Spec / documentation sync

N/A: no spec governs the resolution rule (`sjsb04` F-08). The change brings the adapter in line with the rule already documented in `resolve_verb_repo_root`'s docstring.

## Open questions

### OQ-01: Should a bare call pass `dir=None` or the resolved root string?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED: `None`. Two reasons, both measured at review. (1) The premise of the earlier answer, that "some backends may read `args.dir` directly as a string", is false: every module behind `artifact_types.TYPE_BACKENDS` (`plans_index`, `research_index`, `plans_refs`, `research_refs`, `plans_archive`, `research_archive`, `artifact_rename`, `prompts_index`, `prompts`, `specs`, `backlog`) reads it only as `resolve_verb_repo_root(getattr(args, "dir", None))`, so `None` is the input the resolver was designed for. (2) A resolved string is indistinguishable from an explicit `--dir`, and the Set's own refusal design keys the human text on `bool(getattr(args, "dir", None))` (`jei45f` OQ-02, `rlhmt9` "GUARD ON THE RESOLVED ROOT, NOT ON `--dir`"; `no_project_message(..., explicit=...)`), so a bare call outside a project would get the explicit-`--dir` wording. DEMONSTRATED: from `docs/` in this checkout, bare `aw index research --check --agent` gives `"outcome":"conforms","exit":0`; the same call with `_nv_backend_args` patched in-process to set `sub.dir = getattr(args, "dir", None)` gives `"outcome":"findings","exit":1`, matching the root.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the committed diff of `cli._nv_backend_args`. Paste the re-derived list of backends reachable through it (from `artifact_types.TYPE_BACKENDS` and `_run_check`'s fallback), with one line per backend saying how it reads `args.dir`. Paste the BEFORE/AFTER measurement by subprocess, with the interpreter and `PYTHONPATH` named, on a fixture seeded via `--records-backend repository`: bare `index research --check --agent` and `index plans --check --agent` from `<root>/src/deep` and from `<root>`. BEFORE must show they disagree, AFTER that they agree, with a NONZERO observable at the root. Paste explicit `--dir <root>/src/deep` AFTER still not climbing.
  - Observed evidence:
    Committed diff of `cli._nv_backend_args`:
    ```diff
    diff --git a/agent_workflows/cli.py b/agent_workflows/cli.py
    index 15accf5f7..2f46d9c4f 100644
    --- a/agent_workflows/cli.py
    +++ b/agent_workflows/cli.py
    @@ -12681,10 +12681,8 @@ def _nv_resolve_types(

     def _nv_backend_args(args, artifact_type):
         """Build an args namespace a legacy backend runner understands from the noun-verb args."""
    -    import os
    -
         sub = argparse.Namespace(**vars(args))
    -    sub.dir = getattr(args, "dir", None) or os.getcwd()
    +    sub.dir = getattr(args, "dir", None)
         # THE `--agent` FLAG IS NAMED `agent`, and reading it as `as_agent` SILENTLY DROPPED IT
         # (plan `9zvl2w` E-01). `cli._build_parser` registers the flag as `dest="agent"` and NO parser
         # anywhere in the package defines `as_agent`, so `getattr(args, "as_agent", False)` was always
    ```

    Re-derived list of backends reachable through `_nv_backend_args`:
    - `plans_index.run_index` (plans.index): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `plans_index._dirs`
    - `plans_index.run_find` (plans.find): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `plans_index.run_find` / `_dirs`
    - `plans_refs.run_mv` (plans.rename): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `plans_refs.run_mv`
    - `plans_refs.run_set_assign` (plans.group): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `plans_refs.run_set_assign`
    - `plans_archive.run_archive` (plans.archive): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `plans_archive._dirs`
    - `research_index.run_index` (research.index): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `research_index._roots`
    - `research_index.run_find` (research.find): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `research_index.run_find` / `_roots`
    - `research_refs.run_mv` (research.rename): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `research_refs._resolve_repo_root`
    - `research_refs.run_set_assign` (research.group): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `research_refs._resolve_repo_root`
    - `research_archive.run_archive` (research.archive): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `research_archive._resolve_repo_root`
    - `specs.run_check` (specs.check / _run_check fallback): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `specs.run_check`
    - `artifact_rename.run_rename_specs` (specs.rename): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `artifact_rename.run_group_specs` (specs.group): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `prompts.run_new` (prompts.new): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `prompts.run_new`
    - `prompts_index.run_index` (prompts.index): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `prompts_index.run_index`
    - `artifact_rename.run_rename_prompts` (prompts.rename): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `artifact_rename.run_group_prompts` (prompts.group): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `backlog.run_check` (backlog.check / _run_check fallback): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `backlog.run_check`
    - `artifact_rename.run_rename_backlog` (backlog.rename): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `artifact_rename.run_group_backlog` (backlog.group): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `artifact_rename.run_rename_walkthroughs` (walkthroughs.rename): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `artifact_rename.run_group_walkthroughs` (walkthroughs.group): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `artifact_rename.run_rename_roadmaps` (roadmaps.rename): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `artifact_rename.run_group_roadmaps` (roadmaps.group): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `artifact_rename.run_rename_releases` (releases.rename): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `artifact_rename.run_group_releases` (releases.group): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `artifact_rename.run_rename_other` (other.rename): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`
    - `artifact_rename.run_group_other` (other.group): reads `args.dir` via `resolve_verb_repo_root(getattr(args, "dir", None))` in `artifact_rename._resolve_repo_root`

    Subprocess measurement:
    Interpreter: python3
    PYTHONPATH: <lane-worktree-root>

    BEFORE measurement (disagree, false clean conforms/exit 0 from deep):
    research root: 1 {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"research","findings":2,"diagnostics":[{"location":"INDEX.json","rule":"check.stale-index-stale"},{"location":"INDEX.md","rule":"check.stale-index-stale"}],"next":null}
    research deep: 0 {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"research","findings":2,"diagnostics":[{"location":"INDEX.json","rule":"check.stale-index-missing"},{"location":"INDEX.md","rule":"check.stale-index-missing"}],"next":null}
    plans root: 1 {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"plans","findings":2,"diagnostics":[{"location":"INDEX.json","rule":"check.stale-index-stale"},{"location":"INDEX.md","rule":"check.stale-index-stale"}],"next":null}
    plans deep: 0 {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"plans","findings":2,"diagnostics":[{"location":"INDEX.json","rule":"check.stale-index-missing"},{"location":"INDEX.md","rule":"check.stale-index-missing"}],"next":null}

    AFTER measurement (agree with nonzero observable at root):
    research root: 1 {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"research","findings":2,"diagnostics":[{"location":"INDEX.json","rule":"check.stale-index-stale"},{"location":"INDEX.md","rule":"check.stale-index-stale"}],"next":null}
    research deep: 1 {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"research","findings":2,"diagnostics":[{"location":"INDEX.json","rule":"check.stale-index-stale"},{"location":"INDEX.md","rule":"check.stale-index-stale"}],"next":null}
    plans root: 1 {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"plans","findings":2,"diagnostics":[{"location":"INDEX.json","rule":"check.stale-index-stale"},{"location":"INDEX.md","rule":"check.stale-index-stale"}],"next":null}
    plans deep: 1 {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"plans","findings":2,"diagnostics":[{"location":"INDEX.json","rule":"check.stale-index-stale"},{"location":"INDEX.md","rule":"check.stale-index-stale"}],"next":null}

    Explicit --dir <root>/src/deep AFTER still not climbing:
    explicit research deep: 0 {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"research","findings":2,"diagnostics":[{"location":"INDEX.json","rule":"check.stale-index-missing"},{"location":"INDEX.md","rule":"check.stale-index-missing"}],"next":null}
    explicit plans deep: 0 {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"plans","findings":2,"diagnostics":[{"location":"INDEX.json","rule":"check.stale-index-missing"},{"location":"INDEX.md","rule":"check.stale-index-missing"}],"next":null}
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the committed test file's assertions for (a) to (d) and the run showing it PASSING. Paste a grep of the file for `inspect`, `ast.parse`, `os.getcwd` and any read of `agent_workflows/*.py`, returning nothing. PASTE THE MUTATION: restore `or os.getcwd()` in `_nv_backend_args`, paste the FAILING output from assertion (a), revert, and paste green. PASTE the BARE `python3 -m pytest` summary line reconciled against your own baseline, naming any failing node id. PASTE `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` immediately before committing, listing only the two `- Scope-Paths:` entries.
  - Observed evidence:
    Committed test file assertions from `tests/test_nv_backend_args_climb.py`:
    ```python
    def test_assertion_a_bare_index_check_climb(self):
        """Bare index plans --check and index research --check climb from deep."""
        # Plans index check agent mode
        proc_plans_deep = self._run_cli(
            "index", "plans", "--check", "--agent", cwd=self.deep_subdir
        )
        proc_plans_root = self._run_cli(
            "index", "plans", "--check", "--agent", cwd=self.proj_root
        )
        rec_plans_deep = self._parse_and_validate_agent_record(proc_plans_deep.stdout)
        rec_plans_root = self._parse_and_validate_agent_record(proc_plans_root.stdout)
        self.assertEqual(proc_plans_deep.returncode, proc_plans_root.returncode)
        self.assertEqual(rec_plans_deep["outcome"], rec_plans_root["outcome"])
        self.assertEqual(rec_plans_deep["exit"], rec_plans_root["exit"])
        self.assertEqual(rec_plans_deep["findings"], rec_plans_root["findings"])
        self.assertGreater(rec_plans_root["findings"], 0)

        # Plans index check human mode
        proc_plans_deep_h = self._run_cli(
            "index", "plans", "--check", cwd=self.deep_subdir
        )
        proc_plans_root_h = self._run_cli(
            "index", "plans", "--check", cwd=self.proj_root
        )
        self.assertEqual(proc_plans_deep_h.returncode, proc_plans_root_h.returncode)
        self.assertEqual(proc_plans_deep_h.stdout, proc_plans_root_h.stdout)

        # Research index check agent mode
        proc_rsch_deep = self._run_cli(
            "index", "research", "--check", "--agent", cwd=self.deep_subdir
        )
        proc_rsch_root = self._run_cli(
            "index", "research", "--check", "--agent", cwd=self.proj_root
        )
        rec_rsch_deep = self._parse_and_validate_agent_record(proc_rsch_deep.stdout)
        rec_rsch_root = self._parse_and_validate_agent_record(proc_rsch_root.stdout)
        self.assertEqual(proc_rsch_deep.returncode, proc_rsch_root.returncode)
        self.assertEqual(rec_rsch_deep["outcome"], rec_rsch_root["outcome"])
        self.assertEqual(rec_rsch_deep["exit"], rec_rsch_root["exit"])
        self.assertEqual(rec_rsch_deep["findings"], rec_rsch_root["findings"])
        self.assertGreater(rec_rsch_root["findings"], 0)

        # Research index check human mode
        proc_rsch_deep_h = self._run_cli(
            "index", "research", "--check", cwd=self.deep_subdir
        )
        proc_rsch_root_h = self._run_cli(
            "index", "research", "--check", cwd=self.proj_root
        )
        self.assertEqual(proc_rsch_deep_h.returncode, proc_rsch_root_h.returncode)
        self.assertEqual(proc_rsch_deep_h.stdout, proc_rsch_root_h.stdout)

    def test_assertion_b_preview_write_verbs_propose_and_write_nothing(self):
        """Bare group, rename, archive preview from deep proposes same paths and writes nothing."""
        # Group plans preview
        snap_before_group = _snapshot_tree(self.proj_root)
        proc_group_deep = self._run_cli(
            "group", "plans", "p00001", "--set", "newset", cwd=self.deep_subdir
        )
        proc_group_root = self._run_cli(
            "group", "plans", "p00001", "--set", "newset", cwd=self.proj_root
        )
        self.assertEqual(proc_group_deep.returncode, 0)
        self.assertEqual(proc_group_root.returncode, 0)
        self.assertEqual(proc_group_deep.stdout, proc_group_root.stdout)
        self.assertIn("20261001-testset-01-p00001-plan.ipd.md", proc_group_deep.stdout)
        snap_after_group = _snapshot_tree(self.proj_root)
        self.assertEqual(snap_before_group, snap_after_group)

        # Rename plans preview
        snap_before_rename = _snapshot_tree(self.proj_root)
        proc_rename_deep = self._run_cli(
            "rename", "plans", "p00001", "--slug", "newslug", cwd=self.deep_subdir
        )
        proc_rename_root = self._run_cli(
            "rename", "plans", "p00001", "--slug", "newslug", cwd=self.proj_root
        )
        self.assertEqual(proc_rename_deep.returncode, 0)
        self.assertEqual(proc_rename_root.returncode, 0)
        self.assertEqual(proc_rename_deep.stdout, proc_rename_root.stdout)
        self.assertIn(
            "20261001-testset-01-p00001-newslug.ipd.md", proc_rename_deep.stdout
        )
        snap_after_rename = _snapshot_tree(self.proj_root)
        self.assertEqual(snap_before_rename, snap_after_rename)

        # Archive plans preview
        snap_before_archive = _snapshot_tree(self.proj_root)
        proc_archive_deep = self._run_cli(
            "archive", "plans", "p00003", cwd=self.deep_subdir
        )
        proc_archive_root = self._run_cli(
            "archive", "plans", "p00003", cwd=self.proj_root
        )
        self.assertEqual(proc_archive_deep.returncode, 0)
        self.assertEqual(proc_archive_root.returncode, 0)
        self.assertEqual(proc_archive_deep.stdout, proc_archive_root.stdout)
        self.assertIn(
            "20261001-testset-03-p00003-done.ipd.md", proc_archive_deep.stdout
        )
        snap_after_archive = _snapshot_tree(self.proj_root)
        self.assertEqual(snap_before_archive, snap_after_archive)

    def test_assertion_c_explicit_dir_does_not_climb(self):
        """Explicit --dir <deep> does not climb and result differs from root."""
        # Index plans explicit dir
        proc_plans_exp = self._run_cli(
            "index",
            "plans",
            "--check",
            "--agent",
            "--dir",
            str(self.deep_subdir),
            cwd=self.proj_root,
        )
        rec_plans_exp = self._parse_and_validate_agent_record(proc_plans_exp.stdout)
        proc_plans_root = self._run_cli(
            "index", "plans", "--check", "--agent", cwd=self.proj_root
        )
        rec_plans_root = self._parse_and_validate_agent_record(proc_plans_root.stdout)
        self.assertNotEqual(rec_plans_exp["outcome"], rec_plans_root["outcome"])
        self.assertNotEqual(rec_plans_exp["exit"], rec_plans_root["exit"])

        # Index research explicit dir
        proc_rsch_exp = self._run_cli(
            "index",
            "research",
            "--check",
            "--agent",
            "--dir",
            str(self.deep_subdir),
            cwd=self.proj_root,
        )
        rec_rsch_exp = self._parse_and_validate_agent_record(proc_rsch_exp.stdout)
        proc_rsch_root = self._run_cli(
            "index", "research", "--check", "--agent", cwd=self.proj_root
        )
        rec_rsch_root = self._parse_and_validate_agent_record(proc_rsch_root.stdout)
        self.assertNotEqual(rec_rsch_exp["outcome"], rec_rsch_root["outcome"])
        self.assertNotEqual(rec_rsch_exp["exit"], rec_rsch_root["exit"])

        # Group plans explicit dir
        proc_group_exp = self._run_cli(
            "group",
            "plans",
            "p00001",
            "--set",
            "newset",
            "--dir",
            str(self.deep_subdir),
            cwd=self.proj_root,
        )
        self.assertEqual(proc_group_exp.returncode, 2)
        self.assertIn("no plans artifact matched", proc_group_exp.stdout)

        # Rename plans explicit dir
        proc_rename_exp = self._run_cli(
            "rename",
            "plans",
            "p00001",
            "--slug",
            "newslug",
            "--dir",
            str(self.deep_subdir),
            cwd=self.proj_root,
        )
        self.assertEqual(proc_rename_exp.returncode, 2)
        self.assertIn("no plans artifact matched", proc_rename_exp.stdout)

        # Archive plans explicit dir
        proc_archive_exp = self._run_cli(
            "archive",
            "plans",
            "p00003",
            "--dir",
            str(self.deep_subdir),
            cwd=self.proj_root,
        )
        self.assertEqual(proc_archive_exp.returncode, 2)
        self.assertIn("no plan or Set matches", proc_archive_exp.stdout)

    def test_assertion_d_outside_project_unaltered(self):
        """Bare index plans --check from outside AW project behaves identically."""
        proc_outside = self._run_cli(
            "index", "plans", "--check", "--agent", cwd=self.outside_cwd
        )
        rec_outside = self._parse_and_validate_agent_record(proc_outside.stdout)
        self.assertEqual(proc_outside.returncode, 0)
        self.assertEqual(rec_outside["outcome"], "conforms")
        self.assertEqual(rec_outside["findings"], 2)
        diag_rules = [d.get("rule") for d in rec_outside.get("diagnostics", [])]
        self.assertEqual(
            diag_rules, ["check.stale-index-missing", "check.stale-index-missing"]
        )

        proc_outside_h = self._run_cli(
            "index", "plans", "--check", cwd=self.outside_cwd
        )
        self.assertEqual(proc_outside_h.returncode, 0)
        self.assertIn("check.stale-index-missing", proc_outside_h.stdout)
    ```

    Test passing run output:
    ```
    bringing up nodes...
    ....                                                                     [100%]
    4 passed in 8.22s
    ```

    Grep check for forbidden patterns (inspect, ast.parse, os.getcwd, agent_workflows/*.py):
    ```sh
    $ grep -E "inspect|ast\.parse|os\.getcwd|agent_workflows/.*\.py" tests/test_nv_backend_args_climb.py
    # Exit code: 1 (no matches)
    ```

    Mutation test (restore `or os.getcwd()` in `_nv_backend_args`):
    ```
    =================================== FAILURES ===================================
    _______ NvBackendArgsClimbTests.test_assertion_a_bare_index_check_climb ________
    [gw11] linux -- Python 3.14.6 python3

    self = <tests.test_nv_backend_args_climb.NvBackendArgsClimbTests testMethod=test_assertion_a_bare_index_check_climb>

        def test_assertion_a_bare_index_check_climb(self):
    ...
    >       self.assertEqual(proc_plans_deep.returncode, proc_plans_root.returncode)
    E       AssertionError: 0 != 1

    tests/test_nv_backend_args_climb.py:264: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_nv_backend_args_climb.py::NvBackendArgsClimbTests::test_assertion_a_bare_index_check_climb
    1 failed in 4.16s
    ```
    After reverting mutation:
    ```
    ....                                                                     [100%]
    4 passed in 8.22s
    ```

    Bare `python3 -m pytest` reconciled against baseline:
    - Baseline: `8 failed, 7157 passed, 2 skipped, 3 warnings in 394.73s (0:06:34)`
    - Post-change: `8 failed, 7161 passed, 2 skipped, 3 warnings in 258.06s (0:04:18)`
    - Delta: +4 passed (new tests in `test_nv_backend_args_climb.py`), zero new failures.
    - Failing node IDs match baseline identically:
      - tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_f_commit_scope_reason_rejects_paths_not_out_of_scope
      - tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_b_finalize_leaves_metadata_untouched_when_fully_in_scope
      - tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_c_multiple_out_of_scope_paths_sorted_and_sanitized
      - tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_a_finalize_inserts_scope_exceeded_metadata
      - tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_g_recorded_scope_justifications_survive_recovery_rebegin
      - tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_d_runner_retry_loop_out_of_scope_notice
      - tests/test_scope_exceeded.py::TestScopeExceededMetadataAndSendBack::test_case_e_commit_scope_reason_recording_only_without_paths
      - tests/test_attempt_lane_facts.py::AttemptLaneFactsTests::test_case_2_oc_host_refused_isolated_turn

    aw sanitize --agent output:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```

    git diff --cached --name-only immediately before committing (reconciled):
    - `agent_workflows/cli.py`
    - `tests/test_nv_backend_args_climb.py`
    - `.aw/records/plans/pending/20261007-dirsilent-05-pua92o-route-the-noun-verb-backend-adapter-through-resolve-verb-rep.ipd.md`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. EXECUTION CONTRACT: commit ONLY the two declared `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A`, and NEVER push. Paste the ACTUAL runner output for every test claim. Resolve every `V-*` item with concrete pasted evidence, in a separate pass from its `E-*` mark.

SCOPE FENCE (a declaration for the runner to reconcile, not an instruction to stop). Do NOT: add a refusal to any verb; make an explicit `--dir` climb; edit `resolve_verb_repo_root`; touch the six `sjsb04` sites; edit any backend module. An out-of-scope edit that proves necessary is made and then justified with `aw ipd finalize --scope-reason`, and a declared path left unmodified needs `--scope-ack`.

WHAT APPROVAL APPROVES: a bare noun-verb command from a subdirectory now targets the project root. For write verbs (`group`/`rename`/`archive`) that is a target change, the same one every sibling write verb already has for a bare call. That includes the resolver's `$HOME` property (docstring hazard 3): a bare `aw archive plans --apply` run from a non-project directory under a `$HOME` that is itself an AW root now targets `$HOME`, exactly as a bare `aw set` there already does. It is pinned in preview mode only.

ON COMPLETION, the executor runs `aw ipd lint --phase pre-transition` until it conforms. The terminal transition is owed unconditionally, but its owner is conditional. Under `aw oc run` / `aw agy run` the RUNNER performs `aw ipd begin`/`aw ipd finalize` and the executor must not. Executed by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll the move with `git mv` and never hand-edit `- Status: executed`. Backlog `rgl2d4` is NOT closed by this plan: it is a carrier of the item's `- Blocks-Release: next` gate, and the item closes only once every carrier executes.
