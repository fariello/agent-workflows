# Review findings: plan btth0a

- Subject-Id: btth0a
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree at HEAD `6b37de99`. Structural preflight `aw ipd lint --phase
author --agent` CONFORMED (exit 0) before revision, and `--phase review-finalize --detail` conforms
after. No pre-review snapshot was needed: `git status --short` on the plan file was empty, so it was
committed and unmodified.

THE DEFECT IS REAL AND I RE-MEASURED IT RATHER THAN ACCEPTING THE PLAN'S NUMBERS. From a scratch cwd,
a child `import agent_workflows` resolves `<main checkout>/agent_workflows/__init__.py`; with
`PYTHONPATH=<this worktree>` it resolves the worktree's copy. So F-1 and F-2 hold, the editable
install does point elsewhere, and a rehearsal launched from a lane worktree does exercise the wrong
code. The backlog item `bs1iek` carries the measured consequence verbatim (the `[version-unchanged]`
/ 1.2.1 result that flipped to `1.3.0rc2.dev3716` on the import path alone), and the plan correctly
diagnoses `default_aw_cmd` + `run_install` + `sandbox_env` as the mechanism. F-3's correction of the
backlog's `_installer_cmd` is right, and post-`8ud1is` the definition is in
`agent_workflows/upgrade_rehearsal.py` while `tools/aw_upgrade_test.py` is a pure re-exporting shim
with zero `def`s. F-5's constraint is real: `git show 19313eed^:tests/test_aw_upgrade_test.py` does
contain `self.assertEqual(cmd[1:], ["-m", "agent_workflows"])`.

**THEN I MEASURED THE FIX, AND THE FIX DOES NOT WORK.** This is the finding that justifies the
review, and it is not a stylistic objection: I built the sandbox shape the plan's own Step 0 waves
away and ran the authored design against it. The plan's Step 0 said "The sandbox is a copy of a
TARGET repo, which does not contain an `agent_workflows/` package in normal use", and treated the
contrary case as an oddity that `imported_from` would merely make visible. That premise is FALSE at
this HEAD: `discover_sources()` offers this toolkit's own checkout as a rehearsal source (I confirmed
`agent-workflows` appears in the candidate list of 31), so a self-rehearsal produces precisely a
sandbox containing its own `agent_workflows/`. Against that sandbox, with `PYTHONPATH` pinned exactly
as E-03 prescribed, the child imported `<sandbox>/agent_workflows/__init__.py`: the child's cwd
precedes `PYTHONPATH` on `sys.path`, so the pin silently loses and nothing warns. That is F-6, and it
means the authored fix does not fix the bug in the one case that is most likely to arise while
working on this toolkit.

**AND THE SECOND FAILURE IS WORSE THAN THE FIRST, BECAUSE IT DEFEATS THE PLAN'S OWN DETECTOR.** Add
`PYTHONSAFEPATH=1` so the cwd no longer outranks the pin, and the probe now reports the tool root,
which looks like success. But the INSTALL's stderr then reads `aw: invoked in checkout <sandbox> but
imported agent_workflows from <tool root>; re-running with <sandbox>'s package`. This repository has
a SECOND pinning mechanism I had to find rather than being told about:
`checkout_pin.check_and_reexec`, which `cli.main` invokes on every console-script and `-m` entry, and
which re-execs into the checkout enclosing the child's cwd. So the installer runs the SANDBOX's code
while the plan's `imported_from` says the tool root, because a plain `python -c` probe never enters
`cli.main`. That is F-7: a false negative manufactured by the very observation added to prevent false
negatives, in a tool whose docstring calls rehearsing a different version "the one mistake that would
invalidate every result this tool produces". I consider this the most serious thing in the round,
because it would have shipped as a fix, been believed, and been wrong in a way the tool actively
attested was fine.

