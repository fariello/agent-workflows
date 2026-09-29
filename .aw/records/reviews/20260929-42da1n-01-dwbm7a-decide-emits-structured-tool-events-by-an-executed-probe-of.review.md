# Review findings: plan dwbm7a

- Subject-Id: dwbm7a
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `d449f3d2` in a lane worktree. Structural preflight `aw ipd lint --phase author` reported
`conforming` with TWO `IPD-Z602` density advisories (E-03, E-04); after revision `--phase review-finalize`
reports `conforming` with ONE (the E-05 wiring item), and both were examined on merits rather than
deferred to, since the linter's own contract is that a passing count check does not clear conceptual
density. No pre-review snapshot was owed: the plan was committed and unmodified (`git status --short`
empty) and the lane-input copy under `.aw/state/lane-inputs/rev-22/` is byte-identical (`diff -q` reports
IDENTICAL). Bare suite at review HEAD: `3246 passed, 2 skipped, 3 warnings in 48.39s`, which independently
confirms the baseline the plan recorded. NO PRODUCTION FILE OR TEST WAS MODIFIED by this review; every
measurement was a read, an in-process render call, or a timing probe.

THIS PLAN IS EXCEPTIONALLY WELL MEASURED AND EVERY ONE OF ITS EIGHT FINDINGS REPRODUCES. F-01: `host
capabilities antigravity` prints `NO   emits_structured_tool_events` while `supports_session_resume`
carries a `why:` line and this field carries none. F-02: `agy_runipd` argv contains `"--output-format",
"stream-json"` and `render_agy_event` documents and parses that schema; `oc_runipd` builds `["--dir",
agent_dir, "--format", "json"]`. F-03: `run_discovery_then_execution` appears only as its own `def`, its
`__all__` entry, and three call sites in `tests/test_host_sandbox_profile.py`. F-04 reproduces exactly:
`("opencode","linux")` True, `("opencode","darwin")` False, `("opencode","win32")` False,
`("antigravity","linux")` False. F-05 reproduces: the `tool_call`/`tool_name` shape renders `None` while
the `"tool"`/`name` shape renders `'❯ bash:  pytest -q'`, and a lambda palette raises `AttributeError:
'function' object has no attribute 'enabled'` on BOTH renderers. F-06: `ACTION_CLASSES == ('read_only',)`
with requirements `{'read_only': ()}`, and `runner_shared` calls `_hsp.preflight_host_capabilities`. F-07:
re-measured 26 ms / 32 ms for `detect_host_capabilities` and 23 ms / 25 ms for the resume probe. F-08: no
pending plan other than this one declares `host_sandbox_profile.py` in `- Scope-Paths:`. The cited
precedents also resolve: `mjx7ne` PR-007 exists and contains "attempt-not-inspect"; `qul11h` PR-302/303/304
exist and say what the plan says they say; both sibling plans are in `executed/`.

