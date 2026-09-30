# Review findings: plan s2yf26

- Subject-Id: s2yf26
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-701 (HIGH, fixed), PR-702 (MEDIUM, fixed), PR-703 (MEDIUM, fixed), PR-704 (LOW, fixed), PR-705 (LOW, fixed)

## Round 1

Reviewed at HEAD `2c1d4f37` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize` reports `conforming` after revision. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply.

THE PLAN IS UNUSUALLY WELL EVIDENCED AND ITS DIAGNOSIS IS CORRECT. I re-derived every load-bearing claim
rather than reading it. F-01 reproduces exactly: `_completion_tip` has three call sites and they are inside
`_run_install`, `_install_all`, and `_run_setup`, with `_completion_state` having one caller and
`installed_completion_state` one production caller. F-02 reproduces (`stale` on this checkout). F-06
reproduces on inspection: of the nine repo-wide "must be empty" assertions, the `strip() == ""` ones target
`git` subprocesses and the single `aw` case (`tests/test_completion.py`) asserts stdout, so a stderr notice
gated on interactivity cannot reach them. F-07 reproduces (`conformance_matrix.py` has no importer but
itself plus a `command_surface.py` comment). F-08 reproduces exactly (three mentions, none a call, one of
them the stale test docstring). F-11 reproduces in the prototype. Every convention in "Project conventions
discovered" checks out, including `config._ALLOWED_TOP_KEYS` being a five-element frozenset, the two
sidecar precedents and their stated reason, `Term.stream` defaulting to stdout with only `step_cue`
defaulting to stderr, and `is_interactive`'s precedence ladder.

THEN I PROTOTYPED E-01 THROUGH E-04 END TO END, because the plan's risk is not detection but the blast
radius of speaking from `cli.main`, and that is not readable. The prototype works: a human interactive
`aw layout` produced the notice with exactly ONE counted probe, an immediate repeat produced zero probes via
the stamp, `aw completion bash` stdout stayed a clean 6171-byte script starting `# bash completion for aw`
with empty stderr, and a `SystemExit`-raising `check --help` never reached the post-return hook. That
confirms the approach and bounds every finding below to HOW the gates read their inputs.

THE ONE SERIOUS DEFECT, which only prototyping could find. E-04 specified the `__complete` and `completion`
suppressions as tests on `argv`'s first token, and an argv-token gate suppresses NOTHING for a real user.
Three independent measurements, each alone fatal. FIRST, `cli.main`'s signature is `main(argv=None)` and the
entry is `raise SystemExit(main())`, so `argv` is `None` on every console-script invocation; instrumenting
the real entry in a subprocess with `aw completion bash` printed `HOOK SEES argv=None
sys.argv[1:]=['completion', 'bash']`, and `list(argv or [])[:1] == ["completion"]` is therefore False.
SECOND, even with argv supplied, a global flag may precede the command: `parse_args(["--no-color",
"__complete", "aw", "l"])` yields `args.command == "__complete"` while `argv[0]` is `--no-color`. THIRD,
`args` is local to `_dispatch` and appears nowhere in `main`'s body, so the hook cannot read the namespace.
The fix is cheap and provably sufficient: measured inside `_dispatch`, `select_output(args)` sits at body
offset 10121 while the `__complete` branch is at 11633 and the first `"completion"` routing at 11571, so
E-03 now publishes `args.command` beside the mode and the gates read `get_last_command()`. I recorded the
honest mitigation too: during a real TAB press the streams are pipes and `is_interactive()` measured False,
so gate (e) would have caught this in practice; the exposure was a probe on a keypress for any caller
forcing interactivity, not a guaranteed one. That is why it is HIGH and not BLOCKER.

