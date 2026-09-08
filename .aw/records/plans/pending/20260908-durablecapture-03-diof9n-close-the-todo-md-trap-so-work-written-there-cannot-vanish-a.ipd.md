# IPD: Close the TODO.md trap so work written there cannot vanish and repoint the two spec gates that resolve to it

- Date: 2026-09-08
- Kind: child
- Concern: `TODO.md` is functionally retired but structurally still load-bearing, which is the worst of both worlds: it is READ by the artifact scan and then SILENTLY DISCARDED, so anything written there is invisible with no warning that it was dropped. VERIFIED AT HEAD `a2e0438a` by importing the modules. `artifact_core.SCAN_ROOTS` lists `"TODO.md"` (at `:158`), so `iter_scan_files` yields it. `attention._classify_tree("TODO.md")` returns `None`, because no `TreePolicy` root covers a repository-root file. And `attention.scan`'s `pol is None` branch appends `attention.unclassified-tree` drift ONLY when the path starts with `.agents/`, so a root-level file is `continue`d with no violation recorded. Measured the same silent drop for `DECISIONS.md`, `README.md` and `ARCHITECTURE.md`.
  THIS WAS PREDICTED VERBATIM BY THE CONTROLLING SPEC AND SHIPPED ANYWAY. `.aw/records/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md:102-103` reads: "NOTE: `SCAN_ROOTS` already lists `TODO.md`, but `_classify_tree` returns None for it - it has no `TreePolicy` root - which is exactly why TODO.md is read-but-ignored today; PR-003." Known, documented, still live.
  THE FILE HOLDS ZERO WORK ITEMS. 31 lines, all of it a pointer stub plus a deliberate `## Notes` section: `:3-8` says committed and candidate backlog work "now lives in the tracked, attention-visible BACKLOG TREE, not in this file", `:14` keeps `## Notes` as "durable context (Tier-3: not lifecycle-tracked work)", and `:25-31` records the migration provenance (IPD `crv40v`, 2026-08-13). So the risk is not lost content today; it is that the file still LOOKS like a place to record work and is guaranteed to lose it.
  TWO DEFERRED SPECS GATE ON IT AND BOTH GATES ARE DANGLING IN SUBSTANCE. `.aw/records/specs/20260725-0957-01-external-delivery-and-skills.spec.md:5-6` and `.aw/records/specs/20260726-1239-01-clean-delta-and-tracking-modes.spec.md:5-6` each carry `- Gate-Kind: artifact` and `- Gate-Ref: TODO.md`. Both read `- Status: deferred`, dated 2026-07-25 and 2026-07-26. They VALIDATE (the file exists) while resolving to a file whose items were migrated out from under them in August 2026, so they pass in form and mean nothing in substance.
- Scope: Eliminate the silently-scanned-and-discarded state for `TODO.md` (either remove it from `SCAN_ROOTS` or give it a policy so a write is reported as drift, never both-scanned-and-dropped), repoint the two deferred spec gates at carriers that can actually express what they wait for, fix the `whatnext` workflow pointer, and state the deprecation plainly where agents read it. EXCLUDES the releases scan root and the reviews policy (sibling backlog `v7u6vm`, whose plan is authored alongside this one and edits the same `SCAN_ROOTS` tuple); excludes the durable-carrier predicate (pending plan `rnkqrc`, from `jys5dp`); excludes DELETING `TODO.md`, since its `## Notes` section is deliberate Tier-3 durable context.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/attention_contract.py, agent_workflows/engine.py, TODO.md, AGENTS.md, .aw/system/workflows/whatnext/whatnext.md, .aw/records/specs/20260725-0957-01-external-delivery-and-skills.spec.md, .aw/records/specs/20260726-1239-01-clean-delta-and-tracking-modes.spec.md, tests/test_artifact_core.py
- Item-Dependencies: none
- Status: to-review
- Set: durablecapture
- Order: 3
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: diof9n
- From-Backlog: ld08f1

## Workflow history