THE REMEDY WAS ALREADY IN THE TREE, WHICH IS WHY I REWROTE THE FIX RATHER THAN JUST FLAGGING IT.
`runner_shared` already owns child-package pinning: `runner_package_root()`, `pinned_child_env()`
(prepends the root, sets `AW_PIN_KEEP_ROOT`), and `pinned_module_argv()` (adds `-P` on 3.11+ plus the
`_AW_PIN_STRIP` prologue that drops the cwd while KEEPING the pinned root, and sets
`AW_PINNED_CHILD=1`, which `check_and_reexec` pops as its sanctioned exemption). I drove the
canonical trio against the same self-rehearsal sandbox: it resolved the tool's package, printed NO
re-exec notice, `install --help` exited 0, and `filelock` and `yaml` still imported. So the canonical
mechanism closes both F-6 and F-7 and simultaneously preserves the property OQ-01 rejected `-S` for.
Adopting it also removes a duplicate-mechanism risk the plan did not consider: a second hand-rolled
pin would have to be kept in sync with the one the runners use, and spec `llbr2b` C-10 records nested
tool identity as an INVARIANT.

**THE `wrong-checkout` OBSERVATION COULD NEVER HAVE FIRED.** Independently of the pin, the authored
E-04 was inert. `derive_observations` is called from INSIDE `probe`, on the dict `probe` itself
builds (`state["observations"] = derive_observations(state)`), and `rehearse` only assigns
`result["state"] = probe(sandbox)` afterwards, so records copied onto `result["state"]` arrive after
the observations are computed. I confirmed the shape directly: `derive_observations` handed a
mismatched `install_import` row returns `[]` today, and the authored design never gets a row to it in
a real run. That is F-8. The plan asserted in two places that a mismatched state "emits it", which
was untestable as written. The fix threads the records into `probe` as an optional parameter, ahead of
the `derive_observations` call, while keeping the no-argument `probe(sandbox)` shape the `probe`
subcommand depends on.

TWO MORE THINGS THAT WOULD HAVE COST THE EXECUTOR TIME, both measured. F-9: E-05 prescribed loading
the copied module with a bare `importlib.util.spec_from_file_location` + `exec_module`, which FAILS
on this module on 3.12+ (on 3.14 I got `AttributeError: 'NoneType' object has no attribute
'__dict__'` from `dataclasses._is_type`, because `@dataclass` on `SourceRepo` resolves
`cls.__module__` through `sys.modules`). The suite already ships the correct helper,
`support.load_module`, whose docstring documents this exact reason; it loads the same copied file
without complaint. F-10: the obvious composition `pinned_child_env(sandbox_env(sandbox))` silently
DISCARDS the pin, because `sandbox_env` copies `os.environ` wholesale and is applied as an override.
With a caller `PYTHONPATH=/caller/entry` the wrong order yields `PYTHONPATH=/caller/entry` and the
right order yields `<tool root>:/caller/entry` with `XDG_CONFIG_HOME` and `AW_HOME` still inside the
sandbox. I pinned the order in E-04 with the measurement, because both orders read naturally and only
one is correct.

ON RIGHT-SIZING, which the count-based lint passed and which I did not let that settle. The authored
E-04 bundled four distinct deliverables (a new probe function, a `run_install` change, a
`derive_observations` observation, and a `report` change) across four functions, and E-05 bundled four
independent test surfaces. Both fail diagnostic (a) and (b). I split them: E-05/E-06/E-07 for the
record/observe/report deliverables, and E-08/E-09/E-10 for the test surfaces, with E-09 (the
self-rehearsal test) deliberately isolated because it is the ONLY test that distinguishes the correct
fix from the insufficient one. The checklist went from 6 E-items to 11 and was renumbered (my first
pass used suffixed ids like `E-01b`, which `IPD-I302`/`IPD-I305` correctly refused; the linter caught
it and the final numbering is plain).

