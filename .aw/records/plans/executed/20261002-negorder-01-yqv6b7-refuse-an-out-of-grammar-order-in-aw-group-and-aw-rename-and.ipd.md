# IPD: Refuse an out-of-grammar --order in aw group and aw rename, and make the Order substitution regex fail safe instead of silently duplicating the field

- Date: 2026-10-02
- Kind: child
- Concern: Backlog `bmhoxe` measured that `aw group plans <id6> --set <s> --order -1 --rename --apply` and `aw rename plans --id <id6> --order -1 --apply` both exit 0 and corrupt the plan twice: the front matter gains a SECOND `- Order: -1` line (so `aw ipd lint` reports `IPD-M102: Order: duplicate field`), and the file is renamed with a double hyphen where the two-digit `NN` facet belongs (`20260920-negset--1-hhh888-orch.ipd.md`). A later repair with `--order 0` folds the broken prefix into the slug (`...-negset-00-hhh888-negset-1-orch.ipd.md`). Cause, read in code: `plans_refs._ORDER_LINE_RE` is `(?m)^- Order:\s*(\d+)\s*$`, which cannot match a minus sign, so `plans_refs._set_metadata`'s substitution finds nothing, its early-return guard is False, and the insertion branch appends a second `- Order:` line; the name builder formats the order into the `NN` facet without a range check. The existing Kind-conditional refusal (`plans_refs._validate_plan_order`, executed plan `qhcojn`) only fires for `Kind: child`, so a plan with no `- Kind:` line is not protected, and 102 plans in this tree carry none.
- Scope: IN: an unconditional range check on the RESOLVED order, per plan, at both write sites (`plans_refs.plan_set_assign` for `aw group plans`, and the `aw rename plans` path in `plans_refs` that resolves `order` before calling `_validate_plan_order`), refusing a value outside 0 to 99 with exit 2 and nothing written, and NOT overridable by `--allow-invalid-order` (that flag overrides the Kind rule, not the grammar); make `_set_metadata` fail safe by widening `_ORDER_LINE_RE` to `-?\d+` and asserting the result carries exactly one `- Order:` line; apply the same widening to `artifact_rename._ORDER_LINE_RE`, its twin; a regression test. OUT: the Kind-conditional rule (`qhcojn`, executed; `xvi55d`, pending); repairing existing plans (the corpus is clean, re-measured at execution); any other verb.
- Scope-Paths: agent_workflows/plans_refs.py, agent_workflows/artifact_rename.py, tests/test_plans_order_grammar.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: low
- From-Backlog: bmhoxe
- Blocks-Release: next
- Set: negorder
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: yqv6b7