- 2026-09-08 amended (opencode/its_direct/pt3-claude-opus-5-1m-us): CORRECTED A FALSE MECHANISM CLAIM this plan asserted in four places, found by the maintainer. It said a hand edit to `AGENTS.md` "would be overwritten on the next install" and would be "silently reverted". THAT IS FALSE FOR THE OBVIOUS PLACE SOMEONE WOULD PUT IT. Measured by calling `engine.merge_aw_block` in a throwaway repo: content OUTSIDE the `<!-- aw:block -->` markers is PRESERVED across a refresh (action `refreshed`, with a preamble line, a trailing section and a hand-written `TODO.md` sentence all surviving), which the merge docstring states as "preserving foreign before/after text" and which THIS repository already relies on by design at `AGENTS.md:186-190`. INSIDE the block the behavior is manifest-dependent: an edited section is PRESERVED as user drift when a recorded per-section hash exists (`engine.py:1721`) and is silently rewritten when none does (measured with `manifest=None`). `install_agents_pointer` DOES pass a manifest (`engine.py:2468-2473`), though `.aw/system/managed-sections.json` records ZERO managed sections for this repo today, so the hash is not yet established here. E-05's SITE IS UNCHANGED AND STILL CORRECT; only its JUSTIFICATION changed, from a false reversion claim to the real reason, which is REACH: a hand edit states the deprecation for this repo only and for no managed target repo, which fails the item's own requirement that it be stated "where agents will read it". Changes: F-7 rewritten with the measurement and its evidence column; the Step 0 convention corrected; the Concern paragraph now states what would and would not be reverted; E-05 forbids repeating the reversion claim in a comment or commit message; and V-05 additionally requires proving `AGENTS.md:186-190` survived byte-unchanged, so the corrected premise is the one demonstrated. HONEST LIMIT: this amendment was made BEFORE any review, so no review coverage is claimed or invalidated. `aw ipd lint` conforming after the edit.
- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `ld08f1`. The item carries no `- Blocks-Release:` so none is inherited or invented.
  ALL THREE DEFECTS RE-VERIFIED at HEAD `a2e0438a` by importing the modules and reading the files, not by trusting the item: the scan-then-discard path reproduced exactly (including the `.agents/`-only drift condition that makes it silent), both spec gates still read `Gate-Kind: artifact` / `Gate-Ref: TODO.md` on specs still `deferred` and still untouched since July, and the `whatnext` workflow still names `TODO.md` as a survey source in NINE places, not one.
  ONE CITATION IN THE ITEM IS WRONG AND IT CHANGES THE COORDINATION INSTRUCTION. The item says finding F-6 is recorded in "pending IPD `i6015i`" and to "cross-check that item before touching the workflow so the two fixes do not collide". `i6015i` is EXECUTED, not pending, and it did NOT fix the pointer: it DEFERRED the rewiring explicitly ("The workflow would benefit (F-6), but it is a prose workflow with its own review path") and its own execution contract says "Do NOT edit spec `25kzda` ... or the `whatnext` workflow". So there is no collision to avoid and the work is unowned; the coordination the item asked for resolves to "that plan deliberately left this to someone else".
  THE ITEM UNDERSTATES THE WORKFLOW EDIT, which is why E-04 is scoped carefully. `TODO.md` appears at NINE places in `whatnext.md`, and most are not a "source" pointer at all: they instruct the workflow to WRITE findings INTO `TODO.md` (`:11`, `:119-121`, `:125`, `:145`, `:150`) and carry an untrusted-content rule about what may be written there (`:27`, `:133`). So this is not a one-line pointer swap; it is redirecting the workflow's WRITE target, which is a behavior change to an agent-facing workflow and needs its own care.
  THE `AGENTS.md` HALF IS A GENERATOR EDIT, AND THE REASON IS REACH RATHER THAN REVERSION. The sentence the item quotes ("Do NOT keep committed backlog only in prose (e.g. `TODO.md`)") lives in `agent_workflows/engine.py:1151`, which renders the managed block INSTALLED INTO EVERY TARGET REPOSITORY. So an edit to this repository's `AGENTS.md` alone would state the deprecation for THIS repo and for no managed repo, which fails the item's own requirement that it be stated "where agents will read it". E-05 therefore edits the generator.
  BE PRECISE ABOUT WHAT WOULD AND WOULD NOT BE REVERTED, because an earlier revision of this plan asserted a stronger claim that is FALSE and would have misled an executor. Measured 2026-09-08 by calling `engine.merge_aw_block` in a throwaway repo: content OUTSIDE the `<!-- aw:block -->` / `<!-- /aw:block -->` markers is PRESERVED across a refresh (action `refreshed`, with a preamble line, a trailing section, and a hand-written `TODO.md` sentence all surviving), which the merge docstring states as "preserving foreign before/after text" and which this repository already relies on: `AGENTS.md:186-190` holds a repo-local section whose own text says it "sits deliberately BELOW the `<!-- /aw:block -->` marker, outside every managed block". INSIDE the block the answer depends on the manifest: with a per-section manifest an edited section is PRESERVED as user drift (`engine.py:1721`, "on-disk body differs from OUR recorded hash for that slug -> user drift -> preserve the on-disk section body"), and with NO manifest the section is silently rewritten (measured: a hand edit inside the block did not survive). `install_agents_pointer` DOES pass `manifest=plan.manifest` (`engine.py:2468-2473`), so the drift-preserving path is the one a real install takes, though `.aw/system/managed-sections.json` currently records ZERO managed sections for this repo, so the hash is not yet established here. NONE of that changes E-05's site; it changes only the justification, and the honest justification is reach.
  SIBLING BOUNDARY, and it is a real hazard rather than a note: this plan and `v7u6vm`'s plan (`m867ox`) BOTH edit `artifact_core.SCAN_ROOTS`. That one ADDS a releases entry; this one may REMOVE the `TODO.md` entry. They must not be executed concurrently against the same tuple, and each declares the other in its fence.

