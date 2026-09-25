# Review findings: plan wj5b53

- Subject-Id: wj5b53
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 01 of Set `laneawpin`, the only child, `- Item-Dependencies: none`. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE semantic review, and
`--phase review-finalize` reports exit 0 after the revisions with one INFO advisory (`IPD-Z602` on E-04)
that is assessed and declined in the plan's gate rather than silently passed. The plan file was committed
and unchanged, so no pre-review snapshot was needed. Every measurement below was taken in this lane at
HEAD `e2fba20d`, not inherited from the plan.

THE DIAGNOSIS IS CORRECT AND INDEPENDENTLY REPRODUCIBLE, and it is the strongest part of the plan.
Confirmed from this lane: `python3 -P -c "import agent_workflows"` resolves
`<main-checkout>/agent_workflows/__init__.py` (the MAIN checkout) while
`python3 -c "import agent_workflows"` from the lane root resolves this lane's copy. So the two
invocations run different code exactly as `lcmz33` and `jeh310` describe. The `argv is None` seam is
real (`cli.main(argv=None)`, `__main__.py` calling `main()`), `cli.main` does return an int rather than
exiting, and the `_AW_PIN_BOOTSTRAP` string constant is genuinely NOT among the AST fingerprints
(`pinned_child_env`, `pinned_module_argv`, and `assert_child_tool_identity` are; the constant is not),
so F-4's "safe seam" claim holds and the plan's chosen mechanism is the right one.

THREE OF THE PLAN'S MECHANISMS WOULD NOT HAVE WORKED AS AUTHORED, and each was found by running the
shipped code rather than re-reading the plan. This is the substance of the review.