TWO CORRECTIONS THAT WOULD HAVE COST AN EXECUTOR A CYCLE EACH. `cli._COMPLETION_VERBS` does not exist as a
module attribute (`AttributeError`); the name is a local inside `cli._build_parser`, so E-05's "register it
in this list" pointed at nothing importable. And `--json`/`--agent` are PER-LEAF flags: measured,
`parse_args(["--json", "layout"])` leaves `args.json is False` and `select_output` returns
`OutputMode.HUMAN`, while `["layout", "--json"]` returns `JSON`. That matters twice over, because the
plan's suppression vectors were written in the broken order (so those rows would have asserted silence for
the wrong reason and passed with gate (d) deleted) and because it independently proves the mode gate must
read the published `select_output` result rather than any argv scan.

ONE MEASUREMENT-HYGIENE FIX. The performance figures drifted in a day: probe 52.1-62.2ms warm versus the
plan's 45-55ms, 219.8ms first-in-process versus ~151ms, `aw --version` 323ms versus ~280ms, and
`__version__` already moved from `1.3.0rc2.dev5565+g6402f145` to `1.3.0rc2.dev6002+g2c1d4f37`. The ARGUMENT
is untouched (both runs give about 16-19 percent, and the stamp-read figure reproduced to the digit at
0.0184ms), but an executor re-deriving would have found every number wrong with nothing telling them
whether that was a finding. The version drift is also the churn argument demonstrated rather than asserted:
the raw string changed while the derived key held at `1.3.0rc2`.

WHAT I DELIBERATELY DID NOT CHANGE. F-04's distinction between a stamp as DETECTOR and as THROTTLE is sound
and correctly cites `installed_completion_state`'s docstring; the warn-only inheritance is correct; OQ-01 is
legitimately maintainer-owned taste and correctly non-blocking, and its `Carrier-Declined` reasoning holds
because both answers are reachable with no outstanding work; OQ-02's rejection of `aw doctor` is correct on
the repo-scoped-versus-user-scoped ground it gives; and the four `Deferred` rows are all properly justified,
with `rayd4c` verified to exist as an open backlog item. The plan's own under-scope statements are honest and
I strengthened none of them because none needed it.

