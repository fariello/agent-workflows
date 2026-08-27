# IPD: Spec id6 filenames: producer emits id6-clustered names, checker cutover grandfathers legacy, and an id6-minting rename converts legacy specs on demand

- Date: 2026-08-26
- Kind: child
- Concern: Specs are the only faceted artifact type that does NOT carry the stable `<id6>` in its filename. They use the legacy `YYYYMMDD-HHMM-NN-<slug>.spec.md` (time-based) form while plans/backlog/research use the uniform grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`. This is inconsistent with the "id6 in every filename" intent. Three code decisions cause it: (1) there is NO spec producer at all - `aw specs` has only set/note/check/migrate, so spec names are hand/workflow-authored (cli.py specs subparser; agent_workflows/specs.py has no filename builder); (2) the checker deliberately does not name-check specs - `check_engine.py` SUPPORTED["specs"] = ("content",) omits "names", so `check.name-nonconformant` never runs on specs (aw check specs = 0 naming findings); (3) the naming-grammar spec `20260817-2147-01` line 56 grandfathered specs ("ALREADY the convention (no change)"), addressing only the `.spec.md` suffix and never mandating the id6 backfill, and a companion spec kept specs flat to avoid breaking `YYYYMMDD-HHMM-NN` citation paths. Additionally, 19 of 21 specs carry NO id6 anywhere (not filename, not `- Id:` metadata), and the existing `aw rename specs` cannot inject one (its `_LEGACY_TIMESTAMP_RE` branch in artifact_rename.py:92-100 rebuilds the HHMM form with no id6 slot). Origin: incident review 2026-08-26.
- Scope: Make id6-in-filename the convention for specs GOING FORWARD while GRANDFATHERING existing legacy specs, AND deliver a rename capability so the maintainer or a user can convert a legacy spec to the id6-clustered form ON DEMAND (not forced). Three deliverables: (1) a new spec PRODUCER (`aw specs new`/`scaffold`) that mints an id6 via `artifact_core.generate_id6` and emits `build_clustered_name(..., artifact_type="spec")`, writing the id6 into both the filename and the `- Id:` metadata; (2) a checker CUTOVER: enable spec naming with a per-repo cutover date so a spec created at/after the cutover must be id6-clustered while pre-cutover legacy specs remain conformant (grandfathered, advisory at most) - this requires a per-type strictness option on the shared normalizer predicate (`normalize_plan_names.is_conformant`) rather than dropping the legacy `_NEW_RE`, which other types still rely on; (3) an id6-MINTING RENAME: extend `aw rename specs` (or a dedicated `--to-id6`/`--mint-id6` mode) so a legacy `YYYYMMDD-HHMM-NN-<slug>.spec.md` can be converted to `YYYYMMDD-<id6>-NN-<id6>-<slug>.spec.md` (standalone specs use their own id6 as setid, NN=01 per the grammar) - mint the id6, write `- Id:`, git mv, and rewrite repo-wide references (guarding full-path citations). The 2 specs that already carry `- Id:` (the aw-run spec `25kzda` at `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, and the research-lifecycle spec `5tapom` at `.aw/records/specs/20260824-2000-01-research-lifecycle-reliability.spec.md`) are cheap pilots. Does NOT mass-rename the 19 legacy specs (that is a separate, deliberate migration run using this new capability); this IPD delivers the tooling + forward default only.
- Scope-Paths: agent_workflows/specs.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/artifact_naming.py, agent_workflows/artifact_rename.py, agent_workflows/check_engine.py, .aw/system/workflows/setup-repo/tools/normalize_plan_names.py, tests/, AGENTS.md, .aw/records/specs/
- Status: to-review
- Set: specid6
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: ha55fi

## Workflow history
- 2026-08-26 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): status set to to-review

- 2026-08-26 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Bring specs into the uniform id6-in-filename grammar going forward (a real spec producer + a grandfathering checker cutover) while giving the maintainer/user a tooled, opt-in way to convert existing legacy specs to the id6-clustered form on demand. Legacy specs stay valid until deliberately renamed; new specs are id6-clustered by construction.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Forward-conforming spec producer

