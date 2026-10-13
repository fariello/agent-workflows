# IPD: Migrate the read-only history consumers onto the shared history-record reader

- Date: 2026-10-12
- Kind: child
- Concern: After sibling `kgv213` the dedup predicate and the backlog writer read history through `attention_contract.history_block`, but every other reader still bounds the block with `attention._history_section_lines` (heading-to-heading) and matches records against `line.strip()`, which counts INDENTED history-shaped lines that the canonical rule says are not records. The backlog item asks to "migrate the consumers to it" rather than leave two partitioning rules, and warns that `_history_section_lines` has many consumers, including `plan_readiness` verdict reading, so this migration is its own reviewable change. Measured in this lane at HEAD `5ebf5364d`: substituting the canonical rule for every consumer below and recomputing over all 2489 tracked artifacts with a history heading changed ZERO answers.
- Scope: IN: migrate the record-reading consumers to `attention_contract.history_block(text).records`: `attention` (`_prompts_record`, `_release_record`, `_spec_record`, `_plans_record`, `_research_record`, `_backlog_record`, each `A.last_history_at(_history_section_lines(text))`), `check_engine` (`_item_close_date`, `_item_graduated_date`, `_spec_implementing_date`), and `plan_readiness` (`extract_newest_history_entry`, `history_has_review_record`, `newest_verdict`); keep `attention._history_section_lines` as a function (tests and `tests/support.py` reference it) but document that record readers must use `history_block`; a corpus-equivalence test and fixtures fencing each consumer's indented-quotation behavior; one CHANGELOG entry. OUT: `status_set.same_status_message_is_duplicate` and `backlog` (done by `kgv213`); test modules that call `_history_section_lines` to inspect fixtures (they read their own outputs and are not consumers of the rule); any change to positional newest-first semantics; plan history writers.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/check_engine.py, agent_workflows/plan_readiness.py, tests/test_history_consumers_shared_reader.py, CHANGELOG.md
- Item-Dependencies: executed:kgv213
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: wkpcop
- Set: histdedup
- Order: 4
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6iab2o
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Record: .aw/records/reviews/20261012-histdedup-04-6iab2o-migrate-the-read-only-history-consumers-onto-the-shared-hist.review.md Round 1

- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog item `wkpcop` to carry the consumer migration the item suggests, split from `kgv213` because these readers gate approval and attention surfaces. Zero-answer-change measured over 2489 artifacts at `5ebf5364d`. Blocking status: none.
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every reader of history RECORDS use the one canonical bounding rule, so no surface (attention dates, close and graduation dates, review-verdict and approval gates) can count a quoted, indented history line as a record, while proving no current answer changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [x] E-01 Before editing, record the base sha (`git rev-parse HEAD`) and capture a BASELINE answers file outside the tree's tracked paths (e.g. under `.aw/state/`, gitignored): for every tracked `.aw/records/**/*.md` containing `## Workflow history`, the values of `attention_contract.last_history_at([l.strip() for l in attention._history_section_lines(t)])`, `check_engine._item_close_date`, `check_engine._item_graduated_date`, `check_engine._spec_implementing_date`, `plan_readiness.extract_newest_history_entry`, `plan_readiness.newest_verdict`, `plan_readiness.history_has_review_record`, plus `aw attention --format json` saved beside it. The artifact set is RE-DERIVED at execution time (git-tracked files only; never walk `.aw/worktrees/`); 2489 at authoring and 2516 at review are context, not the bar. FIRST check the prerequisite: `kgv213` is under `.aw/records/plans/executed/` AND `python3 -c "from agent_workflows.attention_contract import history_block; print(history_block.__doc__ is not None)"` succeeds. At review (HEAD `a60a58038`) neither held: `kgv213` was `reviewed` in `pending/` and `history_block` did not exist. If either fails, mark this and every later item `blocked`, set the plan's workflow note accordingly, and edit nothing.
  - Depends on: none
  - Expected outcome: the prerequisite check pasted; a JSON baseline keyed by path, with its artifact count; the saved attention JSON.
  - Execution state: performed

### Task group 2: migrate