```text
F-7  COMPLETION SURFACES REACH main() WITH argv is None
     cli.py registers   sub.add_parser("__complete", help=argparse.SUPPRESS)
     _dispatch calls    _maybe_argcomplete(parser)            # on EVERY invocation
     measured:  python3 -m agent_workflows __complete --cword 1 -- aw ip
                -> stdout 'ipd'   stderr ''   exit 0
     completion.py contract: "fails SOFT: any lookup error yields [] (a completion query must
                              never raise into a live shell)"
     => an unguarded notice + execve fires on every TAB in a lane and corrupts the candidate stream

F-8  THE MARKER WOULD HAVE BEEN INHERITED, NOT SCOPED
     measured: child sets os.environ['AW_PINNED_CHILD']='1', spawns grandchild
               -> GRANDCHILD sees 1
     => the exemption spreads to a whole subtree, silently re-disabling the fix

F-9  THE NAMED CHANGELOG HEADING DOES NOT EXIST
     grep -c Unreleased CHANGELOG.md            -> 0
     grep -n '^## ' CHANGELOG.md                -> 2.0.0 (pending) / 1.3.0 (pending) / 1.2.0 / Earlier
     last commits touching CHANGELOG.md add under '## 1.3.0 (pending)'
     => V-05 as written ("the entry under Unreleased") was unsatisfiable
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A (correctness) | `agent_workflows/cli.py` `_run_dunder_complete`, `_maybe_argcomplete`, `_dispatch`; `agent_workflows/completion.py` module docstring | SHELL COMPLETION WAS AN UNGUARDED ENTRY POINT. The plan guarded only on `argv is None`, but TWO completion surfaces reach `main()` that way through the console script: the hidden `aw __complete` verb (registered `help=argparse.SUPPRESS`), and `_maybe_argcomplete(parser)`, which `_dispatch` calls on every single invocation. A completion callback that writes a notice to stderr and then REPLACES ITS OWN PROCESS corrupts the candidate stream the shell is actively reading, and it would fire on every TAB a maintainer pressed inside a lane. `completion.py`'s own contract is explicit that the query engine must never raise into a live shell. Verified the callback is real and silent today: `__complete --cword 1 -- aw ip` prints exactly `ipd`, stderr empty, exit 0. The two surfaces need DIFFERENT guards and neither subsumes the other: `__complete` is an argv token, while argcomplete is driven purely by env (`COMP_LINE`/`_ARGCOMPLETE`) with no distinguishing token. | C:Low; U:High; S:Low; F:Medium; Overall:Medium | FIXED | E-01 gained an env-based completion exemption checked BEFORE anything is printed; E-02 gained a `sys.argv[1:2] == ["__complete"]` skip with the reasoning and the measurement recorded; E-04 case 11 drives BOTH surfaces and is one of the four cases required to be demonstrated FAILING against a mutation. F-7 added to the plan. |
| PR-002 | HIGH | IN-SCOPE | A (correctness) | proposed `_AW_PIN_BOOTSTRAP` marker; measured `os.environ` propagation | THE EXEMPTION MARKER WOULD HAVE LEAKED TO EVERY DESCENDANT. E-03 said to set `os.environ['AW_PINNED_CHILD']='1'` in the bootstrap. An `os.environ` mutation propagates to every process the mutating process spawns, which I measured directly (a child setting it spawns a grandchild that reports `1`). So the exemption intended for ONE pinned nested call would be inherited by that call's entire subtree, silently disabling the fix wherever it reached and reintroducing precisely the silent-false-confidence defect this plan exists to repair. The plan described the marker as identifying "a process started through the bootstrap", which is true of the bootstrap process AND of everything under it. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-03 now requires `check_and_reexec` to CONSUME the marker with `os.environ.pop('AW_PINNED_CHILD', None)` at the moment it reads it, so the exemption is spent by the process it was meant for; the reason must be stated in the module docstring as a correctness property, not a tidy-up; E-04 case 10 pins that a grandchild does NOT see it, and V-03 requires that case demonstrated FAILING with the pop removed. F-8 added. |
| PR-003 | HIGH | IN-SCOPE | E (verification) | `CHANGELOG.md`; plan `E-05`, `V-05` | E-05 AND V-05 NAMED A HEADING THAT DOES NOT EXIST, so V-05 was unsatisfiable as written and an executor would either invent an "Unreleased" heading this project does not use or mark V-05 verified against something else. `grep -c Unreleased CHANGELOG.md` is `0`; the file's four headings are `2.0.0 (pending)`, `1.3.0 (pending)`, `1.2.0`, and `Earlier`, and every recent commit touching the CHANGELOG adds under `1.3.0 (pending)`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now names `## 1.3.0 (pending)`, records the measurement, and requires the heading RE-DERIVED at execution time (a release cut between review and execution would move it, so the heading is a live fact, not a stable one). V-05 now requires pasting `grep -n "^## " CHANGELOG.md` first and then the diff under THAT heading, and explicitly forbids an invented one. F-9 added, and the Scope line corrected. |
| PR-004 | MEDIUM | IN-SCOPE | A (correctness) | `os.execve` semantics; plan `E-01` | THE NOTICE WOULD BE LOST ON EVERY CAPTURED-EVIDENCE PATH. `execve` replaces the process image without flushing Python's buffers, and stderr is line-buffered only when it is a tty. So on a pipe, which is every test case and every instance of an agent capturing output as evidence, the one-line notice the plan exists to produce would vanish while the re-exec still happened. That is the WORST failure mode for this plan specifically: the re-run would silently succeed, which is the same silence `lcmz33` filed. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | E-01 now requires an explicit `sys.stderr`/`sys.stdout` flush before the `execve`, with the pipe-versus-tty reason stated; E-04 case 13 asserts the notice is present when stderr is a PIPE; V-04 requires that case demonstrated FAILING with the flush removed. F-10 added. |
| PR-005 | MEDIUM | IN-SCOPE | D (anti-regression) | `tests/test_ipd_lifecycle_cli.py` | THE DETECTOR PREDICATE HAD A NEARBY WRONG VARIANT THE PLAN DID NOT FENCE OFF. E-01 correctly required `<toplevel>/agent_workflows/__init__.py`, but did not say why the weaker directory-existence test is wrong, and that is the variant an executor simplifying the code would reach for. Measured: `tests/test_ipd_lifecycle_cli.py` builds throwaway git repos containing a BARE `agent_workflows/` directory at seven sites (seven `(self.root / "agent_workflows").mkdir()` calls, none writing an `__init__.py`), so a directory test would classify those fixtures as toolkit checkouts and the detector would fire inside them. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now marks the `__init__.py` predicate LOAD-BEARING and names the seven fixtures and the count; E-04 case 12 builds exactly that shape (`.git` plus a bare `agent_workflows/` with no `__init__.py`) and asserts stderr EMPTY; V-01 requires the predicate line pasted; the required-validation list adds `tests/test_ipd_lifecycle_cli.py`. F-11 added. |
| PR-006 | MEDIUM | IN-SCOPE | A (correctness) | `pyproject.toml` `requires-python = ">=3.9"`; `runner_shared.pinned_module_argv`; plan `F-3` | THE RE-EXEC ARGV HAD AN UNSTATED TRAP IN BOTH DIRECTIONS. Everything adjacent in this codebase that launches a pinned child adds `-P` (guarded `if sys.version_info >= (3, 11)`), so an executor pattern-matching on `pinned_module_argv` would plausibly add it here. That would DEFEAT this plan: `-P` suppresses the cwd `sys.path[0]` entry, and the plan's own F-3 shows cwd-first and `PYTHONPATH` are the two halves that make `-m` resolve `<X>`. It is also 3.11+ while this package supports 3.9. Relatedly, the PEP 604 union return annotation E-01 specifies is only legal on 3.9 under `from __future__ import annotations`, which all 163 package modules carry but which the plan did not require. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now forbids `-P` and states both reasons (it defeats the mechanism, and it is 3.11+ against a 3.9 floor), requires `from __future__ import annotations`, and V-01 requires evidence that no `-P` appears in the re-exec argv. F-12 added. |
| PR-007 | MEDIUM | UNDER-SCOPE | G (executability) | `.aw/records/backlog/graduated/...jeh310...`; `check_engine.evaluate_blocking_close` | THE DUPLICATE-BACKLOG CLOSURE WAS SENT INTO A GUARANTEED REFUSAL WITH NO ROUTE. The plan said "the executor or runner closes it alongside `lcmz33` citing this executed plan". But `jeh310` carries `- Blocks-Release: next` and NO plan carries `- From-Backlog: jeh310` (this plan's field is single-valued and names `lcmz33`), so `evaluate_blocking_close`'s `done` branch fails closed unless HANDOFF, SATISFIED, or DE-GATED applies. A closer following the plan literally hits an error whose fix the plan never states. | C:Low; U:Medium; S:Low; F:Low; Overall:Low | FIXED | The deferred entry now gives the exact SATISFIED route (`aw backlog set done jeh310 --evidence <this plan in executed/> --message ...`), explains why the HANDOFF route is unavailable (single-valued `From-Backlog` already naming `lcmz33`), and states why this is deliberately NOT an E-item (the citation it requires does not exist until this plan is in `executed/`). The gate repeats it as a named follow-up. F-13 added. |
| PR-008 | MEDIUM | IN-SCOPE | G (executability) | plan `V-02` | V-02 REQUIRED EVIDENCE FROM A PATH THAT DOES NOT EXIST. It instructed the executor to run the measurement "from `/tmp/opencode/graduate-top10/tests`", the AUTHOR's scratch worktree. Verified ABSENT. An executor would either fabricate the measurement or silently substitute a different tree without saying so, and the whole point of V-02 is that the version string proves WHICH tree ran. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-02 now requires the `tests/` subdirectory of the checkout being executed in, RE-DERIVED at execution time, and explicitly names the stale scratch path as not to be reused. This is the live-artifact re-derivation convention applied to a path rather than a count. |
| PR-009 | MEDIUM | UNDER-SCOPE | G (executability) | plan `## Approval and execution gate` | THE GATE WAS ONE PARAGRAPH AND CARRIED NO EXECUTION CONTRACT. It had the commit discipline and the honesty rule, but no statement of what a human is actually approving (this changes the behavior of the entry point every other verb goes through), no scope FENCE in the declaration form the 2026-09-01 ruling requires, and a STOP condition for only one of the two genuinely unsafe preconditions. It also carried a bare "STOP and report" that, read together with the missing fence, risks the executor stopping over a scope question, which the ruling explicitly forbids. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten: a plain statement of the behavior change, its measured cost, and the WARN-ONLY alternative a maintainer could prefer; a declaration-style scope fence (make-then-justify via `aw ipd finalize --scope-reason`/`--scope-ack`, with the `cli.py`/`runner_shared.py` contention noted as NOT a runtime hazard because items are isolated); TWO stop conditions, both genuinely unsafe rather than scope questions; the bare-`pytest` honesty rule with the `-qq` trap named; a sharpened irony note (the defect corrupts this plan's own evidence commands); staged-set verification for a shared checkout; the conditional lifecycle transition with no hand-rolled `git mv`; and the `jeh310` follow-up. A right-sizing assessment of the `IPD-Z602` advisory was added rather than left implicit. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Three mechanisms would not have worked as authored (PR-001, PR-002, PR-003). Is that `REPLAN`, or repairable with bounded edits? | Repair in place; `APPROVE WITH REVISIONS APPLIED`. | `REJECT - NEEDS REPLAN`. Rejected: the diagnosis, the chosen seam (`argv is None` in `cli.main`), the `_AW_PIN_BOOTSTRAP` string as the fingerprint-safe edit point, the equality-not-ancestry comparison, and the six-item decomposition all survive verification intact. What changed is two added guards, one consumed env var, and a corrected heading name, all inside the already-declared paths. | `plan-review` Step 2.4 reserves `REPLAN` for an approach "fundamentally unsound and cannot be repaired with bounded edits". No declared path changed and no E-item was removed. | yes |
| D-2 | Does the completion exemption (PR-001) need a maintainer decision, given it means an `aw` TAB inside a lane silently completes against the WRONG tree? | No. Exempt silently, and record the residual honestly. | (a) Let completion re-exec (rejected: it corrupts the live candidate stream, which `completion.py`'s own contract forbids). (b) Print the notice but skip the exec (rejected: stderr from a completion callback is what the shell may render over the prompt, and the contract is that the path is silent). | `completion.py`: the query engine "fails SOFT: any lookup error yields [] (a completion query must never raise into a live shell)". The residual is bounded and benign: a completion candidate from the wrong tree offers a slightly stale verb list, which no plan pastes as evidence, whereas the defect this plan repairs is false VALIDATION evidence. | yes |
| D-3 | Should the `AW_PINNED_CHILD` leak (PR-002) be fixed by popping the var, or by choosing a non-inherited signal instead? | Pop it in `check_and_reexec` at the moment it is read. | (a) Key the exemption on a marker the bootstrap passes in argv rather than env (rejected: argv is forwarded verbatim to the CLI's own parser, so a synthetic token would have to be stripped, which touches argv handling the plan deliberately leaves alone). (b) Accept inheritance (rejected: it is the defect). | The pop is local to the new module, needs no change to the fingerprinted functions, and is directly testable (E-04 case 10 asserts a grandchild does not see the marker). The plan's own OUT list forbids editing `pinned_child_env`/`pinned_module_argv`/`assert_child_tool_identity`, which rules out the env-plumbing alternatives. | yes |
| D-4 | Is E-04 at 13 cases (up from 9) now over-sized, as the `IPD-Z602` advisory suggests? | Not a split. Record the assessment in the gate. | Splitting E-04 into two child E-items or two files. Rejected: it would duplicate the `tempfile` fixture and the launcher across two files and halve one V-item's evidence, for no gain in focus. | `plan-review` rubric G right-sizing: E-04 is ONE deliverable (one new test file), ONE code region, ONE test surface, ONE validating `V-*`; the 13 cases share a single fixture and launcher and vary only cwd and env, which is parametrization. The growth from 9 to 13 is exactly what PR-001, PR-002, PR-004, and PR-005 required. Per the workflow, a maintainer sizing signal is an actionable finding to investigate by decomposition, which is what this row records; the investigation concluded no split. | yes |
| D-5 | The plan's measurements cite HEAD `877545fc` and scratch worktree `/tmp/opencode/graduate-top10`, neither of which is this lane. Does that block the review? | No. Re-measure everything in this lane and do not raise the difference as a finding. | Raising stale provenance as a finding, or reading the main checkout. Rejected: `877545fc` is a real reachable commit in this repository (verified `git cat-file -t`), and the lane is the complete authorized workspace. | `git log --oneline -1 877545fc` resolves, so the authoring base is genuine. Every claim was independently re-derived at HEAD `e2fba20d` in this lane, which is stronger than auditing the author's paths. The one place the stale path was LOAD-BEARING rather than contextual (V-02's required evidence command) was fixed as PR-008, since there it is an instruction the executor must follow, not a note about where a measurement came from. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author          --agent wj5b53 -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize --agent wj5b53 -> exit 0, 1 INFO (IPD-Z602 on E-04, assessed in D-4)

THE DEFECT, reproduced in this lane (HEAD e2fba20d):
  python3 -P -c "import agent_workflows"  -> <main-checkout>/agent_workflows/__init__.py  (MAIN)
  python3    -c "import agent_workflows"  -> <this lane>/agent_workflows/__init__.py      (LANE)

EQUALITY vs ANCESTRY (confirms F-5 from a second direction, F-14):
  imported root  <main-checkout>
  lane toplevel  <main-checkout>/.aw/worktrees/<lane>
  commonpath == imported  -> True     # ancestry would WRONGLY accept
  realpath equality       -> False    # equality correctly rejects
  this lane's .git is a FILE ('gitdir: ...'), so the file-or-dir walk is required

THE SEAM IS AS THE PLAN DESCRIBES:
  cli.main(argv: Optional[Sequence[str]] = None) -> int    # returns, does not sys.exit
  __main__.py: raise SystemExit(main())                    # argv is None
  _AW_PIN_BOOTSTRAP = _AW_PIN_STRIP + runpy.run_module("agent_workflows", run_name="__main__")
  fingerprints present: pinned_child_env, pinned_module_argv, assert_child_tool_identity
  fingerprints ABSENT : _AW_PIN_BOOTSTRAP, _AW_PIN_STRIP, runner_package_root   # the safe seam holds
  pinned child today:  pinned_module_argv(["--version"]) + pinned_child_env(), cwd=/tmp
                       -> rc 0, stdout the version, stderr ''   (the silence E-03 must preserve)

PR-001  __complete --cword 1 -- aw ip  -> stdout 'ipd', stderr '', exit 0
        argcomplete NOT installed here, so the env-driven surface is untestable locally but reachable
PR-002  grandchild of a process setting AW_PINNED_CHILD in os.environ -> sees '1'
PR-003  grep -c Unreleased CHANGELOG.md -> 0
PR-005  seven '(self.root / "agent_workflows").mkdir()' in tests/test_ipd_lifecycle_cli.py, zero __init__.py
PR-006  requires-python = ">=3.9"; 163/163 modules carry 'from __future__ import annotations'
PR-007  jeh310 has 'Blocks-Release: next'; no plan carries 'From-Backlog: jeh310'
PR-008  /tmp/opencode/graduate-top10 -> ABSENT
F-15    python3 -m agent_workflows --version  floor ~269ms  (bare interpreter ~16ms), 5-run minimum
        so the re-exec costs about one extra startup, on the mismatch path only
```

NOT RE-RUN AT REVIEW, and stated rather than implied: the repository suite. This review changed only
planning prose, so no suite baseline is claimed here in either direction. The plan requires the bare
suite at E-06/V-06, which is the correct treatment.

NOT VERIFIABLE IN THIS LANE, and recorded rather than glossed: `argcomplete` is not installed in this
interpreter, so PR-001's second surface (the `COMP_LINE`/`_ARGCOMPLETE` path) was confirmed by reading
`_maybe_argcomplete` and `_argcomplete_completer` rather than by provoking it. E-04 case 11 therefore
drives that half by setting `COMP_LINE` directly, which tests the guard without requiring the optional
dependency.

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001..PR-009 all FIXED, none deferred, none open. OQ-01 remains open
at `Blocking: no` with a recorded default and a reviewer's note that the design now has three distinct
silencing paths, which under the 2026-09-10 maintainer ruling does not make the plan `NO-GO`.

Readiness `go-pending-approval`. What a human should weigh at approval, none of it a finding: this
changes the behavior of the ENTRY POINT every other verb goes through, so the blast radius is the whole
CLI even though the mechanism is small and the mismatch path is the only one affected. The accepted
residuals are (1) a shell TAB inside a lane completes against the installed tree rather than the lane's,
by deliberate exemption (D-2); (2) an explicit-argv in-process caller gets no protection, by design; and
(3) a managed target repo is unaffected, which is the intended scope. A maintainer who prefers WARN-ONLY
over re-exec can have it by inverting the `AW_NO_REEXEC` default, and the gate now says so.