- [ ] E-01 Add a spec producer `aw specs new` (and/or `scaffold`) in specs.py + cli.py + command_surface.py that mints a fresh id6 via `artifact_core.generate_id6` (collision-checked against the existing spec id6 set), writes a conformant spec skeleton with the id6 in the `- Id:` metadata, and derives the filename via `artifact_naming.build_clustered_name(date, set_id=<id6>, order=1, id6=<id6>, slug=<slug>, artifact_type="spec")` (standalone spec: setid == its own id6, NN=01). Dry-run/preview by default; `--apply` writes. No other spec verb changes behavior.
  - Depends on: none
  - Expected outcome: `aw specs new --title ... --slug ...` previews then (with --apply) writes `.aw/records/specs/YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md` carrying `- Id: <id6>`, lints/`aw specs check` clean.
  - Execution state: pending

### Task group 2: Grandfathering checker cutover

- [ ] E-02 Add a per-type strictness option to the shared predicate `normalize_plan_names.is_conformant(filename, expected_type, require_id6=False)` (default preserves current behavior for every type; when `require_id6=True` the legacy `_NEW_RE` HHMM form is NOT accepted, only the clustered id6 form). Do NOT drop `_NEW_RE`; other types and pre-cutover artifacts still rely on it.
  - Depends on: none
  - Expected outcome: unit tests show `is_conformant(legacy_spec, "spec")` is True (default) and `is_conformant(legacy_spec, "spec", require_id6=True)` is False, while the clustered form is True in both.
  - Execution state: pending

- [ ] E-03 Enable spec name-checking with a grandfather cutover: add `"names"` to `check_engine.SUPPORTED["specs"]`, and make `check_names` pass `require_id6=True` ONLY for specs whose filename date is at/after a single configured spec-id6 cutover date; pre-cutover specs stay conformant (advisory `grandfathered` at most, never mass-fail). NOTE (verified at author time): `check_engine.py` has NO existing cutover-date mechanism to reuse (a repo-wide search for a name-conformance cutover found none; the only `cutover` usages are unrelated command-name removals). Therefore the DEFAULT and expected implementation is a single configured cutover date compared against the spec's filename date; record that constant (and its value) as a DECISION in this plan when chosen (see OQ-01). Do NOT block execution hunting for a pre-existing cutover-policy object that does not exist.
  - Depends on: E-02
  - Expected outcome: `aw check specs` still reports 0 name failures for all 21 existing (pre-cutover) specs - INCLUDING the newest one dated `20260826` (the aw-run spec), which must be grandfathered by the strictly-after cutover boundary (2026-08-27) per OQ-01; a synthetic post-cutover legacy-named spec (filename date >= cutover) is flagged `check.name-nonconformant` with an `aw rename specs ... --to-id6` recovery command; a synthetic pre-cutover legacy-named spec is NOT flagged (boundary test).
  - Execution state: pending

### Task group 3: On-demand id6-minting rename

- [ ] E-04 Extend the rename engine: add an id6-minting conversion mode (e.g. `aw rename specs <legacy> --to-id6`) so `compute_target_name` (artifact_rename.py:67) recognizes the legacy `_LEGACY_TIMESTAMP_RE` spec form and, in this mode, mints an id6 (`artifact_core.generate_id6` over existing spec ids), returns the clustered `build_clustered_name(..., artifact_type="spec")` name, AND signals the caller to inject `- Id: <id6>` into the file metadata during the rename transaction. IMPLEMENTATION NOTE (verified at author time): `run_rename_generic` (artifact_rename.py:271) ALREADY writes front-matter during a rename via `_update_frontmatter_metadata` (artifact_rename.py:364-367, currently for `set`/`order`); extend that SAME existing hook to also write `- Id:` when the `--to-id6` mode mints one, so the mint + name + metadata write remain ONE atomic transaction (no new transaction machinery, no separate E-item). Keep the default (non-`--to-id6`) rename behavior unchanged (HHMM-preserving). A spec that already has an `- Id:` reuses it rather than minting.
  - Depends on: none
  - Expected outcome: `aw rename specs <legacy-spec> --to-id6` previews the new clustered name + the `- Id:` injection; `--apply` git-mv's the file, writes `- Id:`, and reports the change. Idempotent on an already-id6 spec (reuses its id6).
  - Execution state: pending

- [ ] E-05 Ensure the `--to-id6` rename rewrites repo-wide references to the old spec path/stem (reusing `plan_reference_rewrites`), covering full-path citations; where a full-path citation cannot be auto-rewritten, report it fail-loud so the operator can fix it. Pilot on the 2 already-id6 specs (the aw-run spec `25kzda` and the research-lifecycle spec `5tapom`) as a preview-only demonstration in the test/validation, NOT an in-run mass rename. A spec that already carries `- Id:` MUST reuse that id6 (no re-mint); this is the idempotence property verified in V-04/V-05.
  - Depends on: E-04
  - Expected outcome: a preview of `aw rename specs 25kzda --to-id6` (the aw-run spec) lists the new name (reusing its existing id6 `25kzda`, not minting a new one) and every reference that would be rewritten; a test asserts references to a renamed fixture spec are updated and any unrewritable full-path citation is surfaced.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- id6 primitive + generator: `artifact_core.ID6_ALPHABET` (base36 lowercase), `artifact_core.is_valid_id6`, `artifact_core.generate_id6(existing, ...)` (collision-checked). Research/plans already consume it.