## Goal

Make it impossible to write work into `TODO.md` and have it silently vanish, and make the two specs that wait on it wait on something that can actually happen.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: eliminate the scanned-and-discarded state

- [ ] E-01 DECIDE `TODO.md`'s SCAN FATE AND RECORD THE DECISION BEFORE CHANGING ANYTHING. Two acceptable answers and one forbidden state. EITHER remove `"TODO.md"` from `SCAN_ROOTS` so it is honestly out of scope, OR give it a `TreePolicy` so anything written there is at least reported as unclassified drift. THE ONE OPTION TO ELIMINATE is the current both-scanned-and-silently-dropped state.
  DO NOT DELETE THE FILE. Its `## Notes` section is deliberate Tier-3 durable context (`TODO.md:14`) recording the agent-comms formalization and the `crv40v` migration provenance, and the item says plainly that deleting it is probably wrong. The goal is that nobody can write WORK there and have it vanish, not that the file disappears.
  MEASURE WHAT ELSE READS `SCAN_ROOTS` BEFORE REMOVING AN ENTRY. `iter_scan_files` feeds the reference tools and the dangling detector, not only the attention view (the comment above `SCAN_ROOTS` says so). If `TODO.md` is removed, a reference FROM another artifact TO `TODO.md` may stop resolving, or a dangling-reference check may start or stop firing. Measure both directions and report; a decision that improves the attention view and breaks the reference checker is not an improvement.
  IF YOU CHOOSE THE POLICY OPTION, note the mechanical obstacle rather than discovering it mid-edit: every existing `TreePolicy` root is a DIRECTORY under `.agents/`, and `_classify_tree` matches by path prefix after rewriting `.aw/records/<type>` to `.agents/<type>`. A repository-root FILE does not fit that shape, so a policy for `TODO.md` either needs the matcher to handle a file root or needs the drift condition widened, which is the change sibling plan `m867ox` explicitly deferred as too broad. Prefer removal unless you can show the policy path is small.
  - Depends on: none
  - Expected outcome: `TODO.md` is either absent from `SCAN_ROOTS` or covered by a policy; the both-and state is gone; the effect on the reference tools and the dangling detector measured in BOTH directions and reported; the file itself not deleted.
  - Execution state: pending

- [ ] E-02 MAKE THE FILE ITSELF REFUSE WORK, in prose, so the structural fix is matched by what a reader sees. `TODO.md:3-8` already says work lives in the backlog tree, but it reads as a migration note rather than a prohibition, and `:14` invites content into `## Notes`.
  STATE PLAINLY THAT WORK WRITTEN HERE IS NOT TRACKED and name the correct destination (`aw backlog new`). Keep the `## Notes` section and its Tier-3 framing. This is user-facing prose you are authoring, so it must contain NO em or en dashes.
  DO NOT REWRITE THE `## Notes` CONTENT. The agent-comms paragraph and the `crv40v` migration provenance are durable records; adding a header sentence is in scope, editing those paragraphs is not.
  - Depends on: E-01
  - Expected outcome: `TODO.md` states plainly that work written there is untracked and names `aw backlog new`; `## Notes` content byte-unchanged; no em or en dashes in the added prose.
  - Execution state: pending

### Task group 2: repoint the two dangling gates

