# Review: cross-host resource telemetry schema, collector, and sampling (child lhccjf, Set runanalytics)

- Subject-Id: lhccjf
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `05422cd9`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic
review (exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the revisions including
the eight-item split and the rewritten V-item bijection.

METHOD. This child proposes to read the machine and write what it reads, so the first question was not
"is the schema good" but "do the authorities this plan leans on actually behave as it assumes". Three of
them do not, and each was established by CALLING the code rather than reading it: the user config's
key-dropping behavior, the leak detector's hostname tier, and the JSONL writer's per-event fsync.

WHAT THE PLAN GETS RIGHT, and it is a genuinely strong privacy posture. The instinct to record a keyed
pseudonym and persist neither the raw hostname nor the derivation input is correct. Prohibiting arbitrary
environment capture, and explicitly refusing to let environment values become a fallback for host
identity, closes a real hole most such plans leave open. Requiring probe parsers to persist only
numeric/categorical fields and never raw stdout is exactly right. So is refusing to guess a model price
and deferring it to Order 06, and so is the closing instruction not to market the telemetry as anonymous.
Per-invocation rather than per-installation capture is the correct call for a cluster, and the reasoning
given (hardware varies by node and by resumed attempt) is the right reason.

THE TWO FINDINGS THAT WOULD HAVE PRODUCED WRONG CODE ARE BOTH MISPLACED TRUST IN A SHIPPED AUTHORITY.

FIRST, THE CONFIG HOME. "Integrate with those authorities rather than create an unrelated config home" is
good instinct pointed at the wrong module. Measured, `config.py` enforces a fixed `_ALLOWED_TOP_KEYS`
(`:57-65`) and `normalize()` REBUILDS its output from `default_config()`, so an unregistered top-level key
does not survive a save. This is not obscure: the package already hit it and solved it. The
`review_findings_gate` block (`config.py:1082-1145`) states in its own comment that it is recorded in the
committed `.aw/config/project.json` and read there "and not via the XDG user config (which drops unknown
keys)", that it is DELIBERATELY absent from `CONFIG_SCHEMA`, and that it round-trips because
`project_schema.parse_portable_policy` preserves unknown keys in `unknown_fields` and re-serializes them.
An executor following the authored convention would have registered a key that silently vanishes, and the
bug would surface as "my telemetry setting keeps reverting". Fixed by naming the precedent, and OQ-01 now
splits the setting by nature: interval and enable/disable are project policy (committed, reviewable),
while a per-machine opt-out belongs in the gitignored `local.json` whose `runtime_overrides` map already
exists. One divergence from the precedent is stated deliberately: that key is fail-CLOSED because it is a
safety gate, whereas an absent telemetry key must mean the documented default, since failing closed on a
missing telemetry setting would break runs to protect nothing.