Nothing in `agent_workflows/`, `tests/`, or `README.md` was modified. All prototype work lived in gitignored
scratch under `.aw/state/`; `git diff --stat agent_workflows/ tests/ README.md` is empty.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | A. Correctness / C. Operability (a suppression gate that fails open on the only path that matters) | Three measurements. (1) Subprocess-instrumented real entry, `aw completion bash`: `HOOK SEES argv=None sys.argv[1:]=['completion', 'bash']`; `cli.main`'s signature is `main(argv=None)` and the entry is `raise SystemExit(main())`. (2) `parse_args(["--no-color", "__complete", "aw", "l"])` gives `args.command == "__complete"` with `argv[0] == "--no-color"`. (3) `args` appears nowhere in `main`'s body. Ordering that makes the fix safe: `select_output` at `_dispatch` body offset 10121, `"completion"` routing at 11571, `__complete` branch at 11633 | **E-04's `__complete` and `completion` gates are argv-token tests, so for every real invocation they suppress nothing: `argv` is `None` and the gate sees `[]`.** The plan's own F-12 warns that a naive hook runs on every TAB press, and the gate written to prevent it does not. A global flag before the command defeats it even when argv is passed, and the hook cannot reach `args` to do better | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now publishes the resolved COMMAND beside the resolved mode (both `None`-defaulted, both restored in `main`'s `finally`), with the three measurements and the offset ordering recorded. E-04's hook loses its `argv` parameter (`_maybe_notify_stale_completion(rc)`), gates (b)/(c) read `get_last_command()`, a `None` command suppresses, and the third executor refusal in the gate forbids reverting to argv. V-03 requires the command-global transcript and fails a mode-only one; V-04 requires the two rows only this design passes plus a quoted hook body containing no `argv`/`sys.argv`. New F-13, new OQ-03 recording the rejected alternatives, `- Scope:` and proposed-changes entries 3 and 4 updated, F-12 annotated with the measured `is_interactive()` mitigation |
| PR-702 | MEDIUM | IN-SCOPE | G. Plan executability (an instruction naming a symbol that does not exist) | `cli._COMPLETION_VERBS` raises `AttributeError: module 'agent_workflows.cli' has no attribute '_COMPLETION_VERBS'`. `grep` finds exactly two mentions, both inside `cli._build_parser`: `_COMPLETION_VERBS = ("install", "uninstall")` and the next line `_completion_targets = [*completion_mod.SUPPORTED_SHELLS, *_COMPLETION_VERBS]`. `cli._run_completion`'s routing is the single line `if target in ("install", "uninstall")` followed by a shell-name fallthrough | **E-05 and F-09 tell an executor to register `status` in `cli._COMPLETION_VERBS`, which is a local variable, not a module constant.** The adjacent comment's additive promise is quoted correctly, so only the scope is wrong, but an executor would hunt for a module-level tuple that is not there. Separately, E-05 did not say the new branch must precede the shell-name fallthrough, and a branch added after it would pass `status` to script generation | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 says LOCAL VARIABLE, names both lines and the enclosing function, warns against looking for a module constant, and requires the `status` branch BEFORE the shell-name fallthrough with the failure mode named. F-09 carries the correction and the verified `command_surface` declaration values. V-05 now requires evidence that `status` stdout does not begin with the generated script's header. New F-14 |
| PR-703 | MEDIUM | IN-SCOPE | E. Testing (test vectors that assert the right outcome for the wrong reason) | `parse_args(["--json", "layout"])` -> `args.json is False`, `select_output` -> `OutputMode.HUMAN`; `parse_args(["layout", "--json"])` -> `OutputMode.JSON`. Same for `--agent`. `layout` and `attention` both carry `--json`/`--agent` from the common parent | **The plan's suppression vectors are written `["--json", "layout"]`, but these are per-leaf flags that must FOLLOW the command, so those rows would resolve to HUMAN mode and assert silence for a reason unrelated to gate (d).** Such a row passes even with the gate deleted, in a plan whose whole safety argument rests on that gate. It also independently proves the mode must come from the published `select_output` result, never from an argv scan | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04's gate (d) paragraph records the measurement and why it justifies the published-result design; E-03's expected outcome uses `["layout", "--json"]`; the Required-tests hook bullet and V-04 both mandate the flag AFTER the command and state that a pre-command spelling asserts silence for the wrong reason. New F-15 |
| PR-704 | LOW | IN-SCOPE | Evidence accuracy (live measurements presented as flat facts) | Re-derived at review: probe 52.1-62.2ms warm (plan: 45-55ms), 219.8ms first-in-process (plan: ~151.5ms), `cli._build_parser` 49.4ms warm with no `lru_cache` and no `cache_clear`, `aw --version` 323ms and `aw layout` 301ms (plan: ~283/280ms), stamp read 0.0184ms and `exists()` 0.0031ms (plan: 0.0184/0.0024ms), `__version__` now `1.3.0rc2.dev6002+g2c1d4f37` | **F-03's and F-10's figures moved within a day and are stated as flat facts with no re-derivation instruction**, so an executor re-deriving them would find nearly every number wrong and have nothing telling them whether that is a finding. The conclusions are untouched: both runs give about 16-19 percent and the stamp read reproduced to the digit | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03 restated with both dated measurement sets side by side, the RATIO named as the durable claim, an explicit "neither is a bar", and an instruction that drift is expected and only a ratio collapse is a finding. F-05 records the exact reproduction. F-10 records that the raw version changed while the derived key held, which demonstrates its own churn argument, plus the measured `parse_our_version` result for all four E-02 vectors. New F-17 |
| PR-705 | LOW | UNDER-SCOPE | G. Plan executability (an incomplete execution contract) | The gate carried the commit/never-push rule, the bare-run instruction, the honesty MUST, and the two refusals, but no scope fence, no open-questions statement, and a lifecycle paragraph naming `aw ipd begin`/`finalize` without the conditional-ownership distinction | **The gate omits a scope-fence DECLARATION, omits the open-questions statement, and states the lifecycle transition without the conditional runner/executor ownership the repository's contract requires** (a managed lane refuses an agent with `AW-LIFECYCLE-ROLE-001`, so an unconditional executor instruction is wrong) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate gains a declaration-style scope fence naming the four declared paths, the make-then-justify-at-finalize wording, the one genuinely-unsafe stop condition (an unresolvable concurrent edit to `cli.py`/`completion.py`), the open-questions statement, and the unconditional-finalize/conditional-owner paragraph with `aw ipd finalize s2yf26 ... --apply` and the never-hand-roll prohibition. It also records that `- Readiness:` is a review output and that `lz16f3` is already `graduated` (verified) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-701: the argv-token gates fail open. Publish the command, fall back to `sys.argv`, or move the hook? | PUBLISH the resolved command from `_dispatch`, beside the mode E-03 already publishes | (a) `sys.argv[1:]` fallback; (b) move the hook into `_dispatch` where `args` is in scope; (c) change `_dispatch` to return `(rc, args)` | Option (a) fixes only the `argv=None` half and leaves the flag-position half broken, and it re-derives a decision argparse already made, which is the very re-derivation E-03's own rationale rejects. Option (b) forfeits F-11's measured property, since `_dispatch` is the frame `--help` and usage errors raise `SystemExit` out of, so the hook would have to re-earn the placement guarantee the plan relies on. Option (c) changes a return contract every in-process caller and test reads, for a diagnostic. The chosen option costs one global and one assignment beside one the plan already makes, and is provably sufficient: `select_output` runs at `_dispatch` body offset 10121 against 11571 and 11633 for the two commands that must be suppressed | yes |
| D-2 | PR-701 severity: is a probe on a TAB keypress a BLOCKER? | HIGH, not BLOCKER | (a) BLOCKER, since the plan's own F-12 calls this out as the failure to prevent and a 50ms probe per keypress is user-hostile; (b) MEDIUM, since nothing ships until the plan executes | Option (a) was the first instinct and measurement ruled it out: during a real TAB press stdin and stdout are pipes and `is_interactive()` returned False, so gate (e) would in practice have caught what gate (b) missed. The defect is a gate that does not do its job and whose failure is masked by a different gate, which is a real correctness finding but not a guaranteed user-visible harm. Option (b) understates it, because this is exactly the class of defect that survives review by looking obviously correct on the page | yes |
| D-3 | Should the review author the implementation, having prototyped it working? | NO; the prototype stays throwaway scratch | (a) Promote the prototype into `cli.py`/`completion.py`, since it is measured working; (b) paste the prototype source into the plan as the intended implementation | The workflow edits planning documents only. Beyond that, the prototype deliberately cut corners the deliverable must not: it monkeypatched `select_output` rather than editing `_dispatch`, kept the stamp in a dict instead of the atomic-write sidecar E-01 specifies, and asserted nothing about the docstring contract the spec-sync section requires. Option (b) would freeze probe-grade details into an executable contract. What the prototype legitimately contributes is the findings and F-16's evidence that the design works | yes |
| D-4 | OQ-01 is `open` with `Owner: maintainer` and the plan is otherwise clean. Does that block readiness? | NO; `go-pending-approval` | (a) Treat the open question as blocking and record `no-go`; (b) resolve OQ-01 myself and close it | Option (a) contradicts the maintainer ruling of 2026-09-10 (plan `qhy3i3` OQ-01) that only an unresolved BLOCKING question forces `NO-GO`; OQ-01 carries `- Blocking: no` and its author's judgement that it does not stop work is correct, since both answers are reachable with no outstanding work. Option (b) would be a reviewer deciding CLI-noise taste on the maintainer's behalf, which is precisely the judgement the plan correctly declined to make unilaterally; its `Carrier-Declined` reasoning already establishes that nothing is left unfixed either way | yes |