## Workflow history
- 2026-10-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: yqv6b7 verified (set negorder, attempt 1).
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 /plan-review (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004 (all fixed; record `.aw/records/reviews/20261007-negorder-01-yqv6b7-refuse-an-out-of-grammar-order-in-aw-group-and-aw-rename-and.review.md`)
- 2026-10-07 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed
- 2026-10-07 to-review (aw set): authored from backlog bmhoxe; all placeholders replaced, lints conforming

- 2026-10-06 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored the plan body from backlog `bmhoxe`, whose measurements and proposed fix are complete; every placeholder replaced. The item's "IF BUILT" section is the design; the range 0 to 99 is the two-digit `NN` facet the uniform naming grammar defines.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw group plans` and `aw rename plans` refuse any resolved Order that the filename grammar cannot hold, before writing anything, on every plan whether or not it declares a Kind; and make the Order rewrite unable to leave two `- Order:` lines in a file.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: refuse an out-of-grammar order

- [x] E-01 Add `plans_refs._order_grammar_error(order) -> Optional[str]` returning a message when `order` is not an integer in 0 to 99 inclusive (the two-digit `NN` facet), naming the value and the allowed range. Call it in `plan_set_assign` on each plan's RESOLVED order (`start_order + i`, or the preserved order) BEFORE `_validate_plan_order`, returning `(None, err)` so the caller exits 2 with nothing written. Do not let `allow_invalid_order` bypass it.
  - Depends on: none
  - Expected outcome: `aw group plans <id6> --set s --order -1 --apply` exits 2, prints the range error, and leaves the file byte-identical; the same command WITHOUT `--apply` (preview) also exits 2, since `plan_set_assign` runs before `apply_renames`; `--order 99` on two plans resolves 99 then 100, refuses the second, and writes nothing for either (the whole batch is planned before any write, so an early `(None, err)` leaves both files untouched); `--order 98` on two plans (98, 99) succeeds.
  - Execution state: performed

- [x] E-02 Call the same check on the `aw rename plans` path in `plans_refs` after `order` is resolved (from `--order`, the front matter, or the filename) and before `_validate_plan_order`, returning exit 2 with nothing written; again not overridable by `--allow-invalid-order`.
  - Depends on: E-01
  - Expected outcome: `aw rename plans --id <id6> --order -1 --apply` exits 2 with the range error and the file unchanged; a plan with no `- Kind:` line is refused the same way.
  - Execution state: performed

### Task group 2: make the rewrite fail safe

- [x] E-03 Widen `_ORDER_LINE_RE` in `plans_refs` and `artifact_rename` to `(?m)^- Order:\s*(-?\d+)\s*$`, and in `plans_refs._set_metadata` assert after the rewrite that the text contains exactly one line matching `^- Order:` (raise a `ValueError` naming the plan otherwise). CORRECTED AT REVIEW: no caller turns that `ValueError` into a refusal today. `plans_refs.apply_renames` calls `_set_metadata` with no `try`, then `_core.atomic_write` and `_core.git_mv`, plan by plan, so a raise on plan 2 of a batch would surface as a traceback AFTER plan 1 was rewritten and moved. So ALSO: in `apply_renames`, compute every plan's new text in a first pass BEFORE any write or `git_mv`, and catch `ValueError` in `run_set_assign` and `run_mv` around `apply_renames`, printing `error: <message>` and returning `MutationResult(2)`. With E-01/E-02 in place this branch is a backstop unreachable from the CLI on valid input, which is why the test drives `_set_metadata` directly to reach it. Check every reader of `_ORDER_LINE_RE` (`_preserved_order`, the rename path's `om`, `artifact_rename`'s two uses) still behaves for a non-negative value, and record each in the evidence.
  - Depends on: E-02
  - Expected outcome: `_set_metadata` on a text with `- Order: -1` substitutes in place and never inserts a second line; a text carrying an Order line the widened regex still cannot match (for example `- Order: x1`) raises rather than writing a duplicate; and a raise inside `apply_renames` leaves every plan in the batch byte-identical and unmoved, reported as exit 2 by both verbs.
  - Execution state: performed

### Task group 3: pin it

- [x] E-04 Add `tests/test_plans_order_grammar.py` driving `python -m agent_workflows group plans` and `rename plans` as subprocesses in a temporary repository seeded with `--records-backend repository`, covering: negative order on a Kind-less plan and on a `Kind: child` plan, both verbs; 99 allowed and 100 refused; `--allow-invalid-order` not bypassing the range check; file bytes unchanged after every refusal; `aw ipd lint` on the plan reporting no `IPD-M102` after each case; and the bmhoxe repair sequence (`--order 0` after a refused `-1`) leaving a well-formed name. Prove the test can fail with TWO mutations, each reverted: (M1) remove the E-01/E-02 range-check calls ONLY, and paste the failure, which with E-03's widened regex in place is the exit-0 and malformed `--1` filename assertion, NOT a duplicate field (the widened substitution now matches `-1` in place); (M2) remove the range-check calls AND restore the old `(\d+)` regex, and paste the `IPD-M102` duplicate-field failure, which is bmhoxe's original corruption.
  - Depends on: E-03
  - Expected outcome: the new file passes; M1 fails on the exit code and filename, M2 reproduces bmhoxe's duplicate-field corruption and fails it; `tests/test_group_verb_policy.py` and `tests/test_plans_group_order_preservation.py` still pass.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE KIND RULE IS A SEPARATE CHECK. `plans_refs._validate_plan_order` (executed plan `qhcojn`) consults `ipd_schema.validate_metadata` only for `Kind: child`; pending plan `xvi55d` adds the orchestrator half. The grammar check here is unconditional and runs first, so it does not depend on either.
- `--allow-invalid-order` OVERRIDES THE KIND RULE ONLY. Its message reads "pass --allow-invalid-order to override" next to a Kind finding; an out-of-grammar order can never produce a valid filename, so overriding it would always corrupt.
- ORDER IS RESOLVED PER PLAN: `plan_set_assign` computes `start_order + i`, so the check must run on each resolved value, not on the flag (backlog `bmhoxe`, "Evaluate the RESOLVED order per plan").
- MEASURE WITH THE PACKAGE PINNED to the tree under test (`PYTHONPATH=<tree>`, `AW_NO_REEXEC=1`), and seed fixtures with `--records-backend repository`.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Both verbs corrupt on a negative order, exit 0. | backlog `bmhoxe` measurement at HEAD `ee1f2eff2`: `aw group plans hhh888 --set negset --order -1 --rename --apply` produced two `- Order: -1` lines and the name `20260920-negset--1-hhh888-orch.ipd.md`; `aw rename plans --id kkk555 --order -1 --apply` the same |
| F-02 | The regex cannot match a minus, so substitution misses and insertion duplicates. | `plans_refs._ORDER_LINE_RE` is `(?m)^- Order:\s*(\d+)\s*$`; `_set_metadata` substitutes, then returns early only if both lines match, else inserts after `- Id:` |
| F-03 | The Kind rule does not cover Kind-less plans. | `plans_refs._validate_plan_order` returns None unless `_read_kind(text) == ipd_schema.KIND_CHILD`; 102 plans carry no `- Kind:` (backlog `bmhoxe`) |
| F-04 | `artifact_rename` carries a twin regex with the same blind spot. | `artifact_rename._ORDER_LINE_RE` is the same pattern, used to rewrite and to match front-matter Order lines |
| F-05 | The corpus is clean, so nothing needs repair. | backlog `bmhoxe`: 0 of 1135 plan files carry a negative Order or a non-two-digit cluster facet; re-measure at execution |

## Proposed changes (ordered, validatable)

1. Unconditional 0 to 99 check on each resolved order in `aw group plans` (E-01) and `aw rename plans` (E-02), not overridable.
2. Widen both Order regexes and assert a single Order line after the rewrite (E-03).
3. Subprocess tests on both verbs with a mutation reproducing bmhoxe (E-04).

## Deferred / out of scope (with reason)

- THE ORCHESTRATOR HALF OF THE KIND RULE. Owned by pending plan `xvi55d`.
  - Carrier: xvi55d
  - Carrier-Evidence: .aw/records/plans/executed/20261001-oev4h7-01-xvi55d-refuse-an-orchestrator-at-a-nonzero-order-in-aw-group-and-aw.ipd.md
- OTHER ARTIFACT TYPES' `aw group`/`aw rename`. They route through `artifact_rename`, whose regex E-03 widens; their name builder `compute_target_name` is not shown to accept an out-of-range order, and no measurement shows a defect there.
  - Carrier-Declined: not measured as broken; E-03's regex widening removes the shared duplicate-line trap

## Scope check

- Over-scope: none. Two production modules and one test file. The `apply_renames` pre-pass and the `ValueError` handling in `run_set_assign`/`run_mv` (added at review) are inside `plans_refs.py`, already declared.
- Under-scope: none known.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_plans_order_grammar.py tests/test_group_verb_policy.py tests/test_plans_group_order_preservation.py -q` pasted.
- Re-measure the corpus (no negative Order, no non-two-digit facet) and paste the counts.
- Mutation run pasted.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec edited. The uniform naming grammar (`YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md`, `NN` two digits) is already stated in `AGENTS.md` and `.aw/records/plans/README.md`; this plan makes the two verbs enforce it.

## Open questions

### OQ-01: Should Order 0 to 99 be enforced, or only non-negative?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: 0 to 99. The backlog item asks for non-negative, but the defect it measured is a value the `NN` facet cannot hold, and 100 has the same problem (a three-digit facet the grammar does not define). The upper bound costs nothing: the largest Order in the corpus is far below it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the `plan_set_assign` diff and the subprocess outputs for `--order -1` (exit 2, message, file unchanged by checksum) the same command without `--apply` (exit 2), the `--order 99` two-plan case (resolved 100 refused, nothing written for either, both checksums unchanged), and the `--order 98` two-plan case succeeding.
  - Observed evidence: verified. Group plans enforces 0 to 99 range check before any write or metadata update, refusing -1 and 100 with exit code 2 and leaving files unchanged by checksum:
`plan_set_assign` diff in `agent_workflows/plans_refs.py`:
```diff
@@ -260,6 +260,16 @@ def _preserved_date(name: str, text: str) -> str:
     return _plan_date(text)


+def _order_grammar_error(order: int) -> Optional[str]:
+    """Validate that the resolved Order is an integer in 0 to 99 inclusive (the two-digit NN facet)."""
+    if not isinstance(order, int) or order < 0 or order > 99:
+        return (
+            f"Order '{order}' is out of grammar: must be an integer from 0 to 99 "
+            "(the two-digit NN facet)"
+        )
+    return None
+
@@ -348,6 +348,9 @@ def plan_set_assign(
             if start_order is not None
             else _preserved_order(src.name, text)
         )
+        grammar_err = _order_grammar_error(order)
+        if grammar_err:
+            return None, f"plan '{id6}' ({src.name}): {grammar_err}"
         order_err = _validate_plan_order(text, order)
```

Subprocess outputs:
```text
=== CASE 1: group plans --order -1 --apply ===
exit code: 2
stdout: error: plan 'v01aa1' (20261002-testset-01-v01aa1-test-plan.ipd.md): Order '-1' is out of grammar: must be an integer from 0 to 99 (the two-digit NN facet)
file unchanged by sha256: True

=== CASE 2: group plans --order -1 (preview) ===
exit code: 2
stdout: error: plan 'v01aa1' (20261002-testset-01-v01aa1-test-plan.ipd.md): Order '-1' is out of grammar: must be an integer from 0 to 99 (the two-digit NN facet)

=== CASE 3: group plans two plans --order 99 ===
exit code: 2
stdout: error: plan 'v01bb2' (20261002-testset-02-v01bb2-test-plan.ipd.md): Order '100' is out of grammar: must be an integer from 0 to 99 (the two-digit NN facet)
p1 unchanged by sha256: True
p2 unchanged by sha256: True

=== CASE 4: group plans two plans --order 98 --rename --apply ===
exit code: 0
stdout: renamed .aw/records/plans/pending/20261002-testset-01-v01aa1-test-plan.ipd.md -> .aw/records/plans/pending/20261002-newset-98-v01aa1-test-plan.ipd.md
renamed .aw/records/plans/pending/20261002-testset-02-v01bb2-test-plan.ipd.md -> .aw/records/plans/pending/20261002-newset-99-v01bb2-test-plan.ipd.md
wrote        .aw/records/plans/INDEX.json, INDEX.md (2 plans)
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the rename-path diff and the outputs for `--order -1` on a Kind-less plan and a `Kind: child` plan, and for `--order -1 --allow-invalid-order` still refused.
  - Observed evidence: verified. Rename plans enforces 0 to 99 range check before any write on both Kind-less and Kind: child plans, and refuses even with --allow-invalid-order:
Rename-path diff in `agent_workflows/plans_refs.py`:
```diff
@@ -679,6 +679,10 @@ def run_mv(args: argparse.Namespace) -> "MutationResult":
         else:
             parsed = _CLUSTERED_RE.match(src.name)
             order = int(parsed.group("nn")) if parsed else 0
+    grammar_err = _order_grammar_error(order)
+    if grammar_err:
+        print(f"error: plan '{id6}' ({src.name}): {grammar_err}")
+        return MutationResult(2)
     # Validity refusal (qhcojn, xvi55d): refuse a resolved Order violating either half of
```

Subprocess outputs:
```text
=== CASE 1: rename plans Kind-less --order -1 --apply ===
exit code: 2
stdout: error: plan 'v02knd' (20261002-testset-01-v02knd-test-plan.ipd.md): Order '-1' is out of grammar: must be an integer from 0 to 99 (the two-digit NN facet)

=== CASE 2: rename plans Kind: child --order -1 --apply ===
exit code: 2
stdout: error: plan 'v02chd' (20261002-testset-01-v02chd-test-plan.ipd.md): Order '-1' is out of grammar: must be an integer from 0 to 99 (the two-digit NN facet)

=== CASE 3: rename plans --order -1 --allow-invalid-order --apply ===
exit code: 2
stdout: error: plan 'v02chd' (20261002-testset-01-v02chd-test-plan.ipd.md): Order '-1' is out of grammar: must be an integer from 0 to 99 (the two-digit NN facet)
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste both regex diffs and the `_set_metadata` assertion; paste the unit result for a `- Order: -1` text (substituted, one line) and for the unmatchable-Order-line case (raises); paste the `apply_renames` first-pass diff and the `run_set_assign`/`run_mv` `ValueError` handling, plus a run showing a forced raise exits 2 with every plan in the batch unchanged by checksum and unmoved; list each other reader of the regex (`_preserved_order`, `run_mv`'s `om`, `artifact_rename`'s substitution and its line-match) with its checked behavior for a non-negative value.
  - Observed evidence: verified. Both _ORDER_LINE_RE regexes widened to (-?\d+); _set_metadata asserts single Order line; apply_renames pre-computes new text and run_set_assign/run_mv catches ValueError:
Both regex diffs:
In `agent_workflows/plans_refs.py`:
```diff
-_ORDER_LINE_RE = re.compile(r"(?m)^- Order:\s*(\d+)\s*$")
+_ORDER_LINE_RE = re.compile(r"(?m)^- Order:\s*(-?\d+)\s*$")
```
In `agent_workflows/artifact_rename.py`:
```diff
-_ORDER_LINE_RE = re.compile(r"(?m)^- Order:\s*(\d+)\s*$")
+_ORDER_LINE_RE = re.compile(r"(?m)^- Order:\s*(-?\d+)\s*$")
```

`_set_metadata` assertion diff:
```diff
@@ -76,7 +76,12 @@ def _set_value(set_id: str, descriptive: Optional[str]) -> str:


 def _set_metadata(
-    text: str, *, set_id: str, order: int, descriptive: Optional[str] = None
+    text: str,
+    *,
+    set_id: str,
+    order: int,
+    descriptive: Optional[str] = None,
+    plan_name: Optional[str] = None,
 ) -> str:
...
+    order_lines = re.findall(r"(?m)^- Order:.*$", text)
+    if len(order_lines) != 1:
+        target = plan_name or _read_id(text) or "plan"
+        raise ValueError(
+            f"plan '{target}': expected exactly one '- Order:' line after metadata update, "
+            f"found {len(order_lines)}"
+        )
+    return text
```

Unit result for `- Order: -1` and unmatchable line:
```text
=== UNIT 1: _set_metadata with - Order: -1 ===
result text:
# IPD: Test Plan
- Id: v03aa1
- Set: newset
- Order: 5
## Goal

Order lines: ['- Order: 5']
count == 1: True

=== UNIT 2: _set_metadata with unmatchable line - Order: x1 ===
caught expected ValueError: plan 'v03bb2': expected exactly one '- Order:' line after metadata update, found 2
```

`apply_renames` pre-computation first-pass and `run_set_assign`/`run_mv` `ValueError` handling diff:
```diff
@@ -467,16 +495,21 @@ def apply_renames(
         except ValueError:
             return path.as_posix()

+    # IPD yqv6b7 E-03: Pre-compute every plan's new text in a first pass before any write or
+    # git_mv, so an invalid plan raises ValueError before any file in the batch is touched.
+    new_texts: List[str] = []
     for i, p in enumerate(plans):
-        # Update Set/Order metadata in place first. Use the plan's explicit order when provided
-        # (mv preserves it), else the enumerate index (set-assign batch sequencing).
-        text = p.old_path.read_text(encoding="utf-8")
-        text = _set_metadata(
-            text,
+        raw_text = p.old_path.read_text(encoding="utf-8")
+        new_text = _set_metadata(
+            raw_text,
             set_id=_core.kebab(set_id),
             order=p.order if p.order is not None else i,
             descriptive=descriptive,
+            plan_name=p.old_path.name,
         )
+        new_texts.append(new_text)
+
+    for p, text in zip(plans, new_texts):
         _core.atomic_write(p.old_path, text, prefix=".plans-refs-")
@@ -621,15 +621,19 @@ def run_set_assign(args: argparse.Namespace) -> "MutationResult":
     if err:
         print(f"error: {err}")
         return MutationResult(2)
-    touched = apply_renames(...)
+    try:
+        touched = apply_renames(...)
+    except ValueError as e:
+        print(f"error: {e}")
+        return MutationResult(2)
     return MutationResult(0, touched)
@@ -705,15 +709,19 @@ def run_mv(args: argparse.Namespace) -> "MutationResult":
-    touched = apply_renames(...)
+    try:
+        touched = apply_renames(...)
+    except ValueError as e:
+        print(f"error: {e}")
+        return MutationResult(2)
     return MutationResult(0, touched)
```

Run showing forced raise in `apply_renames`:
```text
=== UNIT 3: forced raise in apply_renames batch ===
error: plan '20261002-testset-02-v03dd4-test-plan.ipd.md': expected exactly one '- Order:' line after metadata update, found 2
res rc: 2
p1 unchanged by sha256: True
p2 unchanged by sha256: True
p1 exists at original path: True
p2 exists at original path: True
```

Other readers of `_ORDER_LINE_RE` for non-negative values:
- `_preserved_order(name, text)`: `_ORDER_LINE_RE.search(text)` matches `- Order: 5`, group(1) `"5"` -> `int("5") == 5`. Filename fallback `_CLUSTERED_RE.match(name).group("nn")` -> `"05"` -> `5`. Preserved.
- `run_mv`'s `om`: `_ORDER_LINE_RE.search(text)` matches `- Order: 5`, group(1) `"5"` -> `int("5") == 5`. Preserved.
- `artifact_rename.py` substitution (lines 301-302): `_ORDER_LINE_RE.search(text)` matches `- Order: 5`, `.sub(f"- Order: {order}", text)` rewrites in place. Preserved.
- `artifact_rename.py` line-match (line 549): `_ORDER_LINE_RE.match(line)` matches `"- Order: 5\n"`, appends `f"- Order: {order}\n"`. Preserved.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new test file passing with its count; mutation M1's failure (exit code/filename) and mutation M2's `IPD-M102` duplicate-field failure, each reverted; the two existing test files passing; the corpus re-measurement; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence: verified. Full validation suite passes with 12 new tests in test_plans_order_grammar.py; mutations M1 and M2 verified and reverted; 0 source structure reads; leak sanitizer clean:
New test file passing count:
```text
tests/test_plans_order_grammar.py ............                                                             [100%]
12 passed in 7.04s
```

Mutation M1 failure (range-checks removed, widened regex kept -> exit 0 and malformed `--1` filename):
```text
FAILED tests/test_plans_order_grammar.py::test_negative_order_refused_group_plans_kindless
    def test_negative_order_refused_group_plans_kindless(order_repo: Path) -> None:
        p = _seed_conforming_plan(order_repo, "knd001", kind=None, order=1)
        proc = _run_cli(order_repo, ["group", "plans", "knd001", "--set", "newset", "--order", "-1", "--apply"])
>       assert proc.returncode == 2
E       AssertionError: assert 0 == 2
E        + where 0 = CompletedProcess(args=['python3', '-m', 'agent_workflows', 'group', 'plans', 'knd001', '--set', 'newset', '--order', '-1', '--apply', '--dir', '/tmp/...'], returncode=0, stdout='wrote .aw/records/plans/INDEX.json, INDEX.md (1 plans)\n', stderr='').returncode

FAILED tests/test_plans_order_grammar.py::test_bmhoxe_repair_sequence_leaves_well_formed_name
>       assert proc_fail.returncode == 2
E       AssertionError: assert 0 == 2
E        + where 0 = CompletedProcess(args=['python3', '-m', 'agent_workflows', 'rename', 'plans', 'rep001', '--order', '-1', '--apply', '--dir', '/tmp/...'], returncode=0, stdout='renamed ... -> .../20261002-testset--1-rep001-test-plan.ipd.md\nwrote .aw/records/plans/INDEX.json, INDEX.md (1 plans)\n', stderr='').returncode
```

Mutation M2 failure (range-checks removed, old `(\d+)` regex restored, assertion disabled -> duplicate `- Order:` line and `IPD-M102` failure):
```text
rename exit code: 0
corrupted filename: 20261002-testset--1-rep001-test-plan.ipd.md
corrupted content Order lines:
   - Order: -1
   - Order: -1
lint exit code: 1
lint output:
-    ◔  to-review    plan        20261002-testset--1-rep001-test-plan  [medium]  error
     ! IPD-M102: Order: duplicate field
     ! IPD-M101: Kind: required field missing
     ! IPD-N001: filename does not match the plan grammar (YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md)
```

Existing test files passing:
```text
python3 -m pytest -o addopts="" tests/test_plans_order_grammar.py tests/test_group_verb_policy.py tests/test_plans_group_order_preservation.py -q
........................................................................ [ 77%]
.....................                                                    [100%]
93 passed in 13.28s
```

Corpus re-measurement:
```text
Total .ipd.md files: 1329
Negative Order count: 0
Non-two-digit cluster facet count: 0
```

Source-structure reads grep:
```text
$ grep -E "inspect|ast\.|parse\(|read_text\(.*agent_workflows" tests/test_plans_order_grammar.py
(empty output, exit code 1: no source-structure reads)
```

Bare `python3 -m pytest` reconciled against baseline:
```text
Baseline:
FAILED tests/test_runwire_verifier_authority.py::test_collision_guard_bites_by_mutation
1 failed, 6979 passed, 2 skipped, 3 warnings in 421.28s (0:07:01)

Post-implementation:
FAILED tests/test_runwire_verifier_authority.py::test_collision_guard_bites_by_mutation
1 failed, 6991 passed, 2 skipped, 3 warnings in 364.18s (0:06:04)
(+12 new tests passed, 0 regressions; 1 pre-existing failure tracked in backlog 4dktme)
```

`aw ipd lint` conforming:
```text
$ python3 -m agent_workflows ipd lint .aw/records/plans/pending/20261002-negorder-01-yqv6b7-refuse-an-out-of-grammar-order-in-aw-group-and-aw-rename-and.ipd.md
- >  ◕  approved     plan        20261002-negorder-01-yqv6b7  [low]  [blocking]  conforming
```

`aw sanitize --agent` clean:
```text
$ python3 -m agent_workflows sanitize --agent
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
```

`git diff --cached --name-only` listing declared paths:
```text
agent_workflows/artifact_rename.py
agent_workflows/plans_refs.py
tests/test_plans_order_grammar.py
.aw/records/plans/pending/20261002-negorder-01-yqv6b7-refuse-an-out-of-grammar-order-in-aw-group-and-aw-rename-and.ipd.md
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Paste actual output for every `V-*`. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`. Backlog `bmhoxe` carries `- Blocks-Release: next`, inherited here; it closes `done` only when this plan executes.