SECOND, AND MORE IMPORTANT BECAUSE IT IS THE PLAN'S CENTRAL CLAIM: THE SHIPPED LEAK DETECTOR DOES NOT FAIL
ON A HOSTNAME. Measured by calling `leak_sanitizer.scan_text` on this machine's hostname: ZERO findings at
default settings. The hostname IS derived as a token (`:416`, with FQDN and short label at `:419-424`),
but `_HOSTNAME_REASONS` (`:438`) lands in the `warn` tier and is promoted to `fail` only when the allowlist
sets `hostname_fail = true`, which ships FALSE with a stated reason ("so a shared CI-runner hostname does
not fail every build", `.aw/config/local-leaks-allowlist.toml:35`). Even passing `include_warn=True` to
BOTH `build_ruleset` and `scan_text` yields only a `warn`. The trap is that the detector looks competent
here: a username returns `handle` at `fail` and a home path returns `home-path` plus `handle` at `fail`,
both immediately. So a privacy suite that scans telemetry with `aw sanitize` and sees clean would have
passed while the one field this child exists to suppress shipped in every record. E-04 now requires a
DIRECT assertion against `socket.gethostname()`, `getfqdn()` and the short label, states plainly that the
sanitizer is insufficient for this field and why, and V-04 keeps the sanitizer only as corroboration with
a mandatory control run. This is the same control-run reasoning sibling `bzz5e6` adopted, for the same
reason: a clean report and a detector that was not looking are otherwise indistinguishable.

THIRD, AN 860-LINE IMPLEMENTATION OF NEARLY THIS PROBE SET ALREADY SHIPS IN THIS REPOSITORY.
`.aw/system/workflows/benchmark/tools/bench_env.py` captures CPU model/cores/flags, RAM
total/free/available/cached, swap, load average, GPU, container/VM hints, Python version and the
filesystem the work runs on; it is stdlib-only and read-only by charter. It already solves the two hard
parts of E-02: `_run` (`:63`) bounds every informational command with `capture_output`, an explicit
`timeout` and `check=False`, returning `""` on ANY failure, and `_read` (`:79`) does the same for `/proc`
and `/sys`. It even has `scrub()` (`:652`) replacing hostname, user and paths with placeholders for
sharing, which is a first cousin of this child's whole purpose. Its docstring states the posture this plan
independently arrived at, including "NEVER fabricates a value it could not read". Not citing it is how a
second, weaker subprocess wrapper enters a package. OQ-02 now requires the decision be recorded and notes
that a direct runtime import is the WORST of the options, since that path is installed workflow content
the installer manages rather than an importable package module.

FOURTH, "lifecycle shutdown" INVITED A SECOND CLEANUP ROUTINE THAT A SPEC PROHIBITS. `runner_shutdown.py`
is the ONE cleanup implementation, required by spec `c4gd2h` R5 ("Divergent per-level cleanup is
prohibited") with A9 demanding a structural check that exactly one exists; the spec reads
`- Status: implementing`, so it is live. The precedent is sharper than the rule: `oc_runipd.py:1587-1610`
records a previous plan being explicitly REFUSED permission to install `signal.signal` handlers, because
`runstop` Phase 5 (`71vjbn`) owns SIGINT/SIGTERM registration and the two designs were incompatible rather
than merely double-registered. A telemetry sampler that installs its own handler to flush on exit is the
most natural thing in the world to write and would have collided with that. The fence now forbids editing
`runner_shutdown.py`, registering a handler, or calling `clean_shutdown`, and points at Order 04
(`5f2h8i`), which is the plan that actually declares that file.

ON SIZING, WHICH THE LINT CANNOT SEE. Three E-items, and E-02-as-authored named five deliverables
(identity, snapshots, sampling, shutdown, failure isolation) across unrelated test surfaces. Every one of
the Set's ten children carries exactly three items, which is an authoring template rather than a
per-child judgement, and `aw ipd lint --phase author` reported conforming both before and after the split
into eight, so a passing lint cleared nothing here. Sibling `bzz5e6` found and split the identical pattern.
The accelerator probe in particular earned its own item: it is the only probe that shells out to a vendor
tool, and therefore the only one that can hang, flood, or leak a serial number through a parse error.

THE SMALLEST FINDING WITH THE LARGEST TEETH IS THE FSYNC. `runner_shared.append_jsonl` (`:458`) calls
`os.fsync` on EVERY event. That is right for a handful of run events and is a genuine per-sample cost for
a periodic sampler, so a plan promising "bounded overhead" had to name the writer whose cost dominates or
its budget would have been measured against an imagined buffered append. E-05 and E-08 now say so, and
E-05 forbids the tempting fix of quietly adding a second unsynced writer.

WHY APPROVE WITH REVISIONS RATHER THAN OPEN QUESTIONS. Nothing here needed a human: both unmade decisions
were answerable from shipped code and precedent and are recorded as D-1 and D-2, the sizing fix follows
the plan's own right-sizing rule, and the four authority corrections are settled repository facts measured
by execution. No BLOCKER or unfixed HIGH remains. What a human should still notice is F-2 as a FRAMEWORK
observation beyond this child: the leak sanitizer not failing on a hostname by default is a deliberate,
documented trade for CI, and it means every plan in this Set that treats `aw sanitize` as the privacy
oracle needs the same direct assertion. That is worth raising with the maintainer rather than fixing here.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-043 | HIGH | IN-SCOPE | A. correctness; C. architecture; G. executability | `config.py:57-65` (`_ALLOWED_TOP_KEYS`, `normalize()` rebuilding from `default_config()`); `config.py:1082-1145` (`review_findings_gate` comment); `project_schema.py:585`, `:624` (`unknown_fields`) | **THE CONFIG CONVENTION POINTED AT AN AUTHORITY THAT SILENTLY DISCARDS THIS SETTING.** "Integrate with those authorities" reads naturally as `config.py`, which enforces a fixed top-key allowlist and rebuilds its output on save, so an unregistered telemetry key does not round-trip. The package already hit and solved this: `review_findings_gate` is recorded in the committed `.aw/config/project.json`, read by a bespoke never-raising reader, and deliberately absent from `CONFIG_SCHEMA`, precisely because the XDG config "drops unknown keys". An executor would have shipped a setting that reverts | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | Conventions bullet rewritten naming the precedent and the mechanism; E-07 requires that reader shape and records the deliberate fail-open divergence (a safety gate fails closed; a missing telemetry key must mean the default); OQ-01 resolves project-versus-machine placement; V-07 requires the precedent cited and absent/malformed/unknown values landing on the default without raising. New F-1 |
| PR-044 | HIGH | UNDER-SCOPE | B. privacy; E. testing | `scan_text` on `gethostname()` -> **0 findings**; on a username -> `handle`/`fail`; on a home path -> `home-path`+`handle`/`fail`; `leak_sanitizer.py:416`, `:438`, `:485-491`; `.aw/config/local-leaks-allowlist.toml:35` (`hostname_fail = false`) | **THE SHIPPED LEAK DETECTOR DOES NOT FAIL ON A HOSTNAME, THE EXACT FIELD THIS CHILD EXISTS TO SUPPRESS.** The hostname is derived as a token but sits in the `warn` tier, promoted to `fail` only by an allowlist toggle that ships FALSE; even `include_warn=True` on both `build_ruleset` and `scan_text` yields only `warn`. Because a username and a home path DO fail immediately, the detector looks competent, so a privacy suite scanning telemetry with `aw sanitize` would report clean while the raw hostname shipped in every record | C:Low; U:Low; S:High; F:Medium; Overall:Medium | FIXED | E-04 now requires a DIRECT absence assertion against `socket.gethostname()`, `getfqdn()` and the short label, with the measurement and the reason inline; V-04 demands that assertion plus a sanitizer CONTROL run and an explicit statement that the sanitizer does not fail on a hostname at default settings; the required-tests and spec-sync sections both record that "our sanitizer reports clean" is not a privacy claim. New F-2 |
| PR-045 | HIGH | UNDER-SCOPE | C. architecture (no re-fork); F. KISS | `.aw/system/workflows/benchmark/tools/bench_env.py`, 860 lines (`_run:63` timeout-bounded and failure-swallowing, `_read:79`, `scrub:652`); its docstring | **AN 860-LINE, READ-ONLY, STDLIB-ONLY IMPLEMENTATION OF NEARLY THIS PROBE SET ALREADY SHIPS HERE AND THE PLAN NEVER MENTIONED IT.** It covers CPU, RAM breakdown, swap, load, GPU, container/VM hints and filesystem, already bounds every command probe with a timeout, already degrades to empty rather than raising, and already has a scrub-for-sharing routine. Writing fresh probes without deciding about it is how a second, weaker subprocess wrapper enters the package | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | A conventions bullet names the file and its three relevant helpers; E-02 requires reading it FIRST and recording one of import/extract/copy/fresh with a reason; OQ-02 resolves the direction (do not ignore it) and notes a direct runtime import is the worst option since that tree is installed workflow content, not a package module; V-02 requires the recorded decision. New F-3 |
| PR-046 | HIGH | IN-SCOPE | C. architecture; D. anti-regression | spec `c4gd2h` R5/A9, `- Status: implementing`; `runner_shutdown.py:1-31` and `clean_shutdown:451` (7 call sites); `oc_runipd.py:1587-1610`; Order 04 `Scope-Paths` | **"LIFECYCLE SHUTDOWN" INVITED A SECOND CLEANUP PATH THAT A LIVE SPEC PROHIBITS.** R5 forbids divergent per-level cleanup and A9 requires a structural check that exactly one implementation exists. Sharper still, `oc_runipd.py:1587-1610` records a prior plan being explicitly refused permission to register `signal.signal` handlers because `runstop` Phase 5 owns SIGINT/SIGTERM and the designs were incompatible. A sampler installing its own flush-on-exit handler is the natural implementation and would have collided | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | A conventions bullet states R5/A9 and the recorded refusal; E-06 requires a callable stop API ONLY and forbids a handler, a cleanup path or a `clean_shutdown` call, naming Order 04 as the owner that declares the file; the scope fence repeats all three prohibitions and V-06 requires a grep proving none was added. New F-4 |
| PR-047 | MEDIUM | UNDER-SCOPE | C. architecture; F. KISS | `oc_runipd.StallWatchdog:655-714`; `lane_containment.TurnBoundWatch:1276-1348` | The bounded background-sampler pattern exists TWICE already (Event stop flag, `daemon=True` thread started in `__enter__`, `_stop.wait(interval)` rather than `sleep`, `__exit__` setting the event then `join(timeout=1.0)`, interval clamped against the bound). The plan stated the requirement ("samples stop on every cleanup path") without pointing at either, so a third shape would likely have been invented, and a telemetry thread that outlives its run or blocks shutdown is a real hazard | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | A conventions bullet names both classes and enumerates the five shared structural properties; E-06 requires copying that shape; V-06 requires thread-liveness pasted after normal exit, exception and signal teardown. New F-5 |
| PR-048 | MEDIUM | IN-SCOPE | C. operability (overhead); E. testing | `runner_shared.append_jsonl:458` (calls `os.fsync` per event); `atomic_write_json:436` | **THE OVERHEAD BUDGET HAD NO NAMED WRITER, AND THE REAL ONE FSYNCS EVERY EVENT.** That is correct for low-volume run events and a genuine per-sample cost for a periodic sampler, so "prove bounded overhead" would plausibly have been measured against an assumed buffered append, understating the true cost | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | A conventions bullet records the fsync property; E-05 mandates the existing writer, states the cost, and forbids quietly adding a second unsynced writer (a finding must be recorded instead); E-08 and V-05/V-08 require the measured per-event and per-sample figures against the real writer. New F-6 |
| PR-049 | MEDIUM | UNDER-SCOPE | G. right-sizing and conceptual density | `grep -c '^- \[ \] E-'` over all ten `runanalytics` children -> `3` each; `aw ipd lint --phase author` conforming BOTH before and after the split | **THE THREE E-ITEMS WERE MECHANICALLY SIZED, NOT SIZED TO ONE CONCERN.** E-02-as-authored named five deliverables (identity, snapshots, sampling, shutdown, failure isolation) across unrelated test surfaces; E-03 bundled the config model with an eight-case degradation matrix. Every one of the Set's ten children carries exactly three items, which is a template, not a judgement. The count-based lint is structurally unable to see this. Sibling `bzz5e6` had the identical finding | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into EIGHT items across four groups: E-01 envelope, E-02 probes, E-03 the accelerator probe alone (the only vendor-tool shell-out, hence the only hang/flood/leak risk), E-04 identity, E-05 collector lifecycle, E-06 sampler, E-07 config, E-08 proof. `Highest E allocated` 03 -> 08; V-01..V-08 rewritten to bijection; a right-sizing note records the measurement. New F-7 |
| PR-050 | MEDIUM | UNDER-SCOPE | G. executability | plan gate as authored (two sentences); sibling review records for `xbwq8n` and `bzz5e6` naming the identical omission | **THE GATE CARRIED NO EXECUTION CONTRACT**: no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle-move instruction, no dependency posture. Third sibling in a row with the same gap, so it is a Set-wide authoring pattern | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Full contract added: approval requirement plus the `executed:bzz5e6` dependency and the three plans depending on this one (making E-01's envelope a contract, not an internal detail); a scope fence naming six measured prohibitions with the finalize `--scope-reason`/`--scope-ack` mechanics; path-scoped commit, re-verify-after-failed-hook, shared-checkout warning; the hard honesty rule with the bare-pytest instruction; re-locate-by-symbol; and two explicit stop conditions. New F-8 |
| PR-051 | LOW | IN-SCOPE | Presentation | `grep -n '\\`'` -> 10 occurrences at lines 29, 57, 86 before the fix; Order 01's review found six, Order 02's four | Ten escaped backtick pairs rendered as literal backslashes instead of code spans, in an E-item, the Findings table and the validation section. Same defect and same shared authoring pipeline as both reviewed siblings | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All ten unescaped and verified zero remaining |
| PR-052 | LOW | IN-SCOPE | E. testing; evidence accuracy | bare `python3 -m pytest` at `05422cd9` -> `2 failed, 5655 passed, 3 skipped, 2 xfailed`; both node ids | The plan required a bare suite run and `git diff --check` but recorded NO baseline, so an executor meeting two pre-existing failures could not distinguish them from its own. Both are pinned to the live mutable plan corpus | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline recorded in the required-tests section and F-10 with both node ids named and attributed as pre-existing, plus the compare-node-ids-not-totals rule, the empty-delta criterion, and an instruction to re-measure in the executing worktree rather than trust the recorded numbers |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Where does the telemetry configuration live, given the plan said only "existing config authorities"? | SPLIT: interval and enable/disable in the committed `.aw/config/project.json` following the `review_findings_gate` precedent; a per-machine opt-out in the gitignored `local.json` `runtime_overrides`; local overrides project; the reader never raises | The XDG user config (`config.py`), rejected on measurement: `_ALLOWED_TOP_KEYS` plus `normalize()` rebuilding from `default_config()` means an unregistered key is silently dropped on save, so the setting would appear to revert. Registering it in `CONFIG_SCHEMA`, rejected because the `review_findings_gate` precedent is deliberately absent from that schema and adding one would invite the next author to add another. Everything in `local.json`, rejected because an interval and an enable flag are team-reviewable policy, not machine facts. Leaving it unspecified, rejected because an executor would then pick the module the convention named, which is the broken one | `config.py:57-65`; `config.py:1082-1145` and its comment; `project_schema.py:585`/`:624` `unknown_fields` round-trip; `.aw/config/local.json` carrying `runtime_overrides`; `project.json` being committed and `local.json` gitignored | yes |
| D-2 | Is `bench_env.py` reused, and how? | DO NOT IGNORE IT: record one of extract-into-package, copy-with-attribution, or write-fresh-with-a-reason. Direct runtime import named as the worst option | Silently writing fresh probes, rejected because it produces a second, weaker bounded-subprocess wrapper in a repository that repeatedly pays for exactly that. Mandating extraction, rejected because that file is installed workflow content under `.aw/system/`, so lifting it into the shipped package is a real packaging decision this child should not be forced into. Importing it at runtime from `agent_workflows/`, rejected because it would couple the package to a path the installer manages and copies into targets | `bench_env.py` read (`_run:63`, `_read:79`, `scrub:652`, docstring); its location under `.aw/system/workflows/benchmark/tools/`; the installer's ownership of that tree | yes |
| D-3 | Is `aw sanitize` sufficient to prove the hostname is not persisted? | NO. Require a DIRECT absence assertion against `gethostname()`/`getfqdn()`/short label; keep the sanitizer as corroboration WITH a control run | Rely on `aw sanitize` alone, rejected on measurement: it returns ZERO findings for this machine's hostname at default settings, because the derived hostname token is `warn`-tier and `hostname_fail` ships false; the test would have passed while the field shipped. Promote `hostname_fail` to true in this repo's allowlist, rejected because that is a framework-wide policy change with a documented CI rationale, is outside this child's fence, and would still leave every ADOPTER's default unchanged. Drop the sanitizer entirely, rejected because it does catch usernames and home paths at `fail` and is a genuine independent oracle for those | `scan_text` results measured for hostname (0), username (`handle`/`fail`), home path (`home-path`+`handle`/`fail`); `leak_sanitizer.py:416`/`:438`/`:485-491`; `local-leaks-allowlist.toml:35` and its stated reason | yes |
| D-4 | Split the three E-items, or accept them since the lint passes? | SPLIT into eight, and record that the count-based lint cannot clear conceptual density | Accept the authored three, rejected because E-02 named five deliverables across unrelated test surfaces and the controlling workflow states explicitly that a passing count-based size lint does NOT clear right-sizing. Split into separate child PLANS, rejected because the cohesion argument is real: every persisted field must cross ONE privacy boundary, so schema, probes and collector belong in one plan. Keep the accelerator probe inside E-02, rejected because it is the only vendor-tool shell-out and therefore the only probe that can hang, flood, or leak through a parse error | all ten children measured at exactly 3 E-items; lint conforming before and after; plan-review's right-sizing diagnostics answering YES for E-02 | yes |
| D-5 | May this child touch the shutdown path it needs to cooperate with? | NO. Expose a callable stop API only; forbid editing `runner_shutdown.py`, registering a signal handler, and calling `clean_shutdown` | Register a flush-on-exit handler, rejected because `runstop` Phase 5 (`71vjbn`) owns SIGINT/SIGTERM and `oc_runipd.py:1587-1610` records a prior plan being refused exactly this, with the designs noted as incompatible rather than merely duplicated. Call `clean_shutdown` from the collector, rejected because spec `c4gd2h` R5 prohibits divergent cleanup and A9 requires a structural check that exactly one implementation exists. Leave it to the executor, rejected because installing a handler is the obvious implementation and the collision would surface as a lost signal, not a test failure | spec `c4gd2h` R5/A9, `- Status: implementing`; `oc_runipd.py:1587-1610`; Order 04 `5f2h8i` declaring `runner_shutdown.py` in its `Scope-Paths` | yes |