ON WHAT THIS PLAN RISKS. It touches a maintainer-only rehearsal rig, not the shipped install path, so
a defect here cannot corrupt a user's repo; the failure mode is epistemic, which is exactly why the
false-negative findings are rated as they are. The plan shares `derive_observations`, `probe` and
`report` with sibling `sbo3hl` (Order 2), which I verified edits different concerns in those same
functions; I noted in the gate that whichever runs second must rebase its hunks rather than assume the
authored surrounding text. `aw check`'s carrier rule reports nothing for this plan
(`evaluate_durable_carrier` returns `[]`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | BLOCKER | IN-SCOPE | A. correctness; C. architecture | self-rehearsal sandbox + `PYTHONPATH=<tool root>`, cwd the sandbox: `import agent_workflows` -> `<sandbox>/agent_workflows/__init__.py`; with `PYTHONSAFEPATH=1` -> `<tool root>/...`; `discover_sources()` lists `agent-workflows` among 31 candidates | **THE AUTHORED FIX DOES NOT FIX THE BUG IN THE REACHABLE CASE.** A bare `PYTHONPATH` pin is outranked by the child's cwd, and `run_install` sets `cwd` to the sandbox, so a sandbox containing its own `agent_workflows/` wins and the rehearsal silently runs the SANDBOX's code. The plan's Step 0 dismissed this as not occurring "in normal use", but the toolkit offers ITSELF as a rehearsal source at this HEAD, so it is the self-rehearsal path, not an oddity. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-04 rewritten onto `runner_shared.pinned_child_env` + `pinned_module_argv` (whose `-P`/`_AW_PIN_STRIP` strips the cwd while keeping the pinned root and site-packages). New E-02 reproduces the failure before the fix is applied; new E-09 is a self-rehearsal test that fails against a `PYTHONPATH`-only implementation. Step 0, Concern, Goal and Scope corrected. |
| PR-502 | BLOCKER | UNDER-SCOPE | A. correctness; F. prevent silent failure | with `PYTHONPATH=<tool root> PYTHONSAFEPATH=1`, cwd the self-rehearsal sandbox: probe prints `<tool root>/...` while `python3 -m agent_workflows --version` STDERR reads `aw: invoked in checkout <sandbox> ... re-running with <sandbox>'s package`; `cli.main` calls `checkout_pin.check_and_reexec()` | **A SECOND MECHANISM RE-EXECS THE INSTALLER INTO THE SANDBOX'S PACKAGE, AND THE PLAN'S OWN DETECTOR WOULD REPORT CLEAN WHILE IT HAPPENED.** `check_and_reexec` re-execs when the checkout enclosing cwd differs from the imported package. Because a plain `python -c` probe never enters `cli.main`, `imported_from` attests the tool root while the install ran the sandbox's code: a manufactured false negative inside the tool whose stated purpose is preventing exactly this. The plan never mentions `checkout_pin`. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-04 adopts `pinned_module_argv`, whose bootstrap sets `AW_PINNED_CHILD=1`, the exemption `check_and_reexec` pops. E-05's probe must use the SAME pinned argv shape as the install, so it can no longer answer a different question. E-09 asserts the notice is ABSENT from the captured output, against `runner_shared._CHECKOUT_PIN_NOTICE_PREFIX` rather than a copied string. Step 0 and the Concern now name the mechanism. |
| PR-503 | BLOCKER | IN-SCOPE | A. correctness; E. verification | `probe` body: `state["observations"] = derive_observations(state)`; `rehearse`: `result["runs"].append(...)` precedes `result["state"] = probe(sandbox)`; `derive_observations({"install_import": [<mismatch>]})` -> `[]` | **THE `wrong-checkout` OBSERVATION AS AUTHORED COULD NEVER FIRE.** `derive_observations` runs inside `probe` on the dict `probe` builds; records `rehearse` copies onto `result["state"]` arrive after the observations are computed. The plan asserted twice that a mismatched state "emits it", which was untestable as written, so the plan's secondary safety net was inert. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | New E-06 threads the records INTO `probe` via an optional `install_import` parameter placed BEFORE the `derive_observations` call, keeping the no-argument `probe(sandbox)` shape the `probe` subcommand uses. V-06 requires the no-argument case, the firing case, the non-firing case and a sibling-prefix case. |
| PR-504 | HIGH | IN-SCOPE | E. testing (a step that cannot be executed as written) | on 3.14: `AttributeError: 'NoneType' object has no attribute '__dict__'` at `dataclasses._is_type`, from `@dataclass` in the copied `upgrade_rehearsal.py`; `tests/support.py` `load_module` docstring: "Registration is required so that decorators like @dataclass ... can resolve `cls.__module__`"; the same file loads cleanly through it | **THE PRESCRIBED TEST LOADER FAILS OUTRIGHT ON THIS MODULE.** E-05 named a bare `spec_from_file_location` + `exec_module`, which raises on 3.12+ because `@dataclass` on `SourceRepo` resolves `cls.__module__` through `sys.modules`. The suite already ships the helper that fixes this and documents why. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-08 now mandates `support.load_module` and forbids the bare loader, with the measured traceback as the reason; it also requires a unique module name per test and `sys.modules` cleanup in a `finally`, so a registered copy cannot leak under pytest-randomly's ordering. Recorded as a Step 0 convention. |
| PR-505 | HIGH | IN-SCOPE | A. correctness (an order-dependent composition) | with caller `PYTHONPATH=/caller/entry`: `pinned_child_env(sandbox_env(sb))` -> `PYTHONPATH=/caller/entry`; pin-first-then-override -> `<tool root>:/caller/entry`, `XDG_CONFIG_HOME`/`AW_HOME` still under the sandbox | **THE NATURAL-LOOKING ENV COMPOSITION SILENTLY DISCARDS THE PIN.** `sandbox_env` copies `os.environ` wholesale, so passing it as `pinned_child_env`'s override argument hands back the caller's `PYTHONPATH` and the pin is gone, with no error. Both orders read plausibly and only one is correct, so an executor had a coin flip on the plan's central mechanism. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-04 specifies the order explicitly (pin first, then `sandbox_env`'s keys EXCEPT `PYTHONPATH`), names the wrong form as forbidden, and carries the measurement. V-04 requires the composition check with a caller `PYTHONPATH` set, asserting both the pin and the sandbox isolation survive. |
| PR-506 | HIGH | UNDER-SCOPE | G. executability (right-sizing / conceptual density) | authored E-04 spanned `probe_import_origin`, `run_install`, `derive_observations` and `report`; authored E-05 bundled four independent test surfaces in one item | **TWO E-ITEMS EACH CARRIED FOUR DISTINCT DELIVERABLES**, failing right-sizing diagnostics (a) and (b): each touched multiple independent code regions and would need several unrelated V-items. The count-based size lint passed, which does not clear conceptual density. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into E-05 (record), E-06 (make the observation able to fire), E-07 (report) and E-08/E-09/E-10 (worktree simulation / self-rehearsal / unchanged-path and rows), with E-09 isolated because it is the only test that distinguishes the correct fix. Checklist 6 -> 11 E-items, renumbered; V-* re-bijected 1:1. `aw ipd lint --phase review-finalize` conforming. |
| PR-507 | MEDIUM | IN-SCOPE | E. verification (evidence that cannot fail) | authored Required tests and V-05 presented the suite run and the worktree simulation as the outcome evidence; a `PYTHONPATH`-only implementation passes both | **THE PLAN'S TERMINAL EVIDENCE COULD NOT DETECT ITS OWN CENTRAL DEFECT.** The worktree-simulation test passes under the insufficient fix, because a sandbox with no `agent_workflows/` never exercises the cwd-precedence or re-exec paths. So an executor could paste a green suite and an honest-looking V-05 having shipped the broken pin. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-09 is designated THE LOAD-BEARING VALIDATION and requires the self-rehearsal test shown FAILING against a `PYTHONPATH`-only implementation (drop the `pinned_module_argv` half, keep the env half), not merely passing against the final code. Required tests and the gate both state that a green suite is not sufficient evidence here. |
| PR-508 | MEDIUM | IN-SCOPE | A. correctness (a comparison that misclassifies siblings) | authored E-04: "fires when an `imported_from` is present and not under `expected_root`", with no containment rule stated | A `startswith` containment test treats `<root>-other` as inside `<root>`, so a genuinely wrong checkout whose path shares a prefix with the tool root would be judged correct and the observation would stay silent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 requires `commonpath`-style containment and explicitly forbids a bare `startswith`; E-10 adds a sibling-prefix row (`<root>-other`) that must FIRE, and V-06/V-10 demand it, so the comparison is pinned by a test rather than by prose. |
| PR-509 | LOW | IN-SCOPE | C. architecture; G. executability | `runner_shared` import measured at ~0.12s; `upgrade_rehearsal` imports `agent_workflows.config` lazily inside `search_roots`; `runner_shared.py` and `checkout_pin.py` absent from `- Scope-Paths:` | Adopting `runner_shared` raises two things the plan had no need to state before: a module-scope import would add ~0.12s to a harness that is otherwise cheap to import, and an executor might "fix" a stubborn pin by editing the shared pinning code, which is a driver-authoritative contract (spec `llbr2b` C-10 makes nested tool identity an INVARIANT). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 mandates a LAZY import inside `tool_repo_root()` with a `Path(__file__)` fallback, matching the existing `search_roots` precedent, and V-03 asserts `agent_workflows.runner_shared` is absent from a fresh child's `sys.modules` after importing the harness. The Scope check declares both shared modules out of bounds and the gate adds a STOP condition for touching either; the two underscore-prefixed symbols consumed are justified in the Scope check. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The authored `PYTHONPATH` pin is insufficient (PR-501/PR-502). Rewrite the fix onto the canonical `runner_shared` pin, or REPLAN the plan? | REWRITE IN PLACE onto `pinned_child_env` + `pinned_module_argv`. The plan's diagnosis, scope, fence and test strategy are all sound; only the mechanism was wrong, and the correct mechanism already exists and needs no new design. | (a) REPLAN: rejected, a replan implies the approach is unsound, but the approach (pin the child's import path, record what it imported, observe a mismatch) is exactly right and the repair is bounded to one E-item's mechanism plus its tests. (b) Keep `PYTHONPATH` and add `PYTHONSAFEPATH=1` only: rejected, measured to fix F-6 but NOT F-7, since `checkout_pin` then re-execs into the sandbox's package; it would have shipped the more dangerous half of the bug. (c) Hand-roll an equivalent bootstrap inside `upgrade_rehearsal`: rejected, it duplicates a mechanism the runners already own and must stay in sync with, against a spec that makes nested tool identity an invariant. | Measured against a self-rehearsal sandbox: canonical trio resolves the tool package, emits no re-exec notice, `install --help` exits 0, `filelock`/`yaml` still import; `runner_shared.pinned_child_env`/`pinned_module_argv`/`_AW_PIN_STRIP`; `checkout_pin.check_and_reexec` exemption on `AW_PINNED_CHILD`; spec `llbr2b` C-10. | yes |
| D-2 | `-S` was rejected by OQ-01 for dropping site-packages. Does `-P`/`PYTHONSAFEPATH` inherit that objection? | NO. `-P` removes only the SCRIPT/CWD entry from `sys.path`; site-packages is untouched, so third-party dependencies remain importable. OQ-01's rejection of `-S` stands and does not extend to `-P`. | (a) Treat `-P` as equivalent to `-S` and keep a bare `PYTHONPATH`: rejected, it conflates two different flags and would preserve F-6. (b) Drop dependency-bearing behavior and accept `-S`: rejected for OQ-01's original and still-correct reason. | Measured: under `-P` plus the pinned env, a child imported `agent_workflows`, `filelock` and `yaml` successfully, and `install --help` exited 0; `pinned_module_argv` applies `-P` only on 3.11+ while `pyproject.toml` declares `requires-python = ">=3.9"`, and the `_AW_PIN_STRIP` prologue covers older interpreters. | yes |
| D-3 | Should `wrong-checkout` be reached by threading records into `probe`, or by moving `derive_observations` out of `probe` to `rehearse`? | THREAD THEM IN, via an optional `probe(sandbox, install_import=...)` parameter applied before the `derive_observations` call. | (a) Move the `derive_observations` call out of `probe` into `rehearse`: rejected, `probe` is also the `probe` subcommand's entry point and its state dict is documented as carrying `observations`; moving the call would silently drop observations from `aw upgrade-test probe`, a user-visible regression outside this plan's scope. (b) Compute `wrong-checkout` in `report` only: rejected, it would be absent from `--json`/`--agent` output and from the marker file, i.e. invisible to the machine consumers. | `probe`'s body sets `state["observations"]`; `cmd_probe` calls `probe(sandbox)` and prints/serializes that state; `rehearse` assigns `result["state"] = probe(sandbox)` after its runs. | yes |
| D-4 | Is a green suite plus the worktree-simulation test sufficient outcome evidence (authored V-05)? | NO. Designate the self-rehearsal test the load-bearing evidence and require it shown FAILING against a `PYTHONPATH`-only implementation. | (a) Leave the authored evidence: rejected, a `PYTHONPATH`-only fix passes the worktree simulation and the whole suite, so the evidence cannot detect the defect it is offered against. (b) Require only that the new tests pass on final code: rejected, passing on the final code does not show the canonical pin is NECESSARY, and necessity is the claim under review. | The worktree-simulation sandbox contains no `agent_workflows/`, so it never exercises cwd precedence or the re-exec path; both were measured only against the self-rehearsal shape. | yes |
| D-5 | E-05's module loader fails on 3.12+. Mandate `support.load_module`, or write a local loader in the test? | MANDATE `support.load_module`, with unique names and `sys.modules` cleanup. | (a) A local `spec_from_file_location` + manual `sys.modules` registration in the test: rejected, it re-implements a helper the suite already exports and whose docstring exists to record this exact failure. (b) Avoid loading a copy at all and test `tool_repo_root` in isolation: rejected, it would delete the only test that proves the pin follows the TOOL's location rather than the runner's cwd, which is the plan's whole claim. | Measured `AttributeError` from `dataclasses._is_type` on 3.14 with the bare loader; `support.load_module` loaded the same copied file and its docstring states the registration requirement; the test file already imports `load_module` from `support`. | yes |
| D-6 | The plan shares `derive_observations`/`probe`/`report` with sibling `sbo3hl` (Order 2) and the plan claims independence. Raise it, or leave it? | RAISE IT in the gate as a rebase obligation, without adding a dependency edge. | (a) Add `- Item-Dependencies:` on `sbo3hl`: rejected, neither plan needs the other's outcome and an artificial edge would serialize work the runner isolates per item anyway. (b) Leave the independence claim unqualified: rejected, it is true of the CONCERNS and false of the TEXT; whichever executes second will not find the authored surrounding lines. | `sbo3hl`'s `- Scope-Paths:` is the same two files and its E-items edit `derive_observations`, `probe` and `report`; both declare `- Item-Dependencies: executed:8ud1is` only. | yes |

### Deferred and open

- (none). All nine findings were FIXED in place. The three BLOCKERs and three HIGHs all assessed at
  Medium or Low overall Remediation Risk (the fix was bounded, the correct mechanism already existed
  in-tree, and every repair was verifiable by measurement), so the Fix Bar permitted no deferral and
  none was taken. Because nothing was left `OPEN` or `DEFERRED`, no escalation to a `- Blocking: yes`
  question was required.
- Both authored open questions were re-verified rather than accepted, and one was CORRECTED. OQ-01's
  conclusion ("use `PYTHONPATH`") was measured FALSE and its rationale rewritten; its rejection of
  `-S` was independently re-checked and RETAINED, with `-P` distinguished from `-S` (D-2). OQ-02's
  observation-not-verdict answer was retained, with its residual case sharpened: the
  sandbox-contains-its-own-package scenario is not residual under the authored fix and is now closed
  in the mechanism.
- No `Reversible: no` decision was made. All six decisions are plan-text choices on an unexecuted
  plan, and none changes a published interface, migrates data, or deletes anything.

HONEST LIMITS, stated because they bound what this round proves. FIRST, every measurement was taken
on ONE machine and ONE interpreter (3.14, with this repository installed editable). The cwd-precedence
and re-exec behaviors are interpreter-level and I expect them to generalize, but `pinned_module_argv`
applies `-P` only on 3.11+ while the project supports 3.9, so on 3.9/3.10 the pin rests on the
`_AW_PIN_STRIP` prologue alone; I did not test a 3.9 or 3.10 interpreter, and E-02 is written to
surface a divergence rather than assume one cannot happen. SECOND, I did not run the full suite: this
review changed no code, and E-11 owns that. THIRD, I verified the canonical pin works for `--version`
and `install --help`, not for a full real `install -y` into a sandbox copied from a live repo; a full
install exercises far more code and E-09's `install_args` choice trades fidelity for speed, which is
a deliberate and stated compromise. FOURTH, I confirmed the toolkit is offered as a rehearsal source
at this HEAD but did not establish that a maintainer has ever actually self-rehearsed; the case's
reachability is proven, its historical frequency is not. FIFTH, my finding that the authored
`wrong-checkout` could never fire rests on reading the call order plus driving `derive_observations`
directly; I did not run a full authored-design rehearsal end to end, because the fix removes that
design.