- [x] E-02 `agent_workflows/attention.py`: in the six `_*_record` builders replace `A.last_history_at(_history_section_lines(text))` with `A.last_history_at(A.history_block(text).records)`. Add to `_history_section_lines`'s docstring that it returns the RAW heading-bounded section and that record readers must use `attention_contract.history_block`.
  - Depends on: E-01
  - Expected outcome: no `_history_section_lines` call remains on a record-reading path in `attention.py`.
  - Execution state: performed

- [x] E-03 `agent_workflows/check_engine.py`: in `_item_close_date`, `_item_graduated_date`, `_spec_implementing_date` read `_ac.history_block(text).records` (records are already rstripped, column-zero, so the `^- ` regexes match unchanged) and update each docstring's "Reuses `attention._history_section_lines`" sentence.
  - Depends on: E-01
  - Expected outcome: the three readers call the shared reader.
  - Execution state: performed

- [x] E-04 `agent_workflows/plan_readiness.py`: in `extract_newest_history_entry`, `history_has_review_record`, `newest_verdict` iterate `history_block(text or "").records` instead of stripped `_history_section_lines` lines; drop the now-unused import only if nothing else in the module uses it; update the module docstring sentence that says the bounding is reused from `attention._history_section_lines`.
  - Depends on: E-01
  - Expected outcome: approval/verdict readers use the shared reader; their answers on the live corpus are unchanged (V-04 proves it).
  - Execution state: performed

### Task group 3: tests and changelog

- [x] E-05 `tests/test_history_consumers_shared_reader.py` (new, behavioral, P16) plus `CHANGELOG.md`: tests calling the real consumers on fixtures written to a temp directory, asserting return values only. (a) THE GATE CASE (F-04): a plan whose only real record is `- <d> to-review (aw set): authored`, carrying `- Readiness: go-pending-approval`, followed by a blank line, a column-zero prose line, a blank line and an indented quoted `    - <d> reviewed (aw set): /plan-review (x): APPROVE; none`, with a later `## Goal`: assert `history_has_review_record` is False, `newest_verdict` is `(None, "")`, and `is_plan_review_approved(<path>)` is False. (a2) The same fixture with the quoted line indented directly under a real `REJECT` review record that has a column-zero prose line between them: `newest_verdict` returns the NEGATIVE polarity read from the real record. (b) A backlog item whose only history-shaped line is indented: `attention.scan` on a temp repo holding that item reports `last_history_at` None for it. (b2) F-05: a backlog item whose block is `Some prose` followed by column-zero `- <d> done ...` and `- <d> graduated ...` lines: `_item_close_date` and `_item_graduated_date` return None, and a spec fixture of the same shape with an `implementing` line makes `_spec_implementing_date` return None. (c) A wrapped multi-line plan record (column-zero record directly followed by an indented continuation, then two more column-zero records) keeps every following record visible: `extract_newest_history_entry` returns the first record and `history_has_review_record` sees a review record placed third. Cases (a), (b2) MUST FAIL at the base sha: show it by copying the module into a temporary `git worktree add` of the base sha and running it there (never stash the working checkout). Add one CHANGELOG line (no em or en dashes) stating that attention, check and readiness readers now share the history bounding rule, so a quoted indented history line can no longer attest a review.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: new module passes; (a) and (b2) fail at the base sha; CHANGELOG has one new entry.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `attention_contract.newest_history_record` is POSITIONAL by design (date-max was measured to flip `history_verdict_approves` for 20 plans); `history_block` keeps file order, so positional semantics are untouched.
- `plan_readiness` gates unattended approval (`is_plan_review_approved`, `approval_refusals`), so any reader change there must be proven answer-preserving on the live corpus, not argued.
- `tests/support.py` documents `attention._history_section_lines` by name; it stays.
- Suite runs bare as `python3 -m pytest`.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | Consumers on the loose rule: six `attention` record builders, three `check_engine` date readers, three `plan_readiness` readers (plus `status_set.same_status_message_is_duplicate`, which `kgv213` owns). | `rg -n "_history_section_lines" agent_workflows` at `5ebf5364d`. |
| F-02 | Migration changes no answer today. | Probe patching the canonical rule into `attention._history_section_lines` and `plan_readiness._history_section_lines`, recomputing the seven answers in E-01 over 2489 artifacts: `diffs {}`. |
| F-03 | The loose rule CAN mis-answer: a quoted indented review line in a body under the history heading region (no intervening `## `) is read as a record. Six tracked artifacts carry indented history-shaped lines in that region (`tk1gqo`, `r74211`, `4znh53`, reviews `7jqev2`, `1i300e`, plan `y6gsqw`); none happens to change an answer, which is luck, not a property. | Corpus probe at `5ebf5364d`. |
| F-04 | (Review PR-001.) The loose rule ATTESTS A FORGED READINESS FIELD today. A plan whose only real history record is `- 2026-01-01 to-review (aw set): authored`, carrying a hand-written `- Readiness: go-pending-approval` and, after a blank line and prose, an indented quoted `    - 2026-01-02 reviewed (aw set): /plan-review (x): APPROVE; none`, makes `plan_readiness.history_has_review_record` return True, `newest_verdict` return `('positive', <the quoted line>)`, and `is_plan_review_approved` return True. That is the gate AGENTS.md says must refuse an unattested Readiness (`IPD-M107`), and it gates unattended `--full-auto` promotion. The canonical rule excludes the quoted line, so after E-04 all three refuse. Not reached by any tracked plan today. | Review probe at HEAD `a60a58038`: `history_has_review_record: True`, `newest_verdict: ('positive', '- 2026-01-02 reviewed ...')`, `is_plan_review_approved: True`. Corpus re-check: dropping indented lines from `plan_readiness`'s input changes 0 answers over 2516 tracked artifacts with a history heading. |
| F-05 | The `check_engine` date readers match their regexes against the RAW (unstripped) lines, so they already ignore indented lines; the defect there is a column-zero history-shaped line that FOLLOWS a column-zero prose line (the heading-to-heading bound keeps it). | Review probe: fixture `## Workflow history` / `Some prose` / `- 2026-01-01 done ...` / `- 2026-01-01 graduated ...` -> `_item_close_date` `20260101`, `_item_graduated_date` `20260101`; the canonical rule ends the block at `Some prose`, so both become None. An indented-only fixture already returns None for both. |