THE PLAN'S DEFECT IS ONE LAYER ABOVE ITS OWN BEST FINDING, which is what makes PR-001 worth a BLOCKER on
an otherwise excellent plan. F-05 correctly warns that a PLAUSIBLE-LOOKING tool-event schema silently
renders `None`. The plan then prescribes a negative control that is wrong in exactly the same way: it
assumes an unparseable line yields nothing, when both renderers have a `JSONDecodeError` branch that
ECHOES the line. An executor who trusted the plan's own stated discipline would write `assert
render(junk) is None`, watch it fail, and most plausibly resolve the contradiction by weakening the
positive assertion to "non-empty" - which the junk fallback also satisfies, producing a probe that
passes for a host with no schema awareness at all. The plan's stated risk ("a plausible probe would
report a capable host as False") therefore applied to the plan itself.

I also verified what does NOT need fixing, so the reviewed scope is legible: the two-halves decision
(OQ-02) is right and its fail-closed reasoning holds; the LATENT verdict (OQ-01) is correct and its
evidence reproduces exactly; the refusal to add an `ACTION_CAPABILITY_REQUIREMENTS` row is right and the
`4h7tt0` OQ-02 ruling it cites is real; the `Carrier-Declined` reasoning on all five Deferred rows is
sound (each states why no obligation exists rather than deferring work); the `CONTRACT_FIELDS` and
`host_cmd._capability_rows` analysis is exactly right (the tuple already lists the field; the report
introspects `to_dict()` so the `why:` line appears automatically); and the three direct-construction
consumer tests do pass `emits_structured_tool_events=True` explicitly and so are insensitive to a
detection change, as OQ-01 claims.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness; E. Testing (the prescribed probe inverts the verdict it exists to fix) | plan E-03 as authored ("require that a deliberately UNPARSEABLE line does NOT produce a tool line"); `agy_runipd.render_agy_event`'s `except json.JSONDecodeError` branch; `render_stream.render_event`'s equivalent | **THE PRESCRIBED NEGATIVE CONTROL IS FALSIFIED BY MEASUREMENT, and following it yields a probe that reports BOTH capable hosts False.** Measured at review HEAD `d449f3d2`: `render_agy_event("not json at all", pal)` returns `'  not json at all'` and `render_event("not json at all", pal)` returns `'not json at all'` - a rendered dim line, NOT `None` - because each renderer echoes an undecodable line rather than dropping it. So `assert render(junk) is None` FAILS for both hosts, and the natural repair (weakening the positive assertion to "non-empty") is satisfied BY THAT SAME FALLBACK, producing a probe that passes for a host with no schema awareness. This is the plan's own F-05 hazard ("a plausible probe would report a capable host as False") applied to the plan itself, one level up. THE DISCRIMINATORS WERE MEASURED: a WELL-FORMED NON-TOOL event returns `None` from both (`{"type":"totally_unknown","part":{}}`; `{"event":"step_update","step_update":{"state":"DONE","step_type":"thinking"}}`), and the tool lines (`'❯ bash:  {"command": "pytest -q"}'`, `'❯ bash:  pytest -q'`) CONTAIN the tool name while the junk fallback does not. Also measured: `""` and `"   "` do return `None`, so they are not usable controls either (returning `None` for no input is not evidence of parsing). | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-03 now FORBIDS the unparseable-line control by name with the measured strings, prescribes both discriminators (well-formed non-tool -> `None`; tool line contains the tool name), and states why non-empty alone is insufficient. V-03 demands all four cases including the junk-is-not-`None` proof and FAILS the item for either mistake. Added F-09 and OQ-03; the gate's fence names it as the one mistake that silently inverts the fix. |
| PR-002 | HIGH | IN-SCOPE | Step 1 evidence (a cited test that does not exist) | plan E-01 as authored (`tests/test_agy_runipd_cli.py::AgyStreamRenderingTests`); measured: no such class; the enclosing class of `test_render_agy_event_and_tracker` is `AgyVerbosityFlagTests` | **THE SHIPPED-PROOF COMMAND NAMES A NONEXISTENT TEST CLASS, so it collects nothing and `no tests ran` could be read as the proof passing.** E-01 is the plan's premise re-measurement step and this is one of its four required measurements, so a silently-empty run undermines the step that exists to stop the executor trusting the plan over the tree. The METHOD is real and asserts what the plan says. Same class as `4h7tt0` PR-007 (a V-item requiring a named test that did not exist). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now gives the fully qualified node id with `AgyVerbosityFlagTests`, records that the authored name does not exist and why that mattered, and tells the executor to re-locate by the METHOD name if the class moves again. Added F-10. |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Executability (right-sizing and conceptual density) | plan E-03 as authored; `aw ipd lint --phase author` reporting `IPD-Z602` on E-03 ("3 clauses") and E-04 | **E-03 BUNDLED BOTH PROBE HALVES plus both wire schemas, the palette requirement, the negative control and the cost-avoidance guidance into one item.** The two halves are independently executable and independently verifiable, and they have DIFFERENT risk profiles: the renderer half is in-process and side-effect free, while the argv half touches subprocess-spawning machinery and carries the entire cost question (F-07's measured 23-25 ms and `qul11h` PR-302's `bwrap`/journal inventory). Rubric diagnostics (a), (b) and (c) all answer YES, and the deterministic check flagged it independently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-03 (renderer half) and E-04 (argv half + assembly) with V-03/V-04 each demanding one half's evidence; downstream items renumbered to E-05..E-09 and V-05..V-09, `- Highest E allocated:` raised to `09`, and every cross-reference swept (F-04's `E-04(c)`/`V-04` and the approver paragraph's `V-04(c)`). Added F-11. |
| PR-004 | MEDIUM | IN-SCOPE | C. Architecture / F. KISS (the cheapest route left to be rediscovered) | plan E-03 as authored ("reusing/refactoring the existing capture"); `_probe_session_resume`'s local `fake_popen` assigning `captured["argv"] = cmd` | **THE PLAN ASKED FOR REUSE WITHOUT NAMING THE REUSABLE THING.** The argv half needs only that a flag pair appears in a built argv, and the sibling probe already captures the FULL argv for both hosts at its `Popen` seam. Left unnamed, an executor on a hot path (F-06: `detect_host_capabilities` now runs per-dispatch) is as likely to add a second full-turn drive, doubling a measured 23-25 ms plus a `bwrap` attempt and journal writes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 names the specific confined route (extract that capture into a helper both probes call); V-04 pins the review-measured 26/32 ms baseline so a doubling is visible rather than assumed. Added F-12. |
| PR-005 | MEDIUM | UNDER-SCOPE | G. Executability (execution contract: lifecycle ownership and scope route) | plan gate as authored | **THE GATE NAMED NO LIFECYCLE OWNER AND NO SCOPE-RECONCILIATION ROUTE.** POST-GATE LIFECYCLE said only that the plan "moves to `.aw/records/plans/executed/`" with no statement of WHO performs the transition; under `aw oc run` / `aw agy run` the runner owns finalize and an executor that also runs it duplicates it. The fence correctly declares three paths and correctly does not instruct a stop over scope, but never states the `--scope-reason`/`--scope-ack` route, so an executor meeting a necessary out-of-scope edit has no stated path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | POST-GATE LIFECYCLE now states the unconditional obligation with conditional ownership, names `aw ipd begin`, and forbids a hand-rolled `git mv`. The justify-route sentence is added and explicitly distinguished from the plan's two legitimate STOP conditions (a changed requirement map; a spec sentence naming this field's derivation). |
| PR-006 | LOW | UNDER-SCOPE | G. Executability (execution contract: honesty rule) | plan gate as authored | The gate required pasted output per `V-*` item but never stated the hard-MUST honesty rule as such, nor the bare-suite instruction, even though E-09 depends on both and the repository contract forbids `-n0` / a second `-q` / `-p no:randomly`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The honesty MUST and the bare-suite rule added to the EXECUTION CONTRACT paragraph, with the forbidden flags named. |
| PR-007 | LOW | IN-SCOPE | E. Testing (a case that could be satisfied the wrong way) | plan E-02 case (3) as authored | E-02's third-host case could be read as provable by a render result, which after PR-001 is the very confusion that breaks the probe. The third host is False because no renderer is KNOWN for it, which is a table lookup, not a render outcome. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 case (3) now states the reason explicitly and forbids proving it through a junk-render assertion. |
| PR-008 | LOW | IN-SCOPE | E. Testing / D. Anti-regression (sweep set and trap left unpinned) | plan E-07/V-07 as authored; measured hit set | The sweep item told the executor to classify every `rg` hit but did not record the hit set, so an unanticipated hit could not be distinguished from an anticipated one - which is the exact judgement V-08 asks them to make. Separately, F-05's schema trap was measured but nothing pinned it, so a renderer change that starts accepting the guessable shape would be silent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-08 records the review-measured hit set field by field (module: default, identity assignment, barrier condition, `missing` entry; tests: `CONTRACT_FIELDS`, three direct-construction descriptors, one `assertFalse`). Required tests gains a case pinning the `tool_call`/`tool_name` shape still rendering `None`, and a case proving the two-halves rule by forcing one half to fail. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What is the probe's negative control, given that an unparseable line renders a fallback line rather than `None` (PR-001)? | A WELL-FORMED NON-TOOL event (which returns `None` from both renderers), with the positive case asserting the rendered line CONTAINS the tool name. | (a) Assert the junk line is falsy as authored; rejected because MEASURED FALSE for both hosts. (b) Assert only that the tool event renders non-empty; rejected because the junk fallback is also non-empty, so it would pass for a host with no schema awareness at all - the fail-open failure the module's docstring exists to prevent. (c) Use the empty string as the control; rejected because although it does return `None` from both, returning `None` for no input is not evidence of parsing. | Measured at review HEAD `d449f3d2` against both real renderers: junk -> `'  not json at all'` / `'not json at all'`; well-formed non-tool -> `None` / `None`; tool -> `'❯ bash:  pytest -q'` / `'❯ bash:  {"command": "pytest -q"}'`, both containing `bash`; `""` and `"   "` -> `None` / `None`. Merits: the capability is SCHEMA AWARENESS, and a passthrough would echo a well-formed unknown event just as it echoes junk, so `None` on a well-formed non-tool event is precisely what separates a parser from a passthrough. Recorded in the plan as OQ-03. | yes |
| D-2 | E-03 bundled both probe halves and the deterministic check flagged it (PR-003). Split, or dismiss the advisory? | Split into E-03 (renderer half) and E-04 (argv half + assembly). | Dismissing the advisory as a count heuristic; rejected because the two halves differ in RISK as well as size (in-process and free versus subprocess-spawning on a per-dispatch hot path), so one V-item covering both cannot check either properly. | `/plan-review` rubric G right-sizing; `IPD-Z602` fired independently on E-03 with "3 clauses"; after the split only the E-05 wiring advisory remains, and that one is dismissed on merits because its (a)/(b)/(c) clauses are one indivisible edit (deleting the branch without wiring the probe leaves the field permanently False). | yes |
| D-3 | Does the off-platform `False` -> `True` change for `opencode` on `darwin`/`win32` need re-litigating here? | No. Accept it as intended and keep the plan's disclosure-and-pin treatment. | Keeping the verdict inside the platform gate for parity; rejected on the same basis the maintainer already accepted for the sibling field in `qul11h` D-3, and because parsing a JSON line is genuinely platform-independent while the sandbox rungs are not. | `qul11h`'s review record D-3 ("ACCEPT IT as intended, and require it be DISCLOSED and pinned with a before/after") for the identical situation on `supports_session_resume`; measured at review that this field behaves identically today (`darwin`/`win32` False, `linux` True). This plan already discloses it in the approver paragraph and pins it in V-05(c). | yes |

### Verdict and readiness

Verdict: `APPROVE WITH REVISIONS APPLIED`. Readiness: `GO - PENDING HUMAN APPROVAL`
(`- Readiness: go-pending-approval`). All eight findings are FIXED in place; nothing is DEFERRED or left
OPEN, so no finding needed escalation as a `- Blocking: yes` question. All three open questions are
`resolved`, none blocking. `aw ipd lint --phase review-finalize --agent` reports `conforming` with one
`IPD-Z602` INFO advisory on E-05, examined and dismissed on merits above.

NOTE FOR THE APPROVER, since this plan carries `- Blocks-Release: next`: the release gate is correctly
inherited from backlog `42da1n` (`- Work-Kind: bug`, `- Blocks-Release: next`, `- From-Backlog: 42da1n`
all present), so this plan is the item's provable carrier and the item stays `graduated` until this plan
executes. What ships is a corrected REPORT and the removal of an anti-pattern, not a new protection; the
plan says so plainly in its own gate and Scope check, and that honesty is preserved unchanged.