- [ ] E-03 REPOINT BOTH DEFERRED SPEC GATES at carriers that can express what they wait for, and do NOT simply delete the gates. `.aw/records/specs/20260725-0957-01-external-delivery-and-skills.spec.md:5-6` and `.aw/records/specs/20260726-1239-01-clean-delta-and-tracking-modes.spec.md:5-6` each carry `Gate-Kind: artifact` / `Gate-Ref: TODO.md`.
  A `deferred` SPEC MUST CARRY A TYPED GATE. That is the specs contract (`AGENTS.md`: "A `deferred` spec MUST carry a typed `Gate-Kind:`/`Gate-Ref:`"), so removing the gate would make the spec non-conforming. Repoint or re-status; never strip.
  READ EACH SPEC AND DETERMINE WHAT IT IS ACTUALLY WAITING FOR before choosing a target. A gate pointing at a file that can no longer contain the awaited thing is the defect; pointing it at a DIFFERENT arbitrary artifact would reproduce it. If the awaited thing has no carrier, the honest fix is to CREATE one (a backlog item) and gate on that. Note this plan may therefore need to file a backlog item, which is a records write and must go through `aw backlog new` rather than a hand-authored file.
  ALSO JUDGE WHETHER EITHER SPEC SHOULD STILL BE `deferred` after six weeks of silence, which the item asks for explicitly. Both are dated late July 2026 and untouched since 2026-08-08. If a spec should be `parked` or `superseded` instead, that is a status change through `aw specs set` with a message, and it needs the maintainer's call rather than an executor's: raise it, do not decide it.
  DO NOT TOUCH ANY OTHER FIELD OF EITHER SPEC. These are `deferred` design contracts; this plan fixes a dangling gate reference, not their content.
  - Depends on: none
  - Expected outcome: both gates resolve to a carrier that can express the awaited condition, with the reasoning recorded per spec; no gate deleted; `aw check specs` clean; any status-change recommendation raised to the maintainer rather than applied.
  - Execution state: pending

### Task group 3: the two remaining pointers

- [ ] E-04 FIX THE `whatnext` WORKFLOW, and treat it as a WRITE-TARGET change rather than a pointer swap. `TODO.md` appears at NINE places in `.aw/system/workflows/whatnext/whatnext.md`: as a survey SOURCE (`:64`, `:119`), and as the WRITE DESTINATION for uncaptured findings (`:11`, `:120-121`, `:125`, `:145`, `:150`), plus two untrusted-content rules about what may be written there (`:27`, `:133`).
  THE WRITE PATH IS THE DEFECT, NOT THE READ PATH. A workflow that appends a finding to `TODO.md` writes it where the attention view cannot see it, which is exactly the trap this plan closes. Redirect those writes to `aw backlog new`, which is the surface `AGENTS.md` already names for committed lightweight work.
  PRESERVE THE UNTRUSTED-CONTENT RULES. `:27` and `:133` forbid writing a comms payload or other untrusted content into the destination. That rule must survive the redirect, and it matters MORE once the destination is a tracked records tree, since an adopted record is permanent. Do not drop it while moving the target.
  KEEP THE EXPLICIT-CONFIRMATION GATE. `:11` and `:145` require the human's explicit confirmation before the workflow adds anything. Preserve it.
  `i6015i` DELIBERATELY LEFT THIS ALONE, so there is no collision: it recorded F-6, deferred the rewiring as "a prose workflow with its own review path", and forbade its own executor from touching this file. This plan is the follow-through.
  - Depends on: E-01
  - Expected outcome: the workflow no longer writes findings into `TODO.md`; the untrusted-content rules and the explicit-confirmation gate survive verbatim in substance; every one of the nine occurrences accounted for with its disposition stated.
  - Execution state: pending

- [ ] E-05 STATE THE DEPRECATION WHERE AGENTS ACTUALLY READ IT, WHICH IS THE GENERATOR AND NOT `AGENTS.md`. The sentence the item quotes lives at `agent_workflows/engine.py:1151` ("NOT keep committed backlog only in prose (e.g. `TODO.md`), where the attention view cannot ..."), inside the managed block `engine.py` installs into every repository.
  EDIT THE GENERATOR, THEN REGENERATE, AND THE REASON IS REACH. An edit to this repository's `AGENTS.md` alone would state the deprecation for THIS repo only and for no managed target repo, which fails the item's requirement that it be stated "where agents will read it". The item's framing ("AGENTS.md currently never names TODO.md as deprecated") is right about the symptom and the generator is the correct site.
  DO NOT JUSTIFY THIS WITH "A HAND EDIT WOULD BE REVERTED", WHICH IS FALSE FOR THE OBVIOUS PLACE SOMEONE WOULD PUT IT. Text OUTSIDE the `<!-- aw:block -->` markers survives a refresh (measured; see F-7), and this repository already depends on that at `AGENTS.md:186-190`. If you write the reversion claim into a comment or a commit message you will be repeating an error this plan already corrected.
  SAY IT PLAINLY, as the item asks: the current wording is an oblique instruction not to keep backlog in prose. State that `TODO.md` is deprecated as a work surface and name the destination. This is user-facing prose, so NO em or en dashes.
  VERIFY THE REGENERATION IS IDEMPOTENT AND CHANGES NOTHING ELSE. The managed block is installed by machinery with its own markers; a regeneration that reflows unrelated text would produce a large diff in every managed repo. Diff `AGENTS.md` and show the change is confined to the intended sentence.
  - Depends on: E-01
  - Expected outcome: `engine.py`'s managed-block text names `TODO.md` as deprecated as a work surface and names the destination; `AGENTS.md` regenerated with a diff confined to that sentence; no em or en dashes added.
  - Execution state: pending