- Uniform-name formatter: `artifact_naming.build_clustered_name(..., artifact_type=...)` (artifact_naming.py:126) requires an id6 and emits `.<type>.md`; `ARTIFACT_TYPE_FACETS` gates the facet; a standalone artifact uses its own id6 as the setid with NN=01 (per `20260817-2147-01` lines 41-43).
- Naming predicate: `normalize_plan_names.is_conformant(filename, expected_type)` (`.aw/system/workflows/setup-repo/tools/normalize_plan_names.py:206`) is the SHARED authority; `_NEW_RE` accepts the legacy HHMM form for all types, `_CLUSTERED_RE` is the id6 form. Changing it affects every type - hence the additive `require_id6` flag, not a regex removal.
- Checker capability table: `check_engine.SUPPORTED` (check_engine.py:18) - specs currently `("content",)` (no `"names"`); `check_names` (check_engine.py:118) emits `check.name-nonconformant`.
- Rename engine: `artifact_rename.compute_target_name` (artifact_rename.py:67) branches by name shape; the `_LEGACY_TIMESTAMP_RE` branch (92-100) is where the id6-minting mode plugs in; `run_rename_generic` (271) does git-mv + ref-rewrite + rename-ledger; specs are NOT auto-indexed (no spec index exists).
- No spec index/manifest exists (unlike plans/research); the sidecar (`specs.py:127`) only activates once a spec has an id6.
- User-facing prose avoids em/en dashes; this internal IPD is exempt.

## Findings

- The id6 exclusion for specs is deliberate and tripartite (no producer / checker omits `"names"` / naming spec grandfathered specs), documented at `artifact_naming.py:32-36` ("id6-less legacy types ... this module does NOT add an id6 to those types") and `20260817-2147-01` line 56.
- 19 of 21 specs have no id6 at all; 2 already carry `- Id:` but still use legacy filenames (the cheap pilots): the aw-run spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) and the research-lifecycle spec `5tapom` (`20260824-2000-01-research-lifecycle-reliability.spec.md`). NOTE: `25kzda` is the aw-run spec, not the research-lifecycle spec.
- The existing `aw rename specs` cannot convert legacy -> id6 (no id6 slot in the `_LEGACY_TIMESTAMP_RE` rebuild), so a new minting mode is required, not just a config toggle.
- Enabling the checker is one line, but ENFORCING id6 needs the shared-predicate `require_id6` flag; enforcing only post-cutover keeps the 21 existing specs green.

## Proposed changes (ordered, validatable)

1. `specs.py`/`cli.py`/`command_surface.py`: `aw specs new` producer minting id6 + clustered filename + `- Id:` metadata. (E-01)
2. `normalize_plan_names.py`: additive `require_id6` param on `is_conformant`. (E-02)
3. `check_engine.py`: `SUPPORTED["specs"]` gains `"names"`; `check_names` applies `require_id6=True` only post-cutover (grandfather legacy). (E-03)
4. `artifact_rename.py` (+ `artifact_naming.py` as needed): `--to-id6` minting rename mode that converts a legacy spec to the clustered form and injects `- Id:`. (E-04)
5. `--to-id6` reference rewrites, fail-loud on unrewritable full-path citations; preview pilot on the 2 id6-bearing specs. (E-05)

## Deferred / out of scope (with reason)

- Mass-renaming the 19 truly-legacy specs: deliberately deferred to a SEPARATE migration run using the E-04/E-05 tooling this IPD delivers, so the reference-rewrite blast radius is handled as its own reviewed change, not bundled here.
- Building a spec INDEX/manifest (like plans/research have): out of scope; specs have no index today and this IPD does not introduce one.
- Extending id6-in-filename to prompts/roadmaps/walkthroughs/releases: separate types, separate decision; not in scope.

## Scope check

- Over-scope: none.
- Under-scope: none. The Scope-Paths cover the producer (specs.py/cli.py/command_surface.py), the predicate (normalize_plan_names.py), the checker (check_engine.py), the rename engine (artifact_rename.py + artifact_naming.py), tests, the AGENTS.md/naming-spec doc sync, and the specs tree for the pilot.

