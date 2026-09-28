# IPD: Refuse an unsafe --summary at backlog creation instead of writing an item the checker immediately flags

- Date: 2026-09-28
- Kind: child
- Concern: `backlog.run_new` checks only that `--summary` is NON-EMPTY, never that it satisfies the Section 8.8 descriptive-field contract its own `backlog.validate_item` enforces, so the verb exits 0 writing an item that `aw backlog check` then exits 1 on (`backlog.summary-unsafe`); worse, an embedded NEWLINE is not merely unsafe but INJECTS arbitrary front matter (a smuggled `- Blocks-Release: next` parses as the item's real gate) and is invisible to the checker.
- Scope: Apply the existing shared `attention_contract.is_safe_descriptive` predicate to the descriptive values `aw backlog new` and `aw backlog set` write into front matter (`--summary`, `--gate-ref`, and the `--message` history record), refusing with exit 2 BEFORE any file is written, through the refusal shape those verbs already use for `--priority`/`--work-kind`/`--graduated-to`. No new field, no new rule id, no change to `is_safe_descriptive`, no change to the checker.
- Scope-Paths: agent_workflows/backlog.py, tests/test_backlog_descriptive_safety.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: a0s33b
- Blocks-Release: next
- Set: a0s33b
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: dtg7dz

## Workflow history

- 2026-09-28 draft (opencode): created.
- 2026-09-28 to-review (opencode): authored from backlog `a0s33b`; reproduced the item's reported over-length case exactly as filed, then measured three FURTHER vectors the item does not name (newline front-matter injection, the same hole on `--gate-ref`, and the same hole on the `--message` history record) and scoped the fix to the descriptive values these verbs write rather than to `--summary` alone.

## Goal

Make `aw backlog new` (and the `--gate-ref`/`--message` values `aw backlog set` writes) refuse a descriptive value that its own checker rejects, so a creating verb cannot manufacture a nonconforming item. Today the create/check pair CONTRADICT each other on the same bytes: creation exits 0 and the checker exits 1 on the artifact creation just produced. A newline in the same field is strictly worse than the item reports, because it writes attacker-or-accident-chosen front matter that the checker reports as CLEAN.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared refusal helper, applied at the creating verb

- [ ] E-01 Add a module-private helper to `agent_workflows/backlog.py` that judges ONE descriptive value against the shared predicate and returns the refusal message, so every call site refuses with identical wording rather than each spelling its own. Signature shape: `_refuse_unsafe_descriptive(verb: str, flag: str, value: Optional[str]) -> Optional[str]`, returning `None` when `value` is `None` or `A.is_safe_descriptive(value)` is True, else a message naming the verb, the flag, WHICH bound was violated (over `A.MAX_DESCRIPTIVE_LEN`, embedded newline, or control character) and the actual length when that is the cause. Do NOT reimplement the predicate's conditions: call `A.is_safe_descriptive` for the VERDICT and inspect the value only to pick the explanatory clause, so the verdict has exactly one owner.
  - Depends on: none
  - Expected outcome: a helper importable as `backlog._refuse_unsafe_descriptive` that returns `None` for `"ok"` and for `None`, and a message mentioning `newline` for `"a\nb"`, `control` for `"a\x07b"`, and both `300` and `340` for a 340-character value.
  - Execution state: pending

- [ ] E-02 Apply the helper to `--summary` in `backlog.run_new`, immediately after the existing empty-summary guard (`aw backlog new: --summary is required`) and BEFORE the `--blocks-release` resolution and the `decide_gate_default` call, so the refusal costs no release lookup and no id6 is consumed by a doomed call. Write the message to `sys.stderr` and `return 2`, matching the exit-2 cannot-run convention the sibling guards in the same function already use (`--priority must be one of`, `--work-kind must be one of`, `a blocked item requires --gate-kind and --gate-ref`) and which `command_surface` declares for this command as `(0, 1, 2)`. Do NOT touch `--agent`/`--json` envelope construction: those branches are reached later in the function, and every existing usage refusal in `run_new` is a plain stderr write, so the new refusal is consistent with them by doing the same.
  - Depends on: E-01
  - Expected outcome: `aw backlog new --summary <340 chars>` exits 2, prints the refusal on stderr, and writes NO file, where before it exited 0 and wrote an item that `aw backlog check` exits 1 on.
  - Execution state: pending

- [ ] E-03 Apply the helper to the two REMAINING descriptive values these verbs write into an item: `--gate-ref` and `--message`, at both `backlog.run_new` and `backlog.run_set`. Place each guard before the corresponding write, keeping `run_set`'s existing byte-identical-on-refusal property (a refused transition must leave the file untouched, which holding the guard before `core.atomic_write` preserves). For `--gate-ref` the new guard is ADDITIVE to the existing `A.validate_gate_ref` kind-specific check, not a replacement: that check is consulted by `validate_item` but only AFTER `Gate-Kind` validity, so a valid kind with a newline-bearing ref reaches disk today. For `--message`, judge the value the history record embeds, since a newline there injects a forged `## Workflow history` record.
  - Depends on: E-02
  - Expected outcome: `aw backlog new --status blocked --gate-kind todo --gate-ref $'TODO.md\n- Blocks-Release: next'` exits 2 and writes nothing, where before it exited 0 and produced an item whose parsed `blocks_release` was `next` with ZERO checker drift. `aw backlog set <id> --message $'note\n- Blocks-Release: next'` likewise exits 2 leaving the item byte-identical.
  - Execution state: pending

### Task group 2: pin the contradiction, the injection, and the non-regressions

- [ ] E-04 Add `tests/test_backlog_descriptive_safety.py` pinning the CREATE/CHECK CONTRADICTION as the primary property, for each of the four unsafe shapes `is_safe_descriptive` rejects (over-length, `\n`, `\r`, C0/C1 control incl. ANSI ESC): for each, assert `run_new` returns 2, that NO `*.backlog.md` file exists afterwards, and that the refusal message names the flag. Then assert the CONVERSE on a conforming value: `run_new` returns 0, the item is written, and `backlog.validate_item` on it returns zero drift. The test that matters is the PAIRED one: no input may exist for which creation succeeds and `validate_item` reports `backlog.summary-unsafe`, which is the exact contradiction backlog `a0s33b` filed. Follow the established template `test_new_blocks_release_unresolvable_fails_closed` in `tests/test_backlog.py`, which asserts both `rc == 2` and that no file was written.
  - Depends on: E-03
  - Expected outcome: a new module whose unsafe cases FAIL on pre-E-02 code (creation returns 0 and writes a file) and PASS after, and whose conforming case passes both before and after.
  - Execution state: pending

- [ ] E-05 In the same module, pin the INJECTION property and the three non-regressions. Injection: a `--summary`, `--gate-ref`, and `--message` each carrying a newline followed by `- Blocks-Release: next` must be REFUSED, and the test must additionally assert that the pre-fix artifact's parsed `blocks_release` WOULD have been `next` with zero drift, so the record states plainly that the checker could not see this and the write path is the only place it can be stopped. Non-regressions: (a) the existing empty-`--summary` refusal still returns 2 with its unchanged message; (b) a value at EXACTLY `A.MAX_DESCRIPTIVE_LEN` is ACCEPTED and one at `+1` refused, pinning the boundary on the predicate's `>` rather than on a copied constant; (c) `--agent` mode still returns 2 on a refusal without emitting a malformed envelope, mirroring the existing `--agent` envelope expectation in `tests/test_backlog_duplicate_guard.py`.
  - Depends on: E-04
  - Expected outcome: the injection tests pass and the three non-regression tests pass, with the boundary test proving 300 accepted and 301 refused.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PREDICATE IS THE SINGLE AUTHORITY AND IS ALREADY SHARED, so this plan adds CALL SITES and changes no condition. `attention_contract.is_safe_descriptive` documents itself as "Section 8.8: a descriptive field is a single, bounded, control-char-free line" and is already consumed from `backlog.validate_item`, three sites in `specs`, and `check_engine.resolve_evidence_artifact`. The defect is that the CREATING verb does not consult what the CHECKING verb does.
- THE REFUSAL SHAPE IS SETTLED IN THIS EXACT FUNCTION: every usage refusal in `backlog.run_new` writes `aw backlog new: <what>` to `sys.stderr` and returns 2, with no exception and no envelope (the `--priority`/`--work-kind` enum guards, the `--summary is required` guard, the blocked-requires-gate guard, and the `--blocks-release ... does not resolve` guard). `cli.py`'s backlog family and `command_surface`'s `backlog new` declaration both fix the exit contract at `(0, 1, 2)`, so exit 2 is the correct cannot-run code and no new code needs inventing.
- A DIRECT PRECEDENT ALREADY APPLIES THIS PREDICATE AT A WRITE PATH IN A SIBLING TREE. `specs.run_set` refuses with `aw specs set: --gate-summary must be a bounded single control-char-free line` when `A.is_safe_descriptive(gs)` is False. So "validate the descriptive value at the verb that writes it" is an ESTABLISHED pattern here, not a new policy; `backlog` simply never adopted it.
- A SECOND PRECEDENT VALIDATES THE WHOLE RENDERED ITEM BEFORE WRITING IT. `set_records` calls `backlog.validate_item` on the rendered text and raises `ValueError("promoted backlog item failed validation: ...")` if any drift appears, BEFORE `atomic_write`. That is a library path so it raises rather than exiting 2, but it establishes that a backlog write path is expected to be checker-clean by construction.
- `aw backlog set --graduated-to` ALREADY REFUSES A NEWLINE-BEARING VALUE, which is why this plan treats refusal-at-the-verb as consistent rather than novel: driven in a temp fixture, `--graduated-to $'abc123\n- Blocks-Release: next'` exits 2 with "takes lowercase-kebab setids of at most 40 characters; malformed", and the item is left untouched. The adjacent descriptive fields simply lack the equivalent guard.
- THE ITEM'S OWN HISTORY RECORDS THE HAND-FIX AND THE REMAINING GAP, and this plan closes exactly the gap it names: "Fixed by hand in `diof9n` by shortening both summaries; the verb gap remains." It also names the intended mechanism ("The creating verb should apply `is_safe_descriptive` and fail closed"), which E-01/E-02 implement literally.
- THE SPEC TEXT FORBIDS THE OBVIOUS ALTERNATIVE FIX. Spec `attention-registry-and-cross-tree-status` Section 8.8: "Over-length values are a contract violation, not silently truncated", and "embedded newlines are rejected (a violation), not wrapped". So truncating or normalizing the summary at creation is ruled out by the governing spec, leaving refusal as the specified behavior. Its A14 acceptance criterion also already requires "hostile-string fixtures" for exactly these four shapes, which is the template E-04 follows.
- THE HISTORY-RECORD FIELD IS DESCRIPTIVE TOO, which is why E-03 covers `--message`. `_render_item` embeds the message in a `- <date> created (aw backlog): <message>` line inside `## Workflow history`, and `backlog.parse_item` stops scanning metadata at the first `## ` heading, so a newline in `--message` writes a second history record rather than metadata. That forges the record's own provenance, which is the artifact the workflow history exists to be trusted as.

## Findings

All findings below were driven in this lane at HEAD `a019e547` against temporary fixture repositories, not read off the source.

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE FILED DEFECT REPRODUCES EXACTLY AS WRITTEN. `run_new` with a 340-character `--summary` returns 0, writes the item, and `validate_item` on that very file returns `backlog.summary-unsafe`. | Driven: `rc = 0`, stderr empty, file `20260928-s-01-ccqw0t-overlong.backlog.md` written, `validate_item` drift `[('backlog.summary-unsafe', 'summary not a single bounded control-char-free line')]`. `A.MAX_DESCRIPTIVE_LEN` is 300. |
| F-02 | THE CONTRADICTION IS VISIBLE END-TO-END THROUGH THE REAL CLI, not only in-process, so it is a user-facing exit-code disagreement on identical bytes. | Driven as two subprocesses in a fresh `git init` fixture: `python3 -m agent_workflows backlog new ... --summary <340 chars>` exited **0** with empty stderr; `python3 -m agent_workflows backlog check --dir <repo> --agent` then exited **1** emitting `"outcome":"findings","findings":1` with `{"rule":"backlog.summary-unsafe"}`. |
| F-03 | A NEWLINE IS STRICTLY WORSE THAN OVER-LENGTH AND THE CHECKER CANNOT SEE IT: it injects real front matter. A `--summary` of `legit\n- Blocks-Release: next` produced an item whose `parse_item(...).blocks_release` is `'next'` with **zero** drift. | Driven: `rc=0`, written file contains `- Summary: legit` followed by `- Blocks-Release: next`; `parse_item` returned `blocks_release='next'`; `validate_item` returned `[]`. The gate was never requested and no release record exists. |
| F-04 | THE INJECTION IS INVISIBLE TO THE CHECKER BECAUSE THE VALUE IS SPLIT BEFORE VALIDATION. `parse_item` reads `- Summary: legit` (a safe, bounded, control-char-free line) and the smuggled bullet as SEPARATE lines, so `is_safe_descriptive` is handed only the safe half. | Driven: the same fixture's `parse_item` returned `summary='legit'` (not the injected string), which is precisely why `validate_item` reported `[]` in F-03. Newline injection therefore CANNOT be closed by strengthening the checker; only the write path sees the unsplit value. |
| F-05 | THE INJECTION REACHES MORE THAN THE GATE FIELD. A `--summary` carrying `\n- Status: done` wrote a second `- Status:` bullet into front matter; a `\n- Gate-Kind: plan\n- Gate-Ref: abc123` pair wrote both and was parsed back as a real gate. | Driven: the `- Status: done` case produced front matter with two `- Status:` lines and zero drift (`parse_item` keeps the FIRST occurrence, so `status` stayed `open` here, but the file now contains a contradictory bullet). The gate case parsed `gate_kind='plan'`, `gate_ref='abc123'` and drifted only `backlog.gate-unexpected`. |
| F-06 | `--gate-ref` HAS THE SAME HOLE ON BOTH VERBS, and it is fully silent for a VALID gate kind. `--gate-kind todo --gate-ref $'TODO.md\n- Blocks-Release: next'` wrote the smuggled gate with **zero** drift on `run_new`, and identically on `run_set`. | Driven twice: `run_new` `rc=0`, `parse_item(...).blocks_release == 'next'`, `validate_item` `[]`. `run_set(status='blocked', gate_ref=<same>)` `rc=0`, same parsed gate, `validate_item` `[]`. With an INVALID kind (`plan`) the only drift reported was `backlog.gate-kind-invalid`, i.e. the kind error masks the injection rather than catching it. |
| F-07 | `--message` HAS THE SAME HOLE ON BOTH VERBS, and it forges the WORKFLOW HISTORY. A `--message` of `note\n- Blocks-Release: next` on `run_set` wrote that bullet as a history line; on `run_new` a `\n- 2026-09-28 done (aw backlog): approved by the maintainer` wrote a forged history record. | Driven: `run_set` `rc=0`, resulting `## Workflow history` contains `- 2026-09-28 set (aw backlog): note` followed by `- Blocks-Release: next`, drift `[]`. `run_new` case produced a history containing a fabricated `done ... approved by the maintainer` record, drift `[]`. |
| F-08 | THE PREDICATE IS ALREADY CORRECT AND NEEDS NO CHANGE; it is simply not consulted. It rejects all four shapes: over-length, `\n`, `\r`, and any C0/C1 control including ANSI ESC. | Source of `A.is_safe_descriptive` read directly: returns True for `None`, False for `len > MAX_DESCRIPTIVE_LEN`, False on `\n`/`\r`, False on `_CONTROL_CHAR_RE` (`[\x00-\x1f\x7f-\x9f]`). Driven per shape via `validate_item`: BEL and ESC both produced `backlog.summary-unsafe`; `\n` and `\r` produced `[]` for the F-04 splitting reason. |
| F-09 | NO TEST ANYWHERE EXERCISES `backlog.summary-unsafe`, so neither the rule nor its absent creation-side guard is pinned. | `grep -rn "summary-unsafe" tests/` matches only `tests/test_doctor.py`, and that is a `check.summary-unsafe` fixture Drift for the doctor remediation table, not the backlog rule. The nearest sibling refusal tests are `test_new_requires_summary` and `test_new_blocks_release_unresolvable_fails_closed` in `tests/test_backlog.py`. |
| F-10 | THERE IS NO EXISTING POPULATION TO BACKFILL, so this plan is purely preventive and needs no migration step. | Driven over the whole tree: `validate_item` across every item `backlog._iter_items` yields (674 at this lane's HEAD, of which 673 match `*.backlog.md` and one is a legacy `...-token-test-bindings.md` the iterator still picks up) reported ZERO summary-rule findings, and `aw backlog check --agent` reported `"outcome":"clean","checked":674,"findings":0`. The two items that originally triggered the report were hand-fixed in `diof9n`, as the item's own history records. |
| F-11 | THE REFUSAL PATH IS ALREADY AGENT-SAFE, so E-02 needs no envelope work: the existing empty-summary refusal returns 2 on stderr even under `--agent`. | Driven with `agent=True`: `rc=2`, stdout empty, stderr `'aw backlog new: --summary is required\n'`. The new guard sits beside it and inherits that behavior. |
| F-12 | THE DEFECT CLASS IS NOT CONFINED TO THIS TREE: `aw specs new` and `aw releases new` have the identical unguarded hole, which is why the fix pattern matters more than the single flag. Both are carried by `qbz8i1`, filed while authoring this plan, and neither is fixed here. | Driven: `specs.run_new(summary="legit\n- Blocks-Release: next")` exited 0 and wrote a spec whose front matter carries a real `- Blocks-Release: next` bullet, after which `python3 -m agent_workflows specs check --agent` reported `"outcome":"clean","findings":0`. `releases.run_new` with the same value wrote the same smuggled bullet at `rc=0`. Specs is the WEAKER case: it has no summary rule at all, so the value is unbounded at both the write path and the checker. |
| F-13 | THE INJECTION DOES NOT CURRENTLY FORGE A SPEC APPROVAL, and this plan states that explicitly rather than overclaiming the severity. A `\n- Status: approved` injection writes a second `- Status:` bullet, but the reader keeps the FIRST. | Driven: the resulting spec contained `['- Status: draft', '- Status: approved', '- Status: approved']`, while `specs._read_status(lines)` returned `'draft'` and `specs._find_status_index(lines)` returned 3 (the legitimate bullet). So the measured harm is a record carrying contradictory metadata that every later reader and rewriter sees, not a bypassed approval gate. |

## Proposed changes (ordered, validatable)

1. E-01: add one module-private refusal helper in `backlog.py` that delegates the VERDICT to `A.is_safe_descriptive` and composes a message naming the flag and the violated bound.
2. E-02: call it on `--summary` in `run_new`, after the empty check and before any release lookup or write, refusing with stderr + exit 2.
3. E-03: call it on `--gate-ref` and `--message` at both `run_new` and `run_set`, before the write, preserving `run_set`'s byte-identical-on-refusal property.
4. E-04: pin the create/check contradiction as a paired property over all four unsafe shapes, plus the conforming converse, closing the total absence of coverage F-09 reports.
5. E-05: pin the newline INJECTION (the vector F-03/F-06/F-07 measured and F-04 proves the checker cannot see), the exact `MAX_DESCRIPTIVE_LEN` boundary, the preserved empty-summary refusal, and the `--agent` refusal shape.

## Deferred / out of scope (with reason)

- `aw specs new --summary` AND `aw releases new --summary` HAVE THE SAME UNGUARDED HOLE and are NOT fixed here. Both were driven while authoring this plan: each exits 0 writing a smuggled `- Blocks-Release: next` bullet into real front matter, and `aw specs check` reports `"outcome":"clean"` on the result. Specs is the weaker of the two because it has NO summary checker rule at all (`grep -n "summary-unsafe" agent_workflows/*.py` matches only `backlog.py` and `doctor.py`), so closing it needs a new rule id as well as a write-path guard, which is new policy in a different module and tree.
  - Carrier: qbz8i1
- EVERY OTHER TREE'S CREATING VERBS (`aw research new`, `aw prompts new`) are out of scope for the same reason. This plan fixes the tree the item names, using the pattern `specs.run_set` already established, and deliberately does not attempt a repo-wide sweep of descriptive-field write paths in one pass: each tree has its own rule set, its own checker coverage, and its own refusal conventions, so a sweep would be several unrelated behavior changes sharing one commit.
  - Carrier: qbz8i1
- HARDENING `parse_item` OR `_render_item` AGAINST INJECTION STRUCTURALLY (for example by quoting or escaping values on write, or by refusing to parse a metadata bullet that follows a continuation line) is out of scope and deliberately refused here. It would change the ON-DISK GRAMMAR of every backlog item and therefore what every existing reader parses, which is a spec-level change to the artifact format rather than a validation fix. Refusing the input at the verb closes the measured vector without touching the format.
  - Carrier-Declined: The obligation is DISCHARGED for the vector this plan measures rather than postponed. F-03 through F-07 all enter through a verb's flag value, and E-02/E-03 refuse every one of them before a write occurs, so no measured injection survives this plan. What structural hardening would additionally cover is a HAND-EDITED file, which is a whole-tree checker concern and not reachable from a write path at all; and for that residue the newline case is exactly the one F-04 proves a checker cannot see after the fact, so the carrier would name work with no available mechanism. Filing one would schedule a format change nothing measured here requires.
- THE `attention.stranded_lane_drift` OVER-LENGTH DETAIL is a separate, already-filed instance of "a descriptive field nothing checks", and is not touched here. It is a different producer (assembled output, not a user-supplied flag) and its fix is a contract decision about output rather than input validation.
  - Carrier: hv8zlg
- A SHARED CROSS-MODULE REFUSAL HELPER (one function in `attention_contract` that every tree's verbs call, instead of a `backlog.py`-private one) is out of scope. `specs.run_set` already spells its own refusal inline, so extracting a shared helper would mean editing specs' shipped message text as collateral, and there would be exactly two call-site families to share it. The helper is authored module-private in E-01 precisely so a later sweep can hoist it once a second tree genuinely needs it.
  - Carrier-Declined: Nothing is owed, because this is a deliberate factoring choice with no defect behind it and no current second consumer: `specs.run_set` is already guarded and needs no change, so hoisting today would refactor working code for a caller that does not exist. The helper's placement is trivially reversible when a real second consumer appears (the sweep row above carries that case), so recording a carrier would schedule a speculative refactor rather than outstanding work.

## Scope check

- Over-scope: none. One new module-private helper, three guard call sites across two functions in one module, and one new test module. `is_safe_descriptive`, `MAX_DESCRIPTIVE_LEN`, `validate_item`, the `backlog.summary-unsafe` rule id, the on-disk item grammar, `parse_item`, `_render_item`, and every `--agent`/`--json` envelope stay untouched.
- Under-scope: `aw specs new --summary` and `aw releases new --summary` stay unguarded and specs still has NO summary checker rule (both carried by `qbz8i1`); the other trees' creating verbs are untouched; and a HAND-AUTHORED item bypassing these verbs is unaffected, which for the over-length shape is caught by the shipped `backlog.summary-unsafe` rule but for the newline shape is caught by NOTHING, per F-04. This plan does not claim to close hand-authored injection.

## Required tests / validation

- `python3 -m pytest tests/test_backlog_descriptive_safety.py` for the new module (run bare; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`).
- `python3 -m pytest tests/test_backlog.py tests/test_backlog_duplicate_guard.py tests/test_backlog_production.py tests/test_backlog_handoff_close.py tests/test_attention_contract.py` as the targeted regression set: these own the two verbs being edited, the `--agent` envelope shape a refusal must not break, and the predicate itself.
- `python3 -m pytest` (full fast suite) to prove no order-dependent or cross-module regression.
- `aw backlog check --agent` must still report `"outcome":"clean"` with `"findings":0` on the repository tree, and `aw check backlog --agent` must still report `"outcome":"conforms"`, proving the change introduces no finding of its own on the existing item population (F-10).
- PRE-FIX FALSIFICATION IS REQUIRED, not optional: V-04 and V-05 must each show the new tests FAILING against the pre-E-02 code. A test that passes before the fix proves nothing, and for the injection cases the pre-fix run must show the smuggled field being PARSED as real with zero checker drift.

## Spec / documentation sync

N/A with reason. This plan makes existing code obey an ALREADY-WRITTEN contract; it changes no rule and adds no field, so no `.spec.md` is amended and no spec path appears in `- Scope-Paths:`. The governing text is spec `attention-registry-and-cross-tree-status` Section 8.8, which already states the required behavior for exactly these shapes ("embedded newlines are rejected (a violation), not wrapped"; "Over-length values are a contract violation, not silently truncated") and whose F10 already classes such violations as failures; its A14 already requires hostile-string fixtures of the four shapes, which E-04 supplies for this tree. `.aw/records/backlog/README.md` documents the item FORMAT and is unaffected by a verb-side refusal. The user-facing surface that does change is the two verbs' `--help`-adjacent refusal text, which is emitted by the code this plan edits rather than documented separately.

## Open questions

### OQ-01: Should a refused `--summary` be reported as exit 2 (usage) or exit 1 (findings)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: exit 2. Every existing usage refusal in `backlog.run_new` returns 2 (the `--priority`/`--work-kind` enum guards, `--summary is required`, blocked-requires-gate, and the unresolvable `--blocks-release` guard), `cli.py`'s backlog family and `command_surface`'s `backlog new` entry both declare the contract as `(0, 1, 2)`, and the repository convention recorded there is 0 clean / 1 findings / 2 cannot-run-or-usage. A bad flag value is a cannot-run, not a finding about an existing artifact, so 2 is the consistent code and 1 would make this verb disagree with its own siblings.

### OQ-02: Should `--message` be refused, given it lands in the history body rather than the metadata block?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT: yes, refuse it. The distinction does not protect anything, because F-07 drove a `--message` newline into a FORGED history record (`done ... approved by the maintainer`) that `validate_item` reported as clean. The workflow history is the artifact's provenance record, and the repository treats a forged attestation as a first-order hazard (`AGENTS.md`: "never hand-write an `- Approval:` attestation"). Non-blocking because the same helper covers it at no additional design cost; if a reviewer disagrees, E-03 can drop the `--message` call site without affecting E-01/E-02.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste an actual Python session (or pytest case output) calling `backlog._refuse_unsafe_descriptive` on five inputs and showing the returned values: `None` -> `None`; `"ok"` -> `None`; `"a\nb"` -> a message containing `newline`; `"a\x07b"` -> a message containing `control`; a 340-character value -> a message containing both `300` and `340`. Also paste the helper's source showing it calls `A.is_safe_descriptive` for the verdict, proving the predicate's conditions were not reimplemented.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the actual terminal output of `aw backlog new` with a 340-character `--summary` against a temp fixture, showing exit status 2 and the refusal on stderr, plus an `ls` of the backlog tree showing NO file was written. Then paste the SAME command with a conforming summary showing exit 0, the written filename, and `aw backlog check --agent` reporting `"outcome":"conforms"` on that fixture. This is the paired before/after of F-01 and F-02, so both halves must be present.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste four actual runs against temp fixtures: (a) `aw backlog new --status blocked --gate-kind todo --gate-ref $'TODO.md\n- Blocks-Release: next'` showing exit 2 and no file written; (b) the same `--gate-ref` through `aw backlog set --status blocked` showing exit 2 AND a `diff` (or an sha256 of the file before and after) proving the item is byte-identical; (c) `aw backlog new --message $'note\n- Blocks-Release: next'` showing exit 2; (d) `aw backlog set --message $'note\n- Blocks-Release: next'` showing exit 2 and the same byte-identical proof. Also paste one run showing a LEGITIMATE multi-word `--message` and a valid `--gate-ref` still succeeding, so the guard is shown not to over-refuse.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the full `python3 -m pytest tests/test_backlog_descriptive_safety.py` output including the `N passed` summary line. Then paste the PRE-FIX run of the same module against stashed implementation code (`git stash push -- agent_workflows/backlog.py`), showing the unsafe-shape cases FAILING with assertion text visible and the conforming case PASSING. A module that passes before the fix does not validate E-04.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the injection tests' names and outcomes from the pytest output. For the PRE-FIX half, paste the actual written file content from a pre-fix `--summary` injection run showing the smuggled `- Blocks-Release: next` bullet in front matter, alongside `parse_item(...).blocks_release == 'next'` and `validate_item(...) == []`, which is the F-03/F-04 measurement the test encodes. Then paste the boundary test showing a 300-character summary ACCEPTED and a 301-character summary REFUSED, the preserved empty-summary refusal message, the `--agent` refusal returning 2 with a well-formed (or deliberately empty) stdout, `python3 -m pytest` (full fast suite) with its `N passed` summary, and `aw backlog check --agent` plus `aw check backlog --agent` both reporting `"outcome":"conforms"` on the repository tree.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval recorded as `- Status: approved` with an `- Approval:` attestation; this plan is authored `to-review` and carries no `- Readiness:` field, because that field is an OUTPUT of `/plan-review` and writing one here would forge a review that has not happened.

Execution contract: commit only the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Run the suite bare as `python3 -m pytest` and paste actual output. Do not mark any `V-*` item complete without the concrete evidence it names, and specifically do not mark V-04 or V-05 complete without the PRE-FIX failing runs, since the injection findings are the load-bearing half of this plan's case.

Post-gate lifecycle: after every `E-*` is performed and every `V-*` is verified with pasted evidence, run `aw ipd lint --phase pre-transition` and move this plan to `.aw/records/plans/executed/` through the tooled transition. This plan carries `- From-Backlog: a0s33b` and inherits that item's `- Blocks-Release: next`, so executing it is what legitimately discharges the item's release gate; the backlog item itself moves to `graduated`, never to `done`, at authoring time.