- [ ] E-06 PIN THE DECISION WITH A TEST so the both-and state cannot return. Whatever E-01 decided, assert it: if `TODO.md` was removed from `SCAN_ROOTS`, assert it is absent; if it was given a policy, assert `_classify_tree("TODO.md")` returns non-`None`.
  ASSERT THE INVARIANT, NOT THE CHOICE. The durable property is that no `SCAN_ROOTS` entry classifies to `None` while being silently dropped. Prefer a test expressing THAT over one pinning the specific membership, because the invariant catches the next root added without a policy. Note the other three root docs (`DECISIONS.md`, `README.md`, `ARCHITECTURE.md`) are in the SAME state, so an invariant test will fail on them too: decide and state whether they are exempt by design (they are documentation, not work surfaces) or whether they are the same bug, and if exempt, encode the exemption explicitly rather than special-casing quietly.
  `tests/test_artifact_core.py` ALREADY PINS THREE `SCAN_ROOTS` MEMBERS (`.agents/plans`, `.agents/docs`, `DECISIONS.md`), so it is the established home and one of those assertions may need updating if E-01 removes an entry. Do not delete an existing assertion to make a new one pass.
  - Depends on: E-01
  - Expected outcome: a test pinning E-01's decision, preferably as the no-silently-dropped invariant with the three root docs' exemption stated explicitly; existing `SCAN_ROOTS` assertions preserved or updated deliberately.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE DEFECT WAS PREDICTED IN THE CONTROLLING SPEC AND SHIPPED ANYWAY. `.aw/records/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md:102-103` names this exact mechanism, which is why the fix is a decision rather than a discovery.