## Required tests / validation

`python -m pytest tests/ -p no:randomly` green including new tests for: the spec producer (mints id6, clustered filename, `- Id:` present, lints clean); `is_conformant` require_id6 matrix; `aw check specs` grandfathering (all 21 existing specs pass, including the newest `20260826`-dated aw-run spec at the cutover boundary; a synthetic post-cutover legacy spec fails with the rename recovery; a pre-cutover-boundary spec passes); the `--to-id6` minting rename (previews name + `- Id:` injection, `--apply` git-mv + metadata write, idempotent on an id6 spec, reference rewrite + fail-loud on unrewritable citation). `aw ipd lint` on this plan clean; `aw check all --agent` adds no new findings to the existing baseline for the 21 legacy specs; `aw sanitize --agent` clean.

## Spec / documentation sync

Update `20260817-2147-01-uniform-artifact-naming-grammar.spec.md` Section 2.1 line 56 (replace "ALREADY the convention (no change)" with the id6-forward + grandfather rule and the `--to-id6` conversion path) via `aw specs note`; update the `artifact_naming.py:32-36` "id6-less legacy types" note; update AGENTS.md naming grammar prose to state specs now carry id6 going forward with legacy grandfathered.

## Open questions

### OQ-01: Cutover marker source for spec grandfathering

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us)
- Resolution or deferral rationale: E-03 needs a cutover boundary to decide which specs must be id6-clustered. RESOLVED from repository evidence during plan-review: a repo-wide search confirmed `check_engine.py` (and the naming tooling) has NO existing name-conformance cutover-date mechanism to reuse - the only `cutover` usages in the codebase are unrelated removed-command-name notes. Therefore E-03 uses a single configured spec-id6 cutover date compared against the spec's FILENAME date (the deterministic, testable path). DECISION to record at execution: set the cutover date to 2026-08-27 (the day AFTER this plan's Date). RATIONALE (important edge case): the newest existing spec, the aw-run spec `25kzda`, has filename date `20260826` - exactly this plan's Date. If the cutover were 2026-08-26 with `require_id6` triggered at `date >= cutover`, that legacy-named spec would be flagged nonconformant, breaking the "all 21 existing specs stay green" invariant (V-03). Setting the cutover strictly AFTER the newest existing spec date (2026-08-27) grandfathers ALL 21 existing specs and forces id6-clustering only on specs created from the day after this plan lands. Store it as a single named module constant with a comment citing this OQ. Non-blocking and fully deterministic; no human input required.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw specs new --title ... --slug ... --apply` output and the created file's `- Id:` line + filename; show the filename matches `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md` and `aw specs check` on it is clean. Runner output for the producer unit test.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: unit test output for the `is_conformant` matrix: legacy spec True by default, False with `require_id6=True`; clustered spec True in both; other types' default behavior unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `aw check specs --agent` showing ZERO name failures across all 21 existing (pre-cutover) specs (explicitly confirm the newest, `20260826`-dated aw-run spec is among the zero-failure set - the boundary case per OQ-01); a test with a synthetic post-cutover legacy-named spec showing `check.name-nonconformant` with an `aw rename specs ... --to-id6` recovery command; a boundary test asserting a spec dated exactly the cutover minus one day is NOT flagged and a spec dated exactly the cutover IS flagged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `aw rename specs <legacy-fixture> --to-id6` preview (new clustered name + `- Id:` injection shown), then `--apply` result (git mv + metadata write); a test asserting idempotence on an already-id6 spec (reuses its id6, no re-mint).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: a test showing references to a renamed fixture spec are rewritten and an unrewritable full-path citation is surfaced fail-loud; a preview-only `aw rename specs 25kzda --to-id6` (the aw-run spec; reuses its existing id6, no re-mint) listing the references it would rewrite (NOT applied in-run).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: touch ONLY the declared `Scope-Paths` plus this plan's own file. Deliver the forward-conforming producer, the grandfathering checker cutover, and the on-demand id6-minting rename; do NOT mass-rename the 19 legacy specs in this run (that is a separate migration using this tooling). Honesty rule (hard MUST): when reporting tests/validation passed, paste the ACTUAL runner output; never claim success not run. Commit only files this plan changes, path-scoped; never `git add -A`; never push. On completion perform the terminal transition via `aw ipd begin <plan> --actor <agent/model>` then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`; do NOT hand-edit the terminal transition. This plan awaits `/plan-review` and explicit human approval (`Status: approved`) before execution.