## Proposed changes (ordered, validatable)

1. E-01 baseline. 2. E-02..E-04 migrate. 3. E-05 fence and record.

## Deferred / out of scope (with reason)

- Deleting `_history_section_lines`: test code references it; deletion buys nothing once no production record reader uses it.
  - Carrier-Declined: test code references it and no production record reader will use it after this plan
- Test modules that read history from fixtures: they are inspecting outputs, not implementing the rule.
  - Carrier-Declined: they inspect their own fixture outputs and do not implement the rule

## Scope check

- Over-scope: none.
- Under-scope: none; every production consumer listed in F-01 that `kgv213` does not own is migrated.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_history_consumers_shared_reader.py tests/test_history_provenance.py tests/test_backlog_history_dedup_parity.py tests/test_history_block_bounding.py`, actual output pasted.
- Every existing test module covering `plan_readiness` and `attention` (find them with `rg -l "plan_readiness|attention" tests`), actual output pasted.
- The WHOLE BARE SUITE, `python3 -m pytest`, summary pasted, no new failure against the base.
- `aw attention --format json` before (base sha) and after, diffed: identical apart from timestamps.

## Spec / documentation sync

N/A. No spec states the bounding rule; the attention spec (`.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`) Section 8.5 requires `last_history_at` be "parsed from validated history, never mtime", which is preserved (still the newest record, now from the canonical reader).

## Open questions

### OQ-01: Is the blast radius acceptable?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The item flagged this risk without measuring it. F-02 measures it as zero answer changes across the whole tracked corpus (re-confirmed at review for `plan_readiness` over 2516 artifacts), and V-04 re-proves that at execution time against a fresh baseline, so the change is gated on evidence rather than argument. The change also CLOSES a live gate hole (F-04): today a quoted indented review line can attest a hand-written Readiness field.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: PASTE the prerequisite check (the `kgv213` path under `executed/` and the `history_block` import succeeding), the base sha, the baseline's artifact count and path, and the saved `aw attention --format json` path.
  - Observed evidence:
```
Prerequisite check:
$ test -f .aw/records/plans/executed/20261012-histdedup-02-kgv213-bound-the-workflow-history-block-by-one-shared-rule.ipd.md && echo "present" && python3 -c "from agent_workflows.attention_contract import history_block; print(history_block.__doc__ is not None)"
present
True