- THE SILENT DROP IS STRUCTURAL, NOT ACCIDENTAL. `attention.scan` flags `attention.unclassified-tree` only when the path starts with `.agents/`, so a root-level or `.aw/records/`-level file with no policy is dropped with no violation. Sibling plan `m867ox` measured the same mechanism for the releases tree and explicitly DEFERRED widening it as too broad.
- `SCAN_ROOTS` FEEDS MORE THAN THE ATTENTION VIEW. Its own comment says the enumeration is "shared by the reference tools and the dangling detector across areas", so removing an entry has consequences beyond the view.
- A `deferred` SPEC MUST CARRY A TYPED GATE, per the specs contract in `AGENTS.md`. Repoint or re-status; never strip.
- EVERY `TreePolicy` ROOT IS A DIRECTORY UNDER `.agents/`, and `_classify_tree` matches by prefix after rewriting `.aw/records/<type>`. A root-level file does not fit that shape, which is what makes the policy option for `TODO.md` awkward.
- THE MANAGED BLOCK IS GENERATED FROM `engine.py`, SO A HAND EDIT TO `AGENTS.md` REACHES ONLY THIS REPOSITORY. That is the reason to edit the generator. It is NOT true that a hand edit is simply overwritten: text outside the `<!-- aw:block -->` markers is preserved across a refresh (the merge docstring's "preserving foreign before/after text"), and `AGENTS.md:186-190` is a live repo-local section that depends on exactly that. Inside the block, an edited section is preserved as user drift when a per-section manifest hash exists (`engine.py:1721`) and is rewritten when it does not.
- `i6015i` (EXECUTED) DELIBERATELY LEFT THE `whatnext` WORKFLOW ALONE and forbade its own executor from touching it, so the item's warning about a collision resolves to the opposite: the work is unowned.
- USER-FACING PROSE CARRIES NO EM OR EN DASHES. This plan authors prose in `TODO.md`, the managed block, and the workflow, so the rule applies to all three.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `a2e0438a`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `artifact_core.py:158`; `attention._classify_tree`; `attention.scan` | `TODO.md` is in `SCAN_ROOTS`, classifies to `None`, and is dropped with NO drift because the unclassified branch requires a `.agents/` prefix. Anything written there vanishes silently. | `_classify_tree("TODO.md")` -> `None`; read the `pol is None` branch |
| F-2 | MED | attention-tier spec `:102-103` | The spec PREDICTED this verbatim: "SCAN_ROOTS already lists TODO.md, but _classify_tree returns None for it ... which is exactly why TODO.md is read-but-ignored today". | file read |
| F-3 | LOW | `TODO.md` | 31 lines, ZERO work items: a pointer stub plus a deliberate Tier-3 `## Notes` section holding the agent-comms formalization and the `crv40v` migration provenance. So the risk is future loss, not present loss, and deleting the file would destroy durable context. | file read |
| F-4 | MED | both spec files `:5-6` | Two `deferred` specs carry `Gate-Kind: artifact` / `Gate-Ref: TODO.md`, dated 2026-07-25 and 2026-07-26 and untouched since 2026-08-08. They validate in form and mean nothing in substance. | both files read |
| F-5 | MED | `.aw/system/workflows/whatnext/whatnext.md` | `TODO.md` appears NINE times, and most are WRITE instructions (`:11`, `:119-121`, `:125`, `:145`, `:150`), not a survey pointer. The item described it as a source pointer, which understates the edit. | grep with line numbers |
| F-6 | CORRECTION | `.aw/records/plans/executed/20260831-worksequence-01-i6015i-...ipd.md:144`, `:167`, `:766` | THE ITEM'S COORDINATION INSTRUCTION IS BASED ON A WRONG STATUS. `i6015i` is EXECUTED, not pending, and it DEFERRED the workflow rewiring and forbade its own executor from touching the file. So there is no collision and the work is unowned. | that plan's `- Status:`, deferred section, and execution contract |
| F-7 | MED | `agent_workflows/engine.py:1151`; `:1621`, `:1721`, `:2468-2473`; `AGENTS.md:186-190` | The sentence the item wants strengthened is GENERATED from `engine.py`, so a hand edit to this repository's `AGENTS.md` reaches THIS repo only and no managed target repo. That is the reason to edit the generator. CORRECTED AT AUTHORING, because an earlier revision of this plan asserted the stronger and FALSE claim that a hand edit "would be overwritten": text OUTSIDE the `<!-- aw:block -->` markers is PRESERVED across a refresh, which the merge docstring states ("preserving foreign before/after text") and which `AGENTS.md:186-190` already relies on by design. Inside the block the behavior is manifest-dependent: an edited section is preserved as user drift when a recorded hash exists, and silently rewritten when none does. `install_agents_pointer` does pass a manifest, but `.aw/system/managed-sections.json` records zero managed sections for this repo today. | called `engine.merge_aw_block` in a throwaway repo twice: outside-block preamble/trailing/sentence all survived a `refreshed` action; an in-block edit did NOT survive with `manifest=None`. Docstrings at `:1630-1644` and `:1718-1724` read; installer call site read |
| F-8 | MED | `artifact_core.py:156-159` | `DECISIONS.md`, `README.md` and `ARCHITECTURE.md` are in the SAME scanned-then-dropped state as `TODO.md`. So an invariant test will implicate them, and their exemption must be stated rather than special-cased. | `_classify_tree` on each returns `None` |
| F-9 | LOW | `artifact_core.py` comment above `SCAN_ROOTS` | The enumeration is "shared by the reference tools and the dangling detector", so removing an entry reaches more than the attention view and must be measured in both directions. | comment read |
| F-10 | HAZARD | sibling plan `m867ox` | This plan and `m867ox` (from `v7u6vm`) BOTH edit `SCAN_ROOTS`: that one ADDS a releases entry, this one may REMOVE the `TODO.md` entry. They must not execute concurrently against the same tuple. | both plans' Scope-Paths |

## Proposed changes (ordered, validatable)

1. E-01 decides and applies `TODO.md`'s scan fate, measuring the effect on the reference tools and the dangling detector.
2. E-02 makes the file itself say plainly that work written there is untracked.
3. E-03 repoints both deferred spec gates at carriers that can express the awaited condition, creating one if none exists.
4. E-04 redirects the `whatnext` workflow's WRITE target off `TODO.md`, preserving its untrusted-content and confirmation rules.
5. E-05 states the deprecation in the managed-block GENERATOR and regenerates.
6. E-06 pins the decision, preferably as the no-silently-dropped invariant with the root-doc exemption stated.

## Deferred / out of scope (with reason)

- DELETING `TODO.md`. Its `## Notes` section is deliberate Tier-3 durable context and the item says deleting it is probably wrong. The goal is that WORK cannot vanish there.
- THE RELEASES SCAN ROOT AND THE REVIEWS POLICY. Sibling backlog `v7u6vm`, plan `m867ox`, authored alongside this one. Both plans edit `SCAN_ROOTS`, so neither may touch the other's entry.
- WIDENING THE UNCLASSIFIED-FILE DRIFT to fire outside `.agents/`. That would surface this whole class of gap, and is attractive, but it immediately implicates the three other root docs and three untracked `.aw/records/` trees that are in `SCAN_ROOTS` by design. Sibling plan `m867ox` deferred it for the same reason. E-06's invariant closes the specific hazard without that blast radius.
- THE DURABLE-CARRIER PREDICATE. Pending plan `rnkqrc` (from `jys5dp`), which names this item in its deferred section as tracked separately.
- CHANGING EITHER DEFERRED SPEC'S CONTENT OR STATUS. E-03 fixes a dangling gate reference. Whether a spec silent for six weeks should still be `deferred` is raised to the maintainer, not decided here.
- REWIRING `/whatnext` TO CONSUME `aw next -o`. `i6015i` F-6 wanted it and deferred it as a separate concern; this plan only stops the workflow writing into a trap.

## Scope check

- Over-scope: `attention_contract.py` is in scope ONLY if E-01 chooses the policy option. `engine.py` is in scope ONLY for the managed-block sentence. Do NOT touch the releases or reviews entries (sibling `m867ox`), do NOT widen the drift condition, and do NOT edit either spec beyond its gate fields.
- Under-scope: stated rather than left as `none`. After this plan, `DECISIONS.md`, `README.md` and `ARCHITECTURE.md` are STILL scanned and dropped (F-8), exempted by design rather than fixed, and a file under a `.aw/records/` tree with no policy is still dropped silently. Both are named with their reasons.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. `tests/test_artifact_core.py` already pins three `SCAN_ROOTS` members and is the home for E-06. Run `aw check specs` after E-03 and `aw check all` after E-01, since `SCAN_ROOTS` feeds the reference tools and the dangling detector and a removal could change what those report in either direction. Run `aw attention --check` before and after to prove the view's validity did not regress. Paste the `AGENTS.md` diff after E-05 to show the regeneration is confined.

## Spec / documentation sync

THIS PLAN EDITS TWO SPEC FILES and both are DECLARED in `- Scope-Paths:`, which is what makes the amendment visible: the runners announce declared spec edits before a run starts and the finalize scope gate reconciles what was actually changed against what was declared.
WHY, since a spec edit changes the contract every other plan is reviewed against: the two edits are to the `- Gate-Ref:` fields of two `deferred` specs whose gates resolve to a file that can no longer contain the awaited thing. That is a correction to a dangling reference, not a change to either spec's design content, and E-03's fence forbids touching anything else in them.
THE ATTENTION-TIER SPEC (`.aw/records/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md`) PREDICTED this defect at `:102-103` and is NOT declared for editing. Check whether it states `TODO.md`'s scan membership as a REQUIREMENT rather than an observation; if it does, E-01's removal contradicts it and the file must be added to `- Scope-Paths:` before execution. Read it and report which.
Do NOT edit spec `25kzda`'s §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Remove `TODO.md` from `SCAN_ROOTS`, or give it a policy?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because both answers eliminate the forbidden both-and state and E-01 requires the decision be recorded either way. The measured asymmetry favors REMOVAL: every `TreePolicy` root is a directory under `.agents/` and `_classify_tree` matches by prefix, so a repository-root FILE does not fit the shape, and making it fit means either teaching the matcher about file roots or widening the drift condition, which sibling plan `m867ox` deferred as too broad. The argument for a policy is that a write would then be REPORTED as drift rather than merely out of scope, which is strictly more helpful. Decide from the code, and if you remove, E-01 still requires measuring what the reference tools and dangling detector do differently.

### OQ-02: What should the two deferred specs actually gate on?

- Blocking: no
- Status: open
- Owner: this plan's executor for the reading, the maintainer for a status change
- Resolution or deferral rationale: NOT blocking, because E-03 gives a decision procedure (read each spec, determine the awaited condition, repoint at a carrier that can express it, create a backlog item if none exists) that terminates without further input. It is recorded because the answer cannot be known without reading two 6-week-old design specs, and because the honest outcome may be that neither is waiting on anything real any more, which is a re-status decision belonging to the maintainer rather than to this plan. Raise it; do not apply it.

### OQ-03: Are the three other root docs exempt by design or the same bug?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-06 requires the exemption be stated explicitly whichever way it is answered, and this plan's fence already excludes fixing them. Measured, `DECISIONS.md`, `README.md` and `ARCHITECTURE.md` are all in the identical scanned-then-dropped state. The defensible position is that they are DOCUMENTATION rather than work surfaces, so being out of the attention view is correct and their presence in `SCAN_ROOTS` serves the reference tools instead. If that is the answer, encode it as a named exemption so the invariant test is honest rather than quietly special-cased. If any of them is in fact a work surface, that is a finding to report as a new item, not to fix here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: state which option OQ-01 resolved to and why. Paste `SCAN_ROOTS` before and after, and `_classify_tree("TODO.md")` before and after. Paste the BOTH-DIRECTIONS measurement of the reference tools and dangling detector: `aw check all` output before and after with the rule-code counts compared, and a statement of whether any reference TO `TODO.md` from another artifact still resolves. Paste `aw attention --check` before and after. Confirm the file was not deleted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the added prose from `TODO.md`. Paste a diff proving the `## Notes` paragraphs are BYTE-UNCHANGED. Paste a grep of the added lines for em and en dashes, returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: for EACH of the two specs, paste the old and new `- Gate-Kind:`/`- Gate-Ref:` lines and state what the spec is waiting for and why the new carrier can express it. If a backlog item was created, paste the `aw backlog new` output. Paste `aw check specs` clean. Paste a diff proving no other field of either spec changed. State the status recommendation raised to the maintainer, and confirm it was NOT applied.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a table of ALL NINE `TODO.md` occurrences in `whatnext.md` with each one's disposition (redirected, removed, or deliberately kept with a reason). Paste the untrusted-content rules and the explicit-confirmation gate as they now read, showing both survived. Paste the new write destination. Confirm no em or en dashes were added.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the changed text in `engine.py` and the regenerated `AGENTS.md` diff, showing the change is CONFINED to the intended sentence and reflowed nothing else. Paste proof the regeneration is idempotent (run it twice, second run produces no diff). Confirm no em or en dashes. ALSO paste proof the regeneration PRESERVED this repository's out-of-block content, naming `AGENTS.md:186-190` (the repo-local research-prompt section) specifically and showing it byte-unchanged: F-7 records that an earlier revision of this plan wrongly claimed out-of-block text is overwritten, so demonstrating the opposite is the evidence that the corrected premise is the one that was implemented.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the test as written and passing. State whether it pins the membership or the no-silently-dropped invariant, and if the invariant, paste the root-doc exemption as encoded and the OQ-03 answer. MUTATION-CHECK it: reintroduce the both-and state (add `TODO.md` back to `SCAN_ROOTS` with no policy, or remove the policy), show the test FAILS, revert, show it passes. Paste the existing three `SCAN_ROOTS` assertions and state whether any was updated and why.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: the four surfaces are one defect and fixing a subset leaves the trap open. `TODO.md` loses work because it is scanned-and-dropped (E-01), looks like a work surface (E-02), is written to by a live workflow (E-04), and is named obliquely rather than as deprecated in the always-loaded instructions (E-05); closing three of those four still leaves an agent writing findings into a file that silently discards them. The two spec gates (E-03) are the same file's other structural dependency and the item's requirement 1, and leaving them would make the item unclosable. The plan is nonetheless internally ordered so each E-item is independently reviewable and revertible, and E-01 is the only one with a design decision.

Scope fence: touch ONLY the nine paths in `- Scope-Paths:`. Do NOT delete `TODO.md`. Do NOT edit the `## Notes` paragraphs. Do NOT touch the releases or reviews entries in `SCAN_ROOTS` (sibling plan `m867ox` owns them). Do NOT widen the unclassified-file drift condition. Do NOT strip a gate from a `deferred` spec, and do NOT change either spec's status or content beyond its gate fields. Do NOT hand-edit `AGENTS.md` instead of the generator. Do NOT rewire `/whatnext` to consume `aw next -o`. Do NOT fix `DECISIONS.md`, `README.md` or `ARCHITECTURE.md`. Do NOT edit spec `25kzda`'s §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find `SCAN_ROOTS`, `iter_scan_files`, `_classify_tree`, `attention.scan`, `TREE_POLICY`, and the managed-block text in `engine.py` by name. The backlog item's own citation of `i6015i` as "pending" was already wrong (F-6), so verify status claims too, not only line numbers.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. THAT IS NOT BOILERPLATE HERE: this plan edits `artifact_core.py`, which sibling plan `m867ox` also edits, and it edits `AGENTS.md`, which the managed-block installer rewrites. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved diof9n --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `ld08f1`, which this plan carries as `- From-Backlog:`. That item carries no release gate, so none is inherited.