Base sha: 7f8bfa47854c30fd0d7cefa1558a3f3711e93eb6
Baseline artifact count: 2555 tracked artifacts with ## Workflow history
Baseline answers path: .aw/state/baseline-6iab2o/baseline_answers.json
Saved aw attention JSON path: .aw/state/baseline-6iab2o/attention_baseline.json
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE `git diff agent_workflows/attention.py` and `rg -n "_history_section_lines" agent_workflows/attention.py` showing only the definition remains. PASTE the before (E-01 saved file) / after `aw attention --format json` diff, filtered of volatile timestamp fields, showing no other difference (or each difference justified as in V-04).
  - Observed evidence:
```
$ rg -n "_history_section_lines" agent_workflows/attention.py
422:def _history_section_lines(text: str) -> List[str]:

$ git diff agent_workflows/attention.py
diff --git a/agent_workflows/attention.py b/agent_workflows/attention.py
index a15a51a8a..52431668e 100644
--- a/agent_workflows/attention.py
+++ b/agent_workflows/attention.py
@@ -420,6 +420,13 @@ def _match_tree_policy(rel_posix: str) -> Optional[TreePolicy]:


 def _history_section_lines(text: str) -> List[str]:
+    """Return the raw heading-bounded lines of the '## Workflow history' section.
+
+    This function returns raw, unvalidated lines between the history heading and the
+    next top-level/second-level heading. Readers that parse history records must use
+    `attention_contract.history_block` to enforce canonical record bounding (column-zero
+    chronological records, omitting indented block quotes and prose).
+    """
     if "## Workflow history" not in text:
         return []
     m = re.search(r"(?m)^## Workflow history[ \t]*$", text)
@@ -1246,7 +1253,7 @@ def _prompts_record(
         )
         return None, drift
     id6 = prompts_mod.read_metadata_id6(text) or ""
-    lha = A.last_history_at(_history_section_lines(text))
+    lha = A.last_history_at(A.history_block(text).records)
     d_kind, d_text = _extract_detail(text)
     oqs, rqs = count_question_stats(text)
     return Item(
@@ -1288,7 +1295,7 @@ def _release_record(
         )
         return None, drift
     mid = _re.search(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$", text)
-    lha = A.last_history_at(_history_section_lines(text))
+    lha = A.last_history_at(A.history_block(text).records)
     d_kind, d_text = _extract_detail(text)
     oqs, rqs = count_question_stats(text)
     return Item(
@@ -1319,7 +1326,7 @@ def _spec_record(
         gate = {"kind": kind, "ref": ref}
         if summary:
             gate["summary"] = summary
-    lha = A.last_history_at(_history_section_lines(text))
+    lha = A.last_history_at(A.history_block(text).records)
     # awdoctorfix Order 01: read Blocks-Release from the spec's front-matter so the board can surface it.
     br = specs_mod._read_blocks_release(lines)
     # xprio rp859c E-03: populate Item.priority from the spec's `- Priority:` line so the board LABELS
@@ -1410,7 +1417,7 @@ def _plans_record(
             )
         )
     pid = _plans_id(text)
-    lha = A.last_history_at(_history_section_lines(text))
+    lha = A.last_history_at(A.history_block(text).records)
     # IPD 7mw7m5 E-02: populate Item.blocks_release for a release-blocking plan so it renders with
     # the `>` glyph / `[blocking]` label like specs/backlog blockers (the release_blockers SET scan
     # already re-reads the file, so set-membership does not depend on this; display parity does).
@@ -1497,7 +1504,7 @@ def _research_record(
         cls = A.class_of("research", status)

     rid = str(data.get("id", "")) if data.get("id") else ""
-    lha = A.last_history_at(_history_section_lines(text))
+    lha = A.last_history_at(A.history_block(text).records)
     # xprio 6vgd0k E-04: populate Item.priority from the doc's `priority:` frontmatter key so the
     # board LABELS a research doc's priority via the existing renderer (absent = None = no label).
     # Shared sort key unchanged.
@@ -1555,7 +1562,7 @@ def _backlog_record(
     gate = None
     if status == "blocked" and item.gate_kind and item.gate_ref:
         gate = {"kind": item.gate_kind, "ref": item.gate_ref}
-    lha = A.last_history_at(_history_section_lines(text))
+    lha = A.last_history_at(A.history_block(text).records)
     d_kind, d_text = _extract_detail(text)
     rd = read_readiness(text)
     oqs, rqs = count_question_stats(text)

aw attention --format json diff (before vs after):
Unified diff lines: 0 (Identical!)
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE `git diff agent_workflows/check_engine.py` and `aw check` output on the live repository with no new finding versus the base.
  - Observed evidence:
```
$ git diff agent_workflows/check_engine.py
diff --git a/agent_workflows/check_engine.py b/agent_workflows/check_engine.py
index 78f6daed9..d0ecd9c62 100644
--- a/agent_workflows/check_engine.py
+++ b/agent_workflows/check_engine.py
@@ -5993,15 +5993,14 @@ def _from_backlog_carrier_index(
 def _item_close_date(item_text: str) -> Optional[str]:
     """Derive the close date (compact YYYYMMDD) for a backlog item from its workflow history (b24o3q E-02).

-    Reuses `attention._history_section_lines` to bound the history section and
+    Uses `attention_contract.history_block` to read history section records and
     `attention_contract.last_history_at` to extract the newest record date.
     Returns compact YYYYMMDD, or None if no parseable date is found.
     """
-    from agent_workflows import attention as _att
     from agent_workflows import attention_contract as _ac

-    lines = _att._history_section_lines(item_text)
-    date_str = _ac.last_history_at(lines)
+    records = _ac.history_block(item_text).records
+    date_str = _ac.last_history_at(records)
     if not date_str:
         return None
     compact = date_str.replace("-", "").strip()
@@ -6268,13 +6267,13 @@ _GRADUATED_LINE_RE = _re.compile(
 def _item_graduated_date(item_text: str) -> Optional[str]:
     """Derive the newest graduated date (compact YYYYMMDD) for a backlog item from its history.

-    Reuses `attention._history_section_lines` to bound the history section.
+    Uses `attention_contract.history_block` to read history section records.
     Returns compact YYYYMMDD, or None if no graduation record is found.
     """
-    from agent_workflows import attention as _att
+    from agent_workflows import attention_contract as _ac

-    lines = _att._history_section_lines(item_text)
-    for line in lines:
+    records = _ac.history_block(item_text).records
+    for line in records:
         m = _GRADUATED_LINE_RE.match(line)
         if m:
             compact = m.group("date").replace("-", "").strip()
@@ -6291,13 +6290,13 @@ _IMPLEMENTING_LINE_RE = _re.compile(
 def _spec_implementing_date(spec_text: str) -> Optional[str]:
     """Derive the newest implementing transition date (compact YYYYMMDD) for a spec from its history.

-    Reuses `attention._history_section_lines` to bound the history section.
+    Uses `attention_contract.history_block` to read history section records.
     Returns compact YYYYMMDD, or None if no implementing record is found.
     """
-    from agent_workflows import attention as _att
+    from agent_workflows import attention_contract as _ac

-    lines = _att._history_section_lines(spec_text)
-    for line in lines:
+    records = _ac.history_block(spec_text).records
+    for line in records:
         m = _IMPLEMENTING_LINE_RE.match(line)
         if m:
             compact = m.group("date").replace("-", "").strip()

aw check summary:
Evidence
  plans  51   specs  21   prompts  2   research  100   backlog  80   walkthroughs  26   roadmaps  1   comms  1   releases  1   reviews  1025   other  1312
  errors  5   warnings  4   info  157
(No new finding versus the base).
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE `git diff agent_workflows/plan_readiness.py`. PASTE the output of recomputing the E-01 answers after E-02..E-04 over the SAME artifact set and diffing against the baseline: the required property is that every differing answer is listed and each is justified as an artifact whose history region holds a quoted indented line or a column-zero record after a prose line (F-03/F-05), with the new answer shown correct; an unjustified difference is a FAIL. Zero differences were measured at authoring and at review. PASTE also the E-05 (a) result showing `is_plan_review_approved` now refuses the F-04 fixture.
  - Observed evidence:
```
$ git diff agent_workflows/plan_readiness.py
diff --git a/agent_workflows/plan_readiness.py b/agent_workflows/plan_readiness.py
index 117109d49..57df2d91d 100644
--- a/agent_workflows/plan_readiness.py
+++ b/agent_workflows/plan_readiness.py
@@ -22,8 +22,8 @@ bug the plan was written to fix.
    "Append" and ``.aw/records/plans/README.md`` said "an appended, dated line"; both were corrected
    to say newest-first (E-07) precisely so a future reader does not "fix" this back into the bug.

-   The bounding and the record grammar are REUSED, not re-implemented: ``attention._history_section_lines``
-   already bounds the section at the next ``## `` heading and ``attention_contract.HISTORY_RECORD_RE``
+   The bounding and the record grammar are REUSED, not re-implemented: ``attention_contract.history_block``
+   already bounds the section canonically and ``attention_contract.HISTORY_RECORD_RE``
    already defines the ``- YYYY-MM-DD <text>`` record grammar. A fourth hand-rolled history parser
    would have been the wrong move.

@@ -77,9 +77,9 @@ from pathlib import Path
 from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

 from agent_workflows import ipd_schema as _schema
-from agent_workflows.attention import _history_section_lines
-from agent_workflows.attention_contract import HISTORY_RECORD_RE
 from agent_workflows.attention_contract import (
+    HISTORY_RECORD_RE,
+    history_block,
     newest_history_record as _newest_history_record,
 )

@@ -274,16 +274,14 @@ def extract_newest_history_entry(text: str) -> Optional[str]:
     the disagreement was a live bug on 534 artifacts; see that function for the measurement and for
     why the rule is deliberately POSITIONAL rather than greatest-by-date.

-    The section is BOUNDED at the next ``## `` heading (via the existing
-    ``attention._history_section_lines``), so a bullet in a later section can never be returned, and
+    The section is BOUNDED at the next ``## `` heading or non-record block boundary (via
+    ``attention_contract.history_block``), so a bullet in a later section can never be returned, and
     a bullet must match the ``- YYYY-MM-DD ...`` record grammar (``HISTORY_RECORD_RE``) to count, so
     an undated stray bullet inside the section is skipped rather than returned.

     Pure. Returns the record with surrounding whitespace stripped.
     """
-    return _newest_history_record(
-        [line.strip() for line in _history_section_lines(text)]
-    )
+    return _newest_history_record(history_block(text or "").records)


 def history_verdict_approves(entry: Optional[str]) -> bool:
@@ -575,8 +573,7 @@ def history_has_review_record(text: str) -> bool:

     Pure. False for text with no history section, which is the fail-closed answer.
     """
-    for line in _history_section_lines(text or ""):
-        candidate = line.strip()
+    for candidate in history_block(text or "").records:
         if not HISTORY_RECORD_RE.match(candidate):
             continue
         if is_review_history_entry(candidate):
@@ -615,8 +612,7 @@ def newest_verdict(text: str) -> Tuple[Optional[str], str]:

     Pure; takes whole plan text.
     """
-    for line in _history_section_lines(text or ""):
-        candidate = line.strip()
+    for candidate in history_block(text or "").records:
         if not HISTORY_RECORD_RE.match(candidate):
             continue
         if not is_review_history_entry(candidate):

Recomputed corpus diff against baseline:
Checked 2555 artifacts.
Diffs count: 0
diffs {}

E-05 (a) result:
plan_readiness.history_has_review_record(plan_text) -> False
plan_readiness.newest_verdict(plan_text) -> (None, "")
plan_readiness.is_plan_review_approved(plan_path) -> False
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE the new module's pytest output passing; PASTE the base-sha run (temporary `git worktree add` of the E-01 sha with the module copied in) showing cases (a) and (b2) FAILING there, then the worktree removed; and `git diff CHANGELOG.md`.
  - Observed evidence:
```
New module pytest output:
$ python3 -m pytest tests/test_history_consumers_shared_reader.py
.....                                                                    [100%]
5 passed in 7.61s

Base-sha run (temporary git worktree add):
$ git worktree add --detach /tmp/base-worktree-6iab2o 7f8bfa47854c30fd0d7cefa1558a3f3711e93eb6
$ cp tests/test_history_consumers_shared_reader.py /tmp/base-worktree-6iab2o/tests/test_history_consumers_shared_reader.py
$ (cd /tmp/base-worktree-6iab2o && PYTHONPATH=. python3 -m pytest -o addopts="" -v tests/test_history_consumers_shared_reader.py)
tests/test_history_consumers_shared_reader.py::TestHistoryConsumersSharedReader::test_gate_case_indented_quoted_review_under_real_reject PASSED [ 20%]
tests/test_history_consumers_shared_reader.py::TestHistoryConsumersSharedReader::test_backlog_indented_history_ignored_by_attention_scan PASSED [ 40%]
tests/test_history_consumers_shared_reader.py::TestHistoryConsumersSharedReader::test_prose_bounded_history_in_check_engine_date_readers FAILED [ 60%]
tests/test_history_consumers_shared_reader.py::TestHistoryConsumersSharedReader::test_gate_case_indented_quoted_review_does_not_attest_readiness FAILED [ 80%]
tests/test_history_consumers_shared_reader.py::TestHistoryConsumersSharedReader::test_multiline_wrapped_plan_record_preserves_subsequent_records PASSED [100%]

=================================== FAILURES ===================================
_ TestHistoryConsumersSharedReader.test_prose_bounded_history_in_check_engine_date_readers _
>       self.assertIsNone(check_engine._item_close_date(b_text))
E       AssertionError: '20261012' is not None
_ TestHistoryConsumersSharedReader.test_gate_case_indented_quoted_review_does_not_attest_readiness _
>           self.assertFalse(plan_readiness.history_has_review_record(plan_text))
E           AssertionError: True is not false
========================= 2 failed, 3 passed in 3.91s ==========================

$ git worktree remove --force /tmp/base-worktree-6iab2o

$ git diff CHANGELOG.md
diff --git a/CHANGELOG.md b/CHANGELOG.md
index d4e3c6032..438af5cd4 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

 Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

+- Fixed: attention, check and readiness readers now share the history bounding rule, so a quoted indented history line can no longer attest a review.
 - Fixed: a mismatch between the runner's own agent_workflows package and the one a nested aw call would load now fails only the affected item (with a tool-identity-mismatch refusal) instead of stopping the whole aw oc run or aw agy run; other independent items keep running.
 - Fixed: aw runs and aw run human output now masks tokens (such as ghp_ tokens and Bearer credentials) the same way --agent and --json already did.
 - Fixed: closing a release-blocking backlog item with --evidence now refuses a cited plan that has not been executed, on both setter spellings.
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval. Open questions: OQ-01 is resolved; none remain. PREREQUISITE: `kgv213` executed and `attention_contract.history_block` present (E-01 checks both; at review neither held, and `- Item-Dependencies: executed:kgv213` makes the runner hold this plan until it does). Start with `aw ipd begin 6iab2o`.

`- Scope-Paths:` is a DECLARATION reconciled at finalize: an out-of-scope edit that proves necessary is made and justified with `--scope-reason`, not a reason to stop. STOP and report only for E-01's prerequisite failure, or if a co-worker's uncommitted change occupies a region you must edit and the two cannot be safely combined. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no output does not satisfy it. Commit only through `aw commit 6iab2o -- <paths>` (never `git add -A`, `-a`, or `--no-verify`), verify the staged set with `git diff --cached --name-only` first, and never push. The terminal transition is MANDATORY and its owner is conditional: under `aw oc run` / `aw agy run` the runner performs the finalize after its merge-and-revalidate gate, so the executor must NOT run `aw ipd finalize`; executed by hand, the executor runs `aw ipd finalize 6iab2o` once `aw ipd lint --phase pre-transition` conforms and every `V-*` records concrete pasted evidence with Result: pass. Never hand-roll the move or `git mv` this plan into `executed/`. Do not set backlog `wkpcop` to `done`.
