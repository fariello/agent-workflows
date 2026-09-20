# Spec: Cross-artifact lifecycle symbols and ANSI status styling

- Date: 2026-09-13
- Status: approved
- Priority: high
- Blocks-Release: next
- Id: uonrjg
- Author: aw specs new
- Scope: A single accessible glyph and ANSI vocabulary for artifact statuses, artifact id6s, and live runner activity across human terminal views.

## Workflow history

- 2026-09-19 note (aw specs): Section 12a re-review round 2 (opencode its_direct/pt3-claude-opus-5-1m-us, plan n4xq3l) at HEAD 8fd2658a, a HEAD where yaxr4i is executed (.aw/records/plans/executed/, finalize commit 878f6152). STATUS DELIBERATELY UNCHANGED at approved: this is a documentary re-read, /spec-review was NOT invoked (it refuses an approved spec, and its transition step would de-approve this release-gating spec), and no .review.md was filed (filing one arms an approval gate with no override). PER-CRITERION VERDICT: A11 NEEDED AMENDMENT and was amended; A12 HOLDS in substance but NEEDED A RE-POINTED CITATION and got one; A13 NEEDED AMENDMENT and was amended; Section 9.3 NEEDED RE-POINTING and was re-pointed. A11: its 'UNCONDITIONAL' claim is no longer true as written, because yaxr4i added the flag layer this spec asked for and placed it ABOVE the environment; measured on a non-TTY stream, --color returns True against all three of A11's conditions (NO_COLOR=1, TERM=dumb, non-TTY), each of which returns False without the flag. Restated to hold for an invocation passing neither --color nor --no-color; the glyph-plus-word half stays unconditional. The documentation hazard A11 warned about is RESOLVED: docs/cli-output-contract.md section 9 is now headed 'RETRACTED 2026-09-19' and the 'adopts aw.agent/v1 immediately upon release' promise survives only as explicitly-quoted retracted text, so the ruling and the document finally agree. A12: substance holds (AW_ASCII_ONLY and FORCE_ASCII are both read in term.should_unicode, gated on exactly '1', untouched by yaxr4i, and there is no --ascii flag, so the new flag layer is color-only), but its citation term.py:224-227 had rotted onto should_color's NO_COLOR block; now cited BY SYMBOL, since a line number in a spec rots on the next unrelated edit and a wrong line is worse than none. A13: 'according to existing precedence' was a deliberately deferred reference and the referent has shipped, so the chain is now written out (--color/--no-color > NO_COLOR/FORCE_COLOR > TERM > isatty) with three rungs named for assertion; FORCE_COLOR=1 with --no-color now yields NO color, so an implementation treating FORCE_COLOR as the top of the chain is wrong. Section 9.3: 'current behavior' re-pointed at the one originating definition (term.should_color), the published chain, the override= argument rule (a flag must never reach the resolver via os.environ, because nested aw processes inherit it), and the measured flag surface (200 leaf subcommands, 229 nodes including 29 intermediate groups; 29 leaves declare neither flag and all 29 are accounted for: 28 host-driver leaves that forward argv verbatim and honor the flags by CONSUMPTION in cli._dispatch, plus the hidden __complete callback, verified separately). TWO DEFECTS FOUND AND FILED AGAINST OTHER ARTIFACTS, NOT THIS SPEC: (1) docs/cli-output-contract.md section 1.1 row 2 says NO_COLOR disables unless FORCE_COLOR 'is set' and that any non-empty FORCE_COLOR enables, which makes FORCE_COLOR=0 both cancel NO_COLOR and enable color; the shipped code does neither (measured FORCE_COLOR=0 -> False, NO_COLOR=1 FORCE_COLOR=0 -> False). The code is right on accessibility grounds and A13 adopts it; the document wording is stale. (2) aw specs note and aw specs set DESTROY tracked inline workflow history (they keep only the latest record, per maintainer-resolved OQ-2 of spec 20260818-1525-02, on the premise that the full log lives in .aw/records/history.jsonl) while that sidecar is GITIGNORED since commit 0c82cbdb, so the dropped rounds have no tracked home; this round's own five predecessor rounds were restored by hand in the same commit to avoid destroying a --by-human approval attestation. APPROVAL NOTE for the maintainer (plan OQ-01 fired): A11 and A13 are acceptance criteria and were NARROWED, on a spec carrying Blocks-Release: next, so the acceptance bar moved and the executing agent is surfacing that rather than deciding it. No aw specs set was run on this spec in either direction.
- 2026-09-13 approved (aw set, --by-human): status set to approved
- 2026-09-13 reviewed (aw set): spec-review round 1 (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; SR-401..SR-409, all nine FIXED, none deferred, none open. THE DESIGN IS SOUND; the findings are about COVERAGE and about relationships to other specs. OVERRIDE AUTHORITY recorded (new 0.5) on the maintainer's ruling, scoped to DISPLAY only, superseding 25kzda 5.6's five-color runner scheme (itself approved and release-gating) and requiring the implementing plan to amend that spec rather than leave two live tables. FIVE ORPHAN STATUS WORDS were in no mapping table and would each have rendered a gray '?', violating the spec's own A2: needs_input and awaiting-human -> waiting-input (satisfying 6kwd2e R4a.6, since 214 differs from blocked's 208), ran -> recovering, unknown_outcome -> failed, quarantined -> parked. OQ-01's PREMISE WAS WRONG and that was the session's most useful finding: the accessibility lens was STALE, not in conflict. DECISIONS D42 already required 'degrade through 256/16/none' and the lens still said 'prefer the 16 named colors', which is why D133 had to be an exception to a superseded rule. The lens is corrected (it ships to every managed repo) and this spec now carries the full ladder in 9.3a with one depth resolver, an AUTHORED 16-color palette with named collapses, and USER CONFIGURABILITY of depth and scheme. TWO FINDINGS RECORD MY OWN ERRORS: I proposed ran -> done (refuted twice over: 25kzda makes a ran item exit 1 and 7.2 already forbids styling unverified completion as success) and I proposed deferring configurability (no advantage, since configured and detected depth are one decision at one seam, and detection cannot see a colorblind user). SEQUENCING: implementing after yaxr4i is safe and recommended; 12a requires a declared executed:yaxr4i edge and a RE-REVIEW of this spec once yaxr4i lands, since it moves the flag surface A11-A13 rest on.
- 2026-09-13 to-review (aw set): Maintainer direction 2026-09-13: priority high, gates the next release (2.0.0). Recorded during /spec-review, before the review's own transition.
- 2026-09-13 to-review (aw set): Lifecycle glyph, active overlay, accessibility, mapping, architecture, and verification contracts finalized for review.
- 2026-09-13 created (aw specs): A single accessible glyph and ANSI vocabulary for artifact statuses, artifact id6s, and live runner activity across human terminal views.

## 0. Decision summary

Human terminal views MUST use one shared lifecycle presentation system for managed artifacts and runner
items. The presentation has three redundant parts:

1. the exact native status word, such as `to-review`, `implementing`, or `blocked`;
2. one semantic-stage glyph, such as `◔`, `▶`, or `⚠︎`; and
3. a restrained xterm-256 foreground color and optional bold weight.

The word is authoritative. The glyph and ANSI styling are redundant scanning aids. Color, glyph shape,
and animation are never the sole carrier of meaning.

Stored artifact status and live activity are distinct. A plan may remain `approved` while a runner is
executing it. In a live runner view, the activity glyph `▶` takes the glyph position and the text MUST
say `executing`; the runner MUST NOT mutate the artifact merely to produce that display. In an artifact
index with no live activity, the same plan displays its stored `approved` state as `◕ approved`.

Work-kind is deliberately excluded. `feature`, `bug`, `docs`, and similar classifications MUST NOT
change the lifecycle glyph, lifecycle color, or id6 styling.

## 0.5 Authority over other specs (added at review, 2026-09-13)

THIS SPEC IS THE SINGLE AUTHORITY FOR LIFECYCLE COLOR, GLYPH, AND ASCII FALLBACK in human terminal
output, and it OVERRIDES the earlier per-surface palettes named below. The maintainer ruled on
2026-09-13 that where this spec conflicts with another on PRESENTATION, this spec wins.

READ THE BOUNDARY OF THAT AUTHORITY PRECISELY, because it is narrow and the narrowness is what makes
the override safe. This spec overrides how a state is DISPLAYED. It overrides nothing about what a
state MEANS, which states exist, which transitions are legal, what a run's exit code is, or which
section of a report an item appears in. Section 3's non-goals already say so, and the override does
not widen them.

| Superseded claim | Where | Status | What this spec replaces it with |
|---|---|---|---|
| The five-color runner scheme: cyan for "running or verifying", green for verified, yellow for "skipped, needs input, or ran but unverifiable", red for failed, gray for informational | `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` (`25kzda`) Section 5.6 | `approved`, `Blocks-Release: next` | Section 5's table. Three differences are deliberate: `running` and `verifying` get DISTINCT glyphs (`▶` versus `◆`) rather than sharing cyan; green is reserved for `done` while `ready` is cyan; and `blocked` is orange 208 rather than folded into yellow. `25kzda`'s outcome VOCABULARY, exit codes, and reporting columns are untouched. |
| "The wizard MUST use the existing `Term` abstraction and 16 named colors", with green for recommended states | `.aw/records/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md` Section 11.4 | `superseded` | Nothing, for two reasons: that spec is already superseded, and its successor (`20260810-1447-01`, `implemented`) carries the accessibility clause forward WITHOUT the 16-color restriction. The wizard is also not a lifecycle surface, so Section 3's non-goal on generic command outcomes exempts it. Recorded so Section 11.4 is not resurrected as a live palette. |
| "Do not assume 256-color or truecolor; fall back through 16-color and then no-color ... prefer the terminal's default fg/bg and the 16 named colors", with a narrow `aw attention`-only xterm-256 exception attributed to DECISIONS D133 | `.aw/system/workflows/assess/lenses/accessibility.md:56-63` | not a spec; it is the normative rubric `20260706-0000-01` Goal 9 delegates to | REQUIRES AN AMENDMENT RATHER THAN AN OVERRIDE, because it is a rubric this spec should satisfy, not a competitor. The D133 exception is currently scoped to `aw attention` alone and must be widened to every renderer this spec names, in the same change that lands the resolver. See the open question in Section 16, which is the one thing here this spec does NOT settle on its own authority. |

WHAT AN IMPLEMENTER MUST DO WITH THIS SECTION, so the override is real rather than asserted: the plan
that lands the resolver MUST amend `25kzda` Section 5.6 to point here rather than leaving two live
color tables in the tree, and MUST declare that spec file in its `Scope-Paths`. An override recorded
only in the winning spec leaves the losing spec still saying the opposite to the next reader.

## 1. Problem

The repository currently has several correct but independent status presentations. `term.py` owns a
large `STATUS_COLOR_256` table and generic outcome glyphs. `attention.py` duplicates native status
colors and colors both status words and id6s. `render_stream.py` owns another palette and its own event
glyphs. Runner, index, lint, and status commands make local choices around those helpers.

The consequences are visible:

- the same semantic stage can have different colors in different commands;
- green currently means both ready and complete in several views;
- active review, execution, verification, integration, and recovery can collapse into one generic
  `running` treatment;
- an id6 can be styled differently from the status of the artifact it identifies;
- adding a new artifact status requires finding several partial tables;
- a compact id6-only reference does not communicate lifecycle stage without color;
- terminal accessibility behavior is easy to preserve in one renderer and miss in another.

This spec defines the presentation contract. It does not change any lifecycle enum or stored artifact.

## 2. Goals

1. Make lifecycle position recognizable at a glance across artifact types.
2. Make active work more specific than a generic spinner or `running` label.
3. Give an artifact id6 the same lifecycle treatment as its adjacent status.
4. Preserve exact native status words so output remains precise and accessible.
5. Centralize semantic resolution, glyphs, ASCII fallbacks, and colors.
6. Preserve clean non-TTY and machine output.
7. Keep the display calm enough for dense status boards and long runner queues.

## 3. Non-goals

- Changing lifecycle states, transition rules, attention classes, or artifact storage.
- Encoding work-kind, priority, severity, gate kind, or artifact type in lifecycle styling.
- Replacing finding-severity icons or generic command outcome icons that are not lifecycle states.
- Adding backgrounds, blinking text, reverse video, underlining, or animated lifecycle symbols.
- Inferring terminal background color or requiring a particular terminal theme.
- Removing native status words from ordinary human-readable output.
- Adding ANSI escapes to `--agent`, `--json`, pipes, redirected output, or `TERM=dumb` output.

## 4. Vocabulary

### 4.1 Native status

The status stored by an artifact owner, for example a plan's `to-review`, a spec's `implementing`, or a
release's `shipped`. Native status remains the lifecycle authority.

### 4.2 Semantic stage

A presentation-only category shared by native statuses with the same lifecycle meaning. Semantic stage
is not written into artifacts and is not a replacement lifecycle enum.

### 4.3 Live activity

Transient work reported by a runner or ledger, such as reviewing, executing, verifying, integrating,
or recovering. Activity may temporarily override the displayed stage glyph in a live view. It does not
override stored status or transition authority.

### 4.4 Integrity state

A renderer-visible fact that the artifact or run record is invalid, contradictory, or failed. Integrity
failure has higher display precedence than live activity because a plausible active glyph on invalid
state is actively misleading.

### 4.4a Why several native words share one stage (and where that hides a real duplication)

MANY-TO-ONE IS THE DESIGN, NOT AN OVERSIGHT. Section 0 makes the native word authoritative and the glyph
a redundant scanning aid, so a stage is deliberately shared by every native word with the same lifecycle
meaning. This spec already does it in several places: `blocked`, `dependency-blocked`,
`integration-blocked` and `merge-conflict` all render `⚠︎` while each printing its own word. A reader
comparing two rows that share a glyph is seeing the aid work, not a table defect.

THE WAITING CASE IS WORTH SPELLING OUT, because three names look interchangeable and are not. They sit at
three different layers, and only the first is this spec's:

| Name | Layer | What it is |
|---|---|---|
| `waiting-input` | presentation | THIS SPEC'S semantic stage: the glyph `…`, the ASCII `.`, color 214, bold |
| `needs_input` | one gate's result | a GATE STATUS in `run_gates.ALL_GATE_STATUSES`, alongside `approved`, `rejected`, `timed_out`, `refused` and `aborted` |
| `awaiting-human` | one queue item's state | a RUN DISPOSITION (spec `6kwd2e` R3.1): non-terminal, item parked, lane preserved, queue continues |

They answer different questions. `needs_input` answers "what did this gate decide?" and can occur where
there is no queue item at all; `awaiting-human` answers "what is this queued item doing?". A gate
returning `needs_input` is one CAUSE of an item becoming `awaiting-human`, not a synonym for it. Both
render `…` because a human reading a board wants one shape for "someone is waiting on me", and both keep
their own word because the word is what says which system is waiting and why.

AND NOW THE PART THAT IS A GENUINE SMELL RATHER THAN A PRESENTATION QUESTION, raised by the maintainer at
review and recorded here because presentation is where it became visible. Two independent vocabularies
exist for "a human is needed", and the reason is measurable: `run_gates.py` is UNWIRED TO BOTH RUNNERS
(`grep run_gates` returns nothing in either driver, and spec `6kwd2e` records the same fact at its own
Section 0.4). So `needs_input` has never had to coexist with a runner disposition, and `awaiting-human`
was designed while the older mechanism sat unreachable. That is how two names for one situation get
built without anyone choosing to build them.

THIS SPEC DOES NOT RESOLVE IT, and must not: collapsing two state vocabularies is a lifecycle change,
which Section 3 excludes, and it would mean editing a reviewed spec's requirement from a presentation
spec. What this spec does is REFUSE TO HIDE IT. Rendering both as `…` is correct today and is explicitly
NOT an endorsement of keeping both: if a later change wires `run_gates` into the runners, whoever does it
should decide whether one of the two names retires. Recorded as the open question in Section 16 so the
observation is not lost with this review.

### 4.5 One-character representation

One Unicode grapheme used as a semantic marker. Some selected graphemes contain a text-presentation
variation selector and therefore contain two code points. They are still one visible representation.
Code MUST NOT use Python `len()` as a proxy for their display width.

## 5. Canonical lifecycle presentation

The following table is normative. ANSI numbers are xterm-256 foreground indices. Bold applies to the
glyph, id6, and status word when those elements are styled. No other SGR attribute is used.

| Semantic stage | Unicode | ASCII | Color | Bold | Meaning |
|---|---:|---:|---:|:---:|---|
| formative | `○` | `D` | 245 | no | Draft, incomplete, or not yet admitted |
| review-queued | `◔` | `Q` | 39 | no | Awaiting review |
| authority-queued | `◑` | `A` | 135 | no | Reviewed and awaiting approval or authority |
| ready | `◕` | `>` | 45 | yes | Approved, planned, open, pending, or otherwise actionable |
| reviewing | `◎` | `R` | 220 | yes | A review turn is active |
| executing | `▶` | `E` | 220 | yes | Implementation or execution is active |
| verifying | `◆` | `V` | 220 | yes | Tests or other verification are active |
| integrating | `⇄` | `M` | 220 | yes | Merge or integration work is active |
| recovering | `↩︎` | `T` | 220 | yes | Retry, correction, resume, or recovery is active or required |
| active | `●` | `*` | 220 | yes | Active work whose subtype is unavailable |
| waiting-input | `…` | `.` | 214 | yes | Waiting for human input or another non-failure response |
| blocked | `⚠︎` | `!` | 208 | yes | Work cannot advance until a named condition clears |
| failed | `✘` | `X` | 196 | yes | Terminal failure or invalid/inconsistent state |
| done | `✓` | `+` | 46 | yes | Successfully completed, implemented, executed, or shipped |
| reusable | `↻` | `~` | 81 | no | Completed reusable artifact that remains intentionally available |
| parked | `◇` | `P` | 244 | no | Intentionally inactive, deferred from current work, or archived |
| superseded | `↪` | `S` | 244 | no | Replaced by a newer artifact or decision |
| abandoned | `∅` | `N` | 244 | no | Intentionally not executed, cancelled, expired, or abandoned |
| unknown | `?` | `?` | 244 | no | State cannot be determined safely |
| none | `·` | `-` | 244 | no | Artifact type has no lifecycle at this location |

`⚠︎` is U+26A0 followed by U+FE0E. `↩︎` is U+21A9 followed by U+FE0E. Implementations MUST
use these text-presentation forms and MUST NOT substitute the emoji-presentation forms `⚠️` or `↩️`.
The text form avoids colorful platform emoji, variable baseline, and unexpectedly wide cells.

The five active subtypes share one amber treatment. Shape carries the subtype, while the adjacent word
states it explicitly. This creates useful differentiation without turning a queue into a rainbow.

Green is reserved for successful completion. Ready work is cyan, not green. Blocked work is orange,
while failed work is red. These separations prevent readiness, recoverable obstruction, and terminal
success or failure from collapsing into color alone.

## 6. Native artifact mappings

Every current managed lifecycle status MUST resolve as follows. A newly added status MUST be added to
this canonical mapping in the same change that adds the status. Falling through silently to gray for a
known status is a defect.

### 6.1 Plans and IPDs

| Native status | Semantic stage |
|---|---|
| `draft` | formative |
| `to-review` | review-queued |
| `reviewed` | authority-queued |
| `approved`, `auto-approved` | ready |
| `executed` | done |
| `reusable` | reusable |
| `superseded` | superseded |
| `not-executed` | abandoned |

`reviewing` and `executing` are live activities, not stored plan statuses.

### 6.2 Specs

| Native status | Semantic stage |
|---|---|
| `draft` | formative |
| `to-review` | review-queued |
| `reviewed` | authority-queued |
| `approved` | ready |
| `implementing` | executing |
| `implemented` | done |
| `deferred` | blocked |
| `parked` | parked |
| `superseded` | superseded |

### 6.3 Backlog items

| Native status | Semantic stage |
|---|---|
| `open` | ready |
| `graduated` | active |
| `blocked` | blocked |
| `parked` | parked |
| `done` | done |

`graduated` uses generic active because graduation can lead to more than one artifact type and does not
prove that execution is running.

### 6.4 Research

| Native status | Semantic stage |
|---|---|
| `todo`, legacy `intake` | ready |
| `active` | active |
| `reference` | done |
| `archive`, `archived` | parked |

Research outcome values such as `adopted`, `rejected`, `informational`, and `none-yet` are a separate
dimension. They MUST NOT replace the lifecycle glyph.

### 6.5 Prompts

| Native status or lane | Semantic stage |
|---|---|
| `pending` | ready |
| `executed` | done |
| `reusable` | reusable |
| `superseded` | superseded |
| `not-executed` | abandoned |
| untracked quarantine lane with no managed status | none |

Prompt kind, including `run-once`, `research`, and `session-handoff`, is not a lifecycle stage.

### 6.6 Releases

| Native status | Semantic stage |
|---|---|
| `planned` | ready |
| `blocked` | blocked |
| `shipped` | done |

### 6.7 Reviews and artifact types without a lifecycle

A review record does not own an independent artifact lifecycle. Where a review row identifies its
subject, it MUST use the subject artifact's stage. Review readiness MAY use `authority-queued` for
`go-pending-approval`, `ready` for `go`, and `blocked` for `no-go`, but MUST be labeled `readiness` so it
cannot be mistaken for the subject's stored status. Finding severity remains a separate visual system.

Walkthroughs, roadmaps, prompt-library entries, and other records with no lifecycle use `none` only when
a lifecycle column is required. Prefer omitting the lifecycle column when every row is `none`.

## 7. Runner and ledger mappings

### 7.1 Action-aware activity

When a live runner knows the action, it MUST choose the specific activity rather than generic `active`:

| Runner fact | Activity |
|---|---|
| review turn is running | reviewing |
| execute or implement turn is running | executing |
| verifier or tests are running | verifying |
| merge, rebase, or integration is running | integrating |
| retry, correction, or preserved-lane resume is running | recovering |
| running with no trustworthy subtype | active |
| human answer is required | waiting-input |

The exact activity word MUST be printed in ordinary status displays. A generic `running` word is allowed
only when the subtype is genuinely unavailable.

### 7.2 Runner item outcomes

| Current item status | Semantic stage |
|---|---|
| `queued` | ready |
| `running` | action-aware activity from 7.1, otherwise active |
| `interrupted`, `partial`, `substantially-complete`, `correction_required` | recovering |
| `reviewed` | authority-queued |
| `approved` | ready |
| `executed`, `verified`, `complete` | done |
| `blocked`, `dependency-blocked`, `integration-blocked`, `merge-conflict` | blocked |
| `failed`, `failed-safely` | failed |
| `not-attempted`, `cancelled` | abandoned |
| `needs_input`, `awaiting-human` | waiting-input |
| `ran` | recovering |
| `unknown_outcome` | failed |
| stale projected `abandoned?` or another inference | unknown |

THE FOUR ROWS ABOVE WERE ADDED AT REVIEW (2026-09-13) and each closes a word this spec's own Section 6
preamble and criterion A2 would otherwise have made a defect. They were absent, not decided against, so
the table silently resolved five real states to `unknown` (`?`) in a spec whose stated rule is that
falling through for a KNOWN status is a defect. The reasoning for each, since three of them were
judgement calls:

- `needs_input` (`run_gates.GATE_STATUS_NEEDS_INPUT`, a live constant) and `awaiting-human` (spec
  `6kwd2e` R3.1) are MECHANICAL: both mean a human is required, which is exactly `waiting-input`. Note
  this satisfies `6kwd2e` R4a.6, which forbids folding `awaiting-human` into the `blocked` group: 214 is
  distinct from `blocked`'s 208 and `failed`'s 196. See 4.4a for why two names exist at all.
- `ran` is `recovering`, NOT `done`, and the spec proves it twice. `25kzda` states that a `ran` item
  "contributes non-success to aggregate calculation and therefore exit 1", and Section 7.2 of THIS spec
  already forbids the alternative: "Unverified completion MUST NOT be styled as verified success merely
  because work was performed." So green `✓` would paint an exit-1 item as success, the exact collapse
  Section 5 exists to prevent. `recovering`'s defined meaning includes "or required", which fits an item
  that needs a human to look at it. REJECTED: `done` (falsifies the exit code), `unknown` (`ran` is
  precisely determined, not undeterminable), `waiting-input` (nothing is being asked), and a new 21st
  stage (honest, but it widens a deliberately restrained table for one outcome, and the printed word
  `ran` already carries the distinction). HONEST COST of the chosen answer: `↩︎` suggests a retry is
  pending when none is scheduled, so the word is doing more work here than in any other row.
- `unknown_outcome` (owned by spec `c4gd2h`, `implementing`) is `failed`, NOT this spec's generic
  `unknown`. It is a REAL, NAMED, terminal disposition, whereas `unknown` means the state could not be
  determined. Mapping a named disposition onto the lookup-failure glyph would erase the distinction
  `c4gd2h` Section 0.0 exists to protect (that section exists because two definitions of this token
  already collided once). A resolver MUST NOT treat the two as the same thing merely because both
  contain the word "unknown".
- `quarantined` (spec `ipd-spec` Section 13.3, emitted by `ipd_lint`) is `parked`: a quarantined plan is
  deliberately set aside with a named owner and follow-up, which is `parked`'s meaning. REJECTED:
  `blocked` (nothing external is obstructing it), `formative` (it may be a complete plan), and `failed`
  (quarantine is a decision, not a failure). Note it is carried by a `- Quarantine:` FIELD rather than a
  `- Status:` value, so a resolver reads it as an integrity/condition input per Section 8, not as a
  native status; it is listed in this table because the lint view must show it without calling it a pass.

An item that is presently verifying displays `verifying`, even if its last durable ledger event is
`performed`. Once verification completes, it displays `done`. Unverified completion MUST NOT be styled
as verified success merely because work was performed.

### 7.3 Run ledger and set state

| Ledger or set state | Semantic stage |
|---|---|
| `pending`, `runnable`, `set_planned` | ready |
| `running`, `set_running` | action-aware activity or active |
| `performed`, `verifying` | verifying |
| `verified`, `complete`, `set_complete` | done |
| `correction_required`, `set_partial` | recovering |
| `set_waiting_input` | waiting-input |
| `blocked` | blocked |
| `failed`, `set_failed` | failed |
| `cancelled`, `set_cancelled` | abandoned |

### 7.4 Communication acknowledgements

Communication acknowledgement states are not artifact lifecycles, but dense status tables MAY use this
same semantic vocabulary: scheduled or queued is ready; delivered is ready; read is authority-queued;
in-progress is active; done or executed is done; agent-not-running or agent-not-responding is blocked;
expired, not-done, or not-executed is abandoned. The native acknowledgement word remains mandatory.

## 8. Resolution precedence

A renderer MUST resolve one displayed semantic stage in this order:

1. invalid, contradictory, or terminally failed state: `failed`;
2. a current named obstruction: `blocked`;
3. a current live activity from section 7.1, including `waiting-input`;
4. the native artifact or durable run status mapping;
5. `unknown` when a lifecycle is expected but cannot be resolved safely;
6. `none` when the artifact type has no lifecycle here.

This is display precedence, not state precedence. The resolver MUST return the native status and activity
separately so a caller can render both when space permits. It MUST NOT mutate either source.

## 9. Rendering contract

### 9.1 Full rows

The preferred full-row form is:

```text
PLAN       ◔  abc123  to-review     Short title
SPEC       ▶  def456  implementing  Short title
BACKLOG    ⚠︎  ghi789  blocked       Short title
```

The glyph, id6, and status word use the same lifecycle color and weight. The artifact type and title do
not inherit lifecycle color. Whole-row coloring is forbidden because it destroys hierarchy and makes a
large board noisy.

The exact column order MAY follow an existing command's stable contract, but glyph MUST immediately
precede either id6 or status so its referent is obvious. Existing stable machine formats are unchanged.

### 9.2 Compact id6 references

When a view intentionally shows only an id6, use `GLYPH id6`, with the glyph and id6 styled together.
If a status word fits, include it. Tooltips are not a substitute in terminal output. A legend MUST be
available in the command help and SHOULD be shown once in a view that contains three or more semantic
stages unless the words already appear beside every glyph.

### 9.3 Plain and ASCII output

When color is disabled, the Unicode glyph and native word remain. When Unicode is disabled by
`AW_ASCII_ONLY=1`, `FORCE_ASCII=1`, or stream capability, the exact ASCII fallback in section 5 replaces
the Unicode grapheme. Native words remain in both modes.

The system MUST preserve current `NO_COLOR`, `FORCE_COLOR`, `TERM=dumb`, TTY, stream-encoding, and
redirection behavior. `FORCE_COLOR` affects ANSI only and MUST NOT force Unicode onto an incompatible
stream.

RE-POINTED 2026-09-19 BY THE SECTION 12a RE-REVIEW (plan `n4xq3l`). "CURRENT" WAS A MOVING TARGET when
this section was written on 2026-09-13, and Section 12a obligation 2 required it to be re-pointed once
`yaxr4i` landed. It has, so "current" now means EXACTLY the following, and the word is replaced by
citations an implementer can check:

- THE ORIGINATING DEFINITION is `agent_workflows.term.should_color`, and there is only one. It is
  package-wide, `runner_shared.should_color` is a sanctioned one-line delegation to it, and
  `tests/test_term.py` asserts the single-originating-definition property. That property is what
  R9.3a.2 demands of the DEPTH resolver, and it is already true of the boolean one, so a depth resolver
  MUST extend this function rather than introduce a rival seam.
- THE PRECEDENCE CHAIN is `--color`/`--no-color` > `NO_COLOR`/`FORCE_COLOR` > `TERM` > `isatty()`,
  published in `docs/cli-output-contract.md` section 1.1 and pinned by `tests/test_term.py` and
  `tests/test_flag_surface_uniformity.py`. See A13 for the three rungs that must be asserted by name,
  and for the one place that published table's wording is stale relative to the code.
- THE FLAG LAYER IS NEW AND SITS ON TOP, which is the change this re-pointing exists to absorb. A
  `--color`/`--no-color` flag is an explicit operator instruction for one invocation and outranks the
  environment, so R9.3a.2's top rung ("`NO_COLOR` / `--no-color` / `TERM=dumb` / non-TTY -> none,
  unchanged, and unconditional") remains correct about `--no-color` and about `NO_COLOR` beating a
  PINNED DEPTH, but `--color` can now produce color in the other three of those four conditions. A11
  carries the restatement.
- THE FLAG MUST NOT REACH THE RESOLVER THROUGH `os.environ`. It is passed as the `override=` argument
  (or set once per invocation via `term.set_color_override`), because this package spawns nested `aw`
  processes and an environment variable is INHERITED, which would silently restyle a child's output. A
  depth resolver added for R9.3a.2 MUST follow the same rule for the same reason.
- THE FLAG SURFACE IS UNIFORM, so a renderer may assume the flags exist everywhere. Measured 2026-09-19
  by walking `cli._build_parser()`: 200 LEAF subcommands (229 subcommand nodes in total, of which 29 are
  intermediate groups that dispatch no action of their own). Exactly 29 leaves DECLARE neither flag, and
  all 29 are accounted for: 28 are host-driver leaves whose argv is intercepted and forwarded VERBATIM
  (the `oc`/`opencode`/`agy`/`antigravity` families plus `run as`/`run ipd`), and they honor the flags by
  CONSUMPTION in `cli._dispatch` before any interception runs; the 29th is the hidden `__complete` shell
  callback, which likewise accepts the flag and emits unstyled candidates. Zero leaves are unexplained.
  STATE THE DENOMINATOR WHENEVER THIS IS RE-MEASURED: 200 and 229 are both true of this tree and count
  different things, and the leaf-miss count (29) coincides numerically with the group count (29), so a
  bare "29 of 229" reads as self-consistent while being the wrong ratio.

### 9.3a Color depth: the 256 -> 16 -> none ladder, and the user's override

ADDED AT REVIEW, 2026-09-13, on the maintainer's ruling. Section 5's table is the 256-COLOR tier. It is
the top rung of a three-rung ladder, not the only rendering, and the tier in force is resolved ONCE by
the same seam that resolves everything else about presentation.

**R9.3a.1 THE LADDER IS 256 -> 16 -> NONE**, per DECISIONS D42 ("degrade through 256/16/none"). A
256-capable context gets Section 5 verbatim. A 16-color context gets the authored 16-color palette of
R9.3a.3. A no-color context gets plain text with the glyph and word intact, exactly as Section 9.3
already requires. THIS SPEC IS NOT AN EXCEPTION TO THE ACCESSIBILITY LENS AND MUST NOT BE WRITTEN AS ONE:
the lens states this same ladder (corrected 2026-09-13, having previously contradicted D42), so the two
documents now agree and an implementation satisfies both at once.

**R9.3a.2 THE DEPTH IS A RESOLVED VALUE, NOT A GUESS AT EACH CALL SITE.** Nothing in the package resolves
color DEPTH today: `term.should_color` returns a plain boolean and `COLORTERM`, `256color` and any depth
logic grep to zero. So the resolver is new work, it belongs beside `should_color` in `term.py`, and it
MUST have exactly one definition. Precedence, highest first:

```text
NO_COLOR / --no-color / TERM=dumb / non-TTY   ->  none      (unchanged, and unconditional)
explicit user depth setting                   ->  that tier
detected capability (COLORTERM, TERM, etc.)   ->  that tier
default                                       ->  256
```

`NO_COLOR` OUTRANKS THE USER'S DEPTH SETTING DELIBERATELY. It is an accessibility convention and a
preference may not defeat it; a user who wants color pins a depth AND does not set `NO_COLOR`. Note the
default is 256 rather than the most conservative rung, which is the whole point of D42: the conservative
default is what produced a decade of monochrome tooling.

**R9.3a.3 THE 16-COLOR PALETTE IS AUTHORED, NOT DERIVED, AND ITS COLLAPSES ARE NAMED.** Section 5 uses 11
distinct 256 indices and 16-color has no room for them, so a mechanical nearest-neighbour mapping would
silently merge stages that must stay distinguishable. The 16-color tier MUST therefore be an explicit
table, and it MUST preserve these separations, which are the ones Section 5 exists to protect: `ready` is
not `done`; `blocked` is not `failed`; `waiting-input` is not `blocked`. The following collapses are
EXPECTED and ACCEPTABLE, because in each case the glyph and the word still separate the states:

- the five active subtypes (`reviewing`, `executing`, `verifying`, `integrating`, `recovering`) and
  `active` collapse to ONE yellow. They already share one color at 256; only their glyphs differ.
- the four grays (`parked`, `superseded`, `abandoned`, `unknown`, `none`, `formative`) collapse to plain
  or to one dim-free neutral. They differ by at most one index at 256 (244 versus 245), so this tier loses
  almost nothing.

**R9.3a.4 THE SCHEME AND THE DEPTH ARE BOTH USER-CONFIGURABLE**, through the existing `aw config` store
(`config.CONFIG_SCHEMA` is a declarative `ConfigKeySpec` map, so this is a schema entry rather than a new
mechanism). At minimum a user MUST be able to pin the DEPTH. A user SHOULD additionally be able to
override an individual stage's color, because that is the only remedy for the case detection cannot see.

WHY CONFIGURABILITY IS IN THIS SPEC RATHER THAN DEFERRED, recorded because the reviewer initially proposed
deferring it and the maintainer rejected that, correctly. FIRST, it is the same decision at the same seam:
a configured depth and a detected depth answer one question ("which tier?"), so building detection alone
means writing that resolver with one input and reopening it later, along with every call site's precedence
assumption. SECOND, and decisive on accessibility grounds, DETECTION CANNOT SEE THE USER. A terminal that
reports 256-color tells you nothing about whether its user can distinguish 208 from 214, and Section 5
puts `blocked` and `waiting-input` on exactly that adjacent-orange pair. Without an override, the user
this lens exists to protect has no recourse but to wait for a later spec. That is the wrong order.

**R9.3a.5 EVERY TIER KEEPS THE INVARIANT.** The glyph and the native word are present at 256, at 16, and
at none. No tier may become the only place a state is distinguishable, which is what makes the collapses
in R9.3a.3 acceptable rather than lossy.

### 9.4 Width and variation selectors

Renderers MUST treat a lifecycle symbol as an opaque grapheme, not index or truncate it by code point.
ANSI stripping, padding, and truncation MUST operate on visible text. Because several preferred symbols
have East Asian Width `A`, perfect alignment cannot be guaranteed across every terminal's ambiguous-width
policy. The supported contract is:

- correct grapheme and no broken variation selector in every UTF-8 mode;
- stable alignment in the repository's normal UTF-8 terminal test profile;
- guaranteed single-byte alignment in ASCII mode;
- no use of `len(styled_text)` to compute a visible column.

An implementation MAY add a shared display-width helper or a small dependency if needed, but MUST NOT
create per-renderer width guesses.

PRIOR ART CONFIRMS THIS SECTION AND NARROWS THE WORK (added at review, 2026-09-13). `render_stream.py`
already carries a measured width policy for its own event glyphs and reaches the same conclusion this
section does, so the requirement is not new ground:

- It measured `unicodedata.east_asian_width` over its ten glyphs and found FIVE ambiguous, TWO OF WHICH
  THIS SPEC ALSO USES AS LIFECYCLE GLYPHS: `▶` U+25B6 (this spec's `executing`) and `◇` U+25C7 (this
  spec's `parked`). So the ambiguity Section 9.4 admits is already documented for this spec's own symbols,
  not merely hypothesized.
- It states its padding is computed in CODEPOINTS via `len` and that this is "exact only for glyphs a
  terminal renders SINGLE-WIDTH", which is precisely the `len(styled_text)` failure this section forbids.
- It solves it the way this spec does, with an ASCII substitution table selected by the same
  `use_unicode` flag, and it explicitly records that "A TRUE display-width helper (a wcwidth-style 0/1/2
  table) is deliberately NOT built here".

CONSEQUENCE FOR THE IMPLEMENTER: no display-width helper exists in the package today (verified: no
`wcwidth`, no `display_width` symbol), so if this spec's resolver needs one it is NEW work, and it must be
shared rather than added beside the existing per-module policy. Reusing `render_stream`'s pattern (an
ASCII table behind one capability flag) satisfies Section 9.4 without a width helper at all, which is the
cheaper route and the one already proven here.

### 9.5 Machine output

`--agent`, `--json`, pipes, and redirected output MUST contain no ANSI escapes. Existing machine schemas
MUST remain backward compatible. If a command adds semantic information to structured output, it MUST
use explicit fields such as `native_status`, `semantic_stage`, and `activity`, not a colored string, and
MUST follow that schema's versioning rules.

## 10. Architecture

### R10.1 One semantic source

Create one stdlib-only semantic module, preferably `agent_workflows/lifecycle_style.py`, containing:

- the semantic-stage definitions from section 5;
- Unicode and ASCII glyph constants;
- xterm-256 color and bold metadata;
- native mappings scoped by artifact or record type;
- runner and ledger mappings;
- the precedence resolver; and
- validation that rejects duplicate keys and incomplete known-status coverage.

The module MUST NOT emit ANSI. It returns immutable presentation data to `Term` or another renderer.

### R10.2 Rendering boundary

`agent_workflows/term.py` remains the terminal capability and ANSI boundary. It SHOULD expose a small
API equivalent to:

```python
resolve_lifecycle(artifact_type, native_status, *, activity=None, integrity=None)
format_lifecycle_marker(resolved)
style_lifecycle_text(text, resolved)
```

Names may differ, but resolution and rendering MUST remain separate and testable.

### R10.3 Consumers

Human lifecycle output in `attention.py`, plan/spec/research/backlog indexes, status setters, lint output,
run viewers, and both runners MUST consume the shared resolver. Local `_STATUS_COLOR_256` lifecycle
tables MUST be removed. `render_stream.py` MAY retain event glyphs and severity colors that are not
lifecycle semantics, but lifecycle item or statusline rendering MUST use the shared resolver.

Generic `Term` outcomes such as command-level OK, WARN, and FAIL remain valid and are outside this spec.
Do not mechanically replace every checkmark in the repository.

### R10.4 Unknown values

The resolver MUST distinguish `unknown` from `none`. A known artifact family with an unrecognized native
status is `unknown` and SHOULD emit a diagnostic at validation boundaries. An artifact family that has
no lifecycle is `none`. Neither case may silently masquerade as parked gray.

## 11. Accessibility and restraint

1. Every ordinary lifecycle display includes a native status or activity word.
2. Glyph and color are redundant cues. Either can be removed without losing the state.
3. No blink, background, underline, reverse video, or load-bearing dim is permitted.
4. Bold is limited to ready, active, waiting, blocked, failed, and done stages in section 5.
5. Only glyph, id6, and status are colored. Titles, paths, descriptions, and evidence remain neutral
   except for an existing independent convention.
6. A legend uses words in the same order as the lifecycle, not color names.
7. Screen-reader and copied output remains linear and understandable.
8. The text-presentation selector is mandatory for warning and recovery symbols.

## 12. Compatibility and rollout

Implementation is additive to human presentation and requires no data migration.

1. Land the semantic resolver and exhaustive table tests first.
2. Add `Term` rendering helpers and capability tests.
3. Convert `attention.py`, including identical treatment of status and id6.
4. Convert indexes, status commands, lint views, and run viewers.
5. Convert lifecycle portions of both runner displays and `render_stream.py`.
6. Remove duplicate lifecycle tables only after all consumers use the shared source.
7. Update command snapshots, help text, and user documentation with one canonical legend.

Existing column order and machine fields MUST be preserved unless a separately reviewed interface change
explicitly changes them. Human snapshot changes are expected where the new marker is introduced.

## 12a. Approved plans already queued against these files (added at review, 2026-09-13)

EIGHT APPROVED, UNEXECUTED PLANS DECLARE FILES THIS SPEC CLAIMS. None contradicts this design, and one is
a genuine SEQUENCING DEPENDENCY that decides when the resolver can honestly be validated. Measured by
reading each plan's `- Scope-Paths:` at HEAD; the runner isolates lanes and re-validates on merge, so
file overlap alone is not a hazard and is not reported as one here.

| Plan | Declares | Relationship |
|---|---|---|
| `yaxr4i` (`ttyflags` 01) | `term.py`, `cli.py`, `result_types.py`, `docs/cli-output-contract.md` | **UPSTREAM DEPENDENCY. See below.** |
| `r2i1b1`, `ys1dor`, `zzcrlo`, `st5klo` | `render_stream.py` and both runners | MERGE FRICTION ONLY. Each adds or changes report CONTENT (a refusal record, an integration-aware outcome, a re-dispatch notice, an end-of-run spec-edit report); this spec restyles rows. Whichever lands second rebases. No vocabulary or palette claim in any of them. |
| `pr5b0t` (`lanestrand` 01) | `attention_contract.py`, `attention.py` | COMPATIBLE. It adds stranded lanes as attention items "mapped onto the existing class vocabulary", so it adds no class and no status this spec must cover. |
| `9iiqmm` (`awinbox` 02) | `attention.py` | COMPATIBLE. One advisory count line on the human board, not a lifecycle row. |
| `quqyc4` (`nogitmsg` 01) | `attention.py`, `cli.py` | COMPATIBLE. A git-aware hint message, not lifecycle styling. |

### `yaxr4i` IS UPSTREAM OF THIS SPEC AND SHOULD LAND FIRST

It owns the presentation-override surface that Sections 9.3 and 11 are written against, and it is
`approved` and runnable today. Three consequences, each verified rather than inferred:

1. IT IS NOT A DESIGN CONFLICT. That plan explicitly records `STATUS_COLOR_256` and `Term.color256` as
   "prior art, not a conflict", and it never touches the lifecycle color table this spec replaces. So
   nothing in it needs overriding.
2. IT ADDS THE FLAGS THIS SPEC ASSUMES. `--no-color` is currently missing from 25 of 219 subcommands
   (measured in that plan, and the gap is regrowing as new subcommands miss the shared parent), and
   `--color` has NO flag form at all, existing only as `FORCE_COLOR`. A13 of this spec speaks of
   `FORCE_COLOR` "according to existing precedence", and that precedence is exactly what `yaxr4i`
   settles. Landing this spec's resolver first would validate A11 to A13 against a surface about to move.
3. IT CARRIES A SETTLED RULING THAT MAKES A11 SAFE, and this was CORRECTED at review after an earlier
   draft of this section got it backwards. `yaxr4i` OQ-01 asked whether non-TTY stdout should select AGENT
   mode as `docs/cli-output-contract.md:159-163` promises. It is `- Status: resolved`: the maintainer ruled
   OPTION B on 2026-09-10, correct the document, because the promise NEVER SHIPPED (piping `aw` emits prose
   today), nothing can depend on behavior that never existed, an unknown number of external consumers
   depend on the ACTUAL behavior, and `--agent` already covers the capability. So piped output stays human,
   A11 is UNCONDITIONAL, and the document is being retracted rather than implemented.
   THE HAZARD THAT REMAINS IS A DOCUMENTATION LAG, not a design risk: the contract file still carries the
   unretracted promise until `yaxr4i` E-05 rewrites it, so anyone validating A11 from that document rather
   than from the ruling will reach the wrong conclusion. That is the strongest reason to land `yaxr4i`
   first, and it is why A11 now cites the ruling in its own text.

### Is it SAFE to implement this spec after `yaxr4i`? Yes, and it is the recommended order

Stated as a direct answer because it is the question a reader of this section will have. Nothing in
`yaxr4i` conflicts with this design (point 1), it ADDS the override surface Sections 9.3 and 11 assume
(point 2), and its one blocking question is already resolved in the direction A11 needs (point 3). So
executing this spec's resolver afterwards is safe, and the reverse order is the risky one, because it
would validate A11 to A13 against flags and a document that are about to change.

TWO OBLIGATIONS FOLLOW, both on the implementing plan rather than on `yaxr4i`:

1. DECLARE THE EDGE. The plan that lands the resolver MUST carry an `- Item-Dependencies:` edge on
   `yaxr4i` (spelled `executed:yaxr4i`), or state in writing why it does not need one. This spec does not
   otherwise constrain execution order.
2. RE-REVIEW THIS SPEC AFTER `yaxr4i` EXECUTES, BEFORE THE RESOLVER IS BUILT. This is a requirement, not a
   suggestion, and the reason is that `yaxr4i` changes the very surface three of this spec's criteria are
   written against: it adds `--color` where only `FORCE_COLOR` existed, adds `--no-color` to 25 of 219
   subcommands, settles `--color`/`--no-color` precedence, and rewrites `docs/cli-output-contract.md`. A11,
   A12 and A13 must be re-read against the flags and precedence as SHIPPED rather than as anticipated
   here, and Section 9.3's "MUST preserve current ... behavior" needs re-pointing at whatever "current"
   then means. Run `/spec-review` on this spec again at that point; a re-review appends a new round and
   keeps the status `reviewed`, so it costs one cheap turn and prevents building against a stale contract.

   DISCHARGED 2026-09-19 by plan `n4xq3l`, at a HEAD where `yaxr4i` is `executed`. The round is recorded in
   this spec's `## Workflow history`; A11 and A13 were AMENDED, A12's citation was RE-POINTED, and Section
   9.3's "current" was replaced by checkable citations. THE RESOLVER MAY NOW BE BUILT against those amended
   criteria.
   TWO CORRECTIONS TO THIS OBLIGATION'S OWN WORDING, recorded so the next reader is not misled by it.
   FIRST, `/spec-review` IS THE WRONG VERB HERE and was not used: that workflow's Step 0.1 classifies a
   spec at `approved` as NOT REVIEWED with its status as the reason, so a conforming run would have
   discharged nothing; worse, its transition step runs `aw specs set reviewed`, and `approved -> reviewed`
   is a legal BACKWARD transition, so it would have DE-APPROVED this release-gating spec, and the typed
   `.review.md` it files ARMS an approval gate whose refusal has no override. A documentary re-read
   recorded with `aw specs note` is the correct mechanism at `approved`, and it is what was done.
   SECOND, "keeps the status `reviewed`" ASSUMED A SPEC SITTING AT `reviewed`. This spec was already
   `approved` when that sentence was written (both happened in the 2026-09-13 round), so the PREMISE never
   held for it, though the CONCLUSION (append a round, do not re-open approval) is exactly right and was
   followed: the status remained `approved` and no `aw specs set` was run in either direction.
   A11's "UNCONDITIONAL" ABOVE IS NOW SUPERSEDED BY A11 ITSELF. Point 3 of the preceding subsection and
   this paragraph both assert it without qualification, which was true of the pre-`yaxr4i` surface; the
   flag layer that plan shipped sits ABOVE the environment, so `--color` overrides all three of A11's
   conditions. A11 carries the restatement and is the authority; read it rather than the sentences above.
   THE DOCUMENTATION LAG IS ALSO CLOSED: `docs/cli-output-contract.md` section 9 is now explicitly headed
   RETRACTED, so validating A11 from that document no longer reaches the wrong conclusion.

WHAT IS NOT A REASON TO WAIT, so the dependency is not overstated: file overlap with the four
`render_stream.py` plans is NOT a hazard, because each execute turn gets an isolated worktree and returns
through the merge-and-revalidate gate. Those four are ordinary rebase friction and impose no ordering.

## 13. Acceptance criteria

- **A1** One canonical module defines every semantic stage, glyph, ASCII fallback, color, bold flag, and
  native mapping in this spec.
- **A2** Every current native lifecycle status in sections 6 and 7 resolves to exactly one semantic
  stage. Tests enumerate the repository's owner enums and fail when a newly added status lacks a mapping.
- **A3** `reviewing`, `executing`, `verifying`, `integrating`, and `recovering` render as `◎`, `▶`, `◆`,
  `⇄`, and `↩︎` respectively, with their exact activity words.
- **A4** Blocked renders with text-form `⚠︎`; failed renders with `✘`; retry or recovery renders with
  text-form `↩︎`; reusable renders with `↻`.
- **A5** `⚠️` and `↩️` do not occur in lifecycle constants or golden output.
- **A6** In artifact-only views, plans display draft through approved as `○`, `◔`, `◑`, and `◕`, then
  executed as `✓`.
- **A7** A live executing approved plan displays `▶` and the word `executing` without changing the plan's
  stored `approved` status.
- **A8** A failed or integrity-invalid item displays `✘` even if a stale runtime field says it is active.
- **A9** A blocked item displays `⚠︎` even if its native state would otherwise be ready.
- **A10** In full human rows, glyph, id6, and status use the same resolved color and bold flag. Titles and
  paths are not lifecycle-colored.
- **A11** `NO_COLOR`, `TERM=dumb`, and non-TTY output contain no ANSI escapes and retain glyph plus word
  when Unicode is supported (Section 9.3's ASCII fallback applies when it is not). THIS IS UNCONDITIONAL,
  and the reason is a ruling rather than the current code's accident: `yaxr4i` OQ-01 was RESOLVED by the
  maintainer on 2026-09-10 as OPTION B, correct the document, so piped output STAYS human-readable and
  `--agent` remains the only way to get JSONL. The published "hard cutover" promise that non-TTY stdout
  adopts `aw.agent/v1` is being RETRACTED, not implemented. So a piped invocation still emits human text
  and this criterion applies to it in full.
  DO NOT RE-DERIVE THIS FROM THE CODE ALONE. Today's behavior and the ruling agree, but they agree for
  different reasons, and `docs/cli-output-contract.md` still carries the unretracted promise until
  `yaxr4i` E-05 lands. An implementer reading that document instead of this line would conclude A11 is
  conditional. It is not.
  AMENDED 2026-09-19 BY THE SECTION 12a RE-REVIEW (plan `n4xq3l`), at a HEAD where `yaxr4i` is
  `executed`. TWO CORRECTIONS: the first retires a warning, the second genuinely NARROWS this criterion.
  FIRST, THE DOCUMENTATION HAZARD IS GONE, so the paragraph immediately above is now history rather than
  a live warning. `docs/cli-output-contract.md` section 9 is headed "Automatic Non-TTY Migration Policy:
  RETRACTED 2026-09-19" and states "Piping or redirecting `aw` emits HUMAN-READABLE TEXT. `--agent` is
  the explicit and only way to obtain `aw.agent/v1` JSONL". The retracted sentence survives there only
  as explicitly-quoted retracted text (`docs/cli-output-contract.md:225`), and section 1 now says outright
  that "THE TTY-NESS OF STDOUT DOES NOT AFFECT THE MODE". So the document and the ruling agree, and an
  implementer may now read either.
  SECOND, AND SUBSTANTIVE: "UNCONDITIONAL" IS NO LONGER TRUE AS WRITTEN, because `yaxr4i` added the very
  flag layer this spec asked for and placed it ABOVE the environment. `--color` now OVERRIDES all three
  of this criterion's conditions. Measured 2026-09-19 against `term.should_color` on a non-TTY stream,
  each case returning False without the flag and True with it: `NO_COLOR=1` plus `--color` -> True,
  `TERM=dumb` plus `--color` -> True, plain non-TTY plus `--color` -> True. That is DELIBERATE and
  correct (`docs/cli-output-contract.md` section 1.1: "`--color` forces ANSI on", flag beats env), so
  this criterion is RESTATED rather than contradicted: A11 HOLDS FOR AN INVOCATION THAT PASSES NEITHER
  `--color` NOR `--no-color`. With `--color` passed, ANSI is EXPECTED and its absence would be the
  defect. The glyph-plus-word half remains unconditional at every tier (R9.3a.5); only the no-ANSI half
  acquires this qualifier.
  WHY THIS NARROWING DOES NOT WEAKEN THE ACCESSIBILITY GUARANTEE: `NO_COLOR` still outranks every
  IMPLICIT input and still outranks a user's pinned DEPTH (R9.3a.2), so no preference, capability
  detection, or configuration setting can defeat it. Only an explicit flag on the command line can, and a
  flag is the operator stating an intent for one invocation. That is the standard
  `docs/cli-output-contract.md` publishes and the one an implementation must satisfy.
- **A12** `AW_ASCII_ONLY=1` and `FORCE_ASCII=1` use the exact fallbacks in section 5 and retain words. Both
  variables are already implemented, so this criterion tests existing behavior.
  RE-POINTED 2026-09-19 BY THE SECTION 12a RE-REVIEW (plan `n4xq3l`). THE CRITERION HOLDS UNCHANGED IN
  SUBSTANCE: both variables are read in `term.should_unicode`, gated on the exact value `"1"`, and
  `yaxr4i` touched neither (it adds no ASCII flag, and `should_unicode` takes no `override` parameter,
  unlike `should_color`). Only the CITATION was stale. This line read `term.py:224-227`, and at this HEAD
  those lines sit inside `should_color`'s `NO_COLOR`/`FORCE_COLOR` block rather than the ASCII test,
  which lives in `term.should_unicode` (`agent_workflows/term.py:374` at this HEAD). CITED BY SYMBOL
  RATHER THAN BY LINE FROM HERE ON, deliberately: a line number in a spec rots on the next unrelated
  edit to the file above it, and a wrong line is worse than no line, because it sends a reader to code
  that looks relevant.
  ONE CONSEQUENCE FOR THE IMPLEMENTER, now that `--color` exists: there is NO `--ascii` flag, so the
  flag-beats-env layer `yaxr4i` introduced is COLOR-ONLY. Section 9.3's rule that `FORCE_COLOR` "MUST NOT
  force Unicode onto an incompatible stream" therefore extends to `--color` unchanged, and A12's env-only
  reasoning stays correct.
- **A12a** (R9.3a.1, R9.3a.2) One depth resolver exists, with exactly one definition, and the precedence
  chain of R9.3a.2 holds at every rung. Assert each rung explicitly: `NO_COLOR` with a pinned depth still
  yields plain text; a pinned depth overrides detection; detection overrides the default; the default is
  256. The `NO_COLOR`-beats-preference case is the one a well-meaning implementation is most likely to get
  backwards, so it must be asserted rather than assumed.
- **A12b** (R9.3a.3) The 16-color tier renders from an AUTHORED table, and the three separations survive
  it: `ready` is distinguishable from `done`, `blocked` from `failed`, and `waiting-input` from `blocked`.
  Assert the expected collapses TOO (the five active subtypes to one yellow, the grays to one neutral), so
  a later change cannot quietly re-expand them into colors 16-color terminals cannot show.
- **A12c** (R9.3a.4) A user can pin the depth through `aw config`, and an invalid value is REFUSED at
  validation with a message naming the accepted set. A user-supplied per-stage color override applies where
  implemented. Assert that a pinned depth does NOT defeat `NO_COLOR`.
- **A12d** (R9.3a.5) At all three tiers the glyph and the native word are present. Run the same fixture at
  256, at 16, and at none, and assert no state is distinguishable by color alone at any tier.
- **A13** `FORCE_COLOR=1` enables ANSI according to existing precedence but does not override ASCII stream
  capability.
  AMENDED 2026-09-19 BY THE SECTION 12a RE-REVIEW (plan `n4xq3l`), because "existing precedence" was a
  DELIBERATELY DEFERRED REFERENCE and the thing it deferred to has now shipped. This criterion was written
  pointing at whatever precedence `yaxr4i` would settle; that is settled and published, so the reference
  is replaced by the SHIPPED chain, highest first, which an implementation must satisfy at every rung:

  ```text
  --color / --no-color   >   NO_COLOR / FORCE_COLOR   >   TERM capability   >   stdout.isatty()
  ```

  THREE RUNGS MUST BE ASSERTED BY NAME, each measured 2026-09-19 against `term.should_color` on a non-TTY
  stream, and each one a case a plausible implementation gets wrong:
  (a) `FORCE_COLOR=1` with NO flag enables ANSI on a pipe (measured True). This is the original A13 and
  it still holds.
  (b) `FORCE_COLOR=1` with `--no-color` yields NO ANSI (measured False). THE FLAG WINS, so an
  implementation that treats `FORCE_COLOR` as the top of the chain is now wrong.
  (c) A FALSEY `FORCE_COLOR` neither forces NOR suppresses. `FORCE_COLOR` in `{"", "0", "false", "no",
  "off"}` (case-insensitive, stripped) falls through to ordinary detection, so `FORCE_COLOR=0` on a pipe
  is monochrome (measured False) and `NO_COLOR=1 FORCE_COLOR=0` stays monochrome on a pipe AND on a TTY
  (both measured False), because a falsey value does not cancel `NO_COLOR`. That falsey set is
  `term._FORCE_COLOR_FALSEY` and both `FORCE_COLOR` readings route through the single
  `term._force_color_is_forcing` predicate; splitting them re-creates a measured defect in which six
  `NO_COLOR`-set cells colorized.
  NOTE THE FALSEY RULE IS NARROWER THAN THE PUBLISHED TABLE, recorded here rather than resolved because
  it is not this spec's to decide. `docs/cli-output-contract.md` section 1.1 row 2 reads "`NO_COLOR` ...
  disables, UNLESS `FORCE_COLOR` is set; `FORCE_COLOR` (any non-empty value) enables", which by its own
  words makes `FORCE_COLOR=0` both cancel `NO_COLOR` and enable color. The SHIPPED code does NEITHER
  (measured above). The code's behavior is the better one on accessibility grounds and is the one this
  criterion ADOPTS; the document's wording is the stale artifact. AN IMPLEMENTER MUST FOLLOW THE CODE AND
  THIS CRITERION, NOT THAT ROW. Filed as a defect against the document, not against this spec.
  MUTUAL EXCLUSION IS A USAGE ERROR, NOT A PRECEDENCE QUESTION. Passing `--color` and `--no-color`
  together exits 2 on both the ordinary and the verbatim-forwarding paths (measured 2026-09-19, exit 2
  with `argument --color: not allowed with argument --no-color`), so no implementation needs a tie-break
  rule between them and none may invent one.
  THE ASCII HALF IS UNCHANGED AND NOW COVERS THE FLAG TOO: neither `FORCE_COLOR` nor `--color` may force
  Unicode onto an incompatible stream, because the color decision and the Unicode decision are separate
  resolvers (`should_color` versus `should_unicode`) and no flag reaches the second.
- **A14** `--agent` and `--json` output contains no ANSI and no schema-breaking decorated status value.
- **A15** Variation selectors survive ANSI stripping, truncation, snapshots, and copyable output.
- **A16** Tests cover the normal UTF-8 profile, ASCII mode, colored TTY, plain TTY, piped output, and
  `TERM=dumb`.
- **A17** Lifecycle presentation in attention, indexes, status commands, lint views, run views, and both
  runners resolves through the shared module. No second lifecycle color or glyph table remains.
- **A18** Generic event, finding-severity, priority, and gate visuals remain independent and are not
  accidentally remapped as lifecycle state.
- **A19** Work-kind has no effect on lifecycle resolution or presentation.
- **A20** Known artifact families with unknown statuses display `?` plus the native word and produce a
  validation diagnostic; types with no lifecycle use `·` or omit the lifecycle column.
- **A21** Full repository tests and `git diff --check` pass.

## 14. Examples

Color is described in comments because Markdown cannot reproduce terminal theme behavior.

```text
PLAN       ○  p1a2b3  draft          Define cache invalidation
PLAN       ◔  q2b3c4  to-review      Review runner analytics
PLAN       ◑  r3c4d5  reviewed       Await maintainer approval
PLAN       ◕  s4d5e6  approved       Ready to execute
PLAN       ▶  s4d5e6  executing      Running implementation
PLAN       ◆  s4d5e6  verifying      Running focused tests
PLAN       ⇄  s4d5e6  integrating    Merging verified lane
PLAN       ↩︎  s4d5e6  recovering     Correcting failed verification
PLAN       ⚠︎  t5e6f7  blocked        Gate: decision D-021
PLAN       ✘  u6f7g8  failed         Lane failed safely
PLAN       ✓  v7g8h9  executed       Verified and merged
PROMPT     ↻  w8h9j0  reusable       Release checklist
SPEC       ◇  x9j0k1  parked         Deferred design exploration
PLAN       ↪  y0k1m2  superseded     Replaced by z1m2n3
PLAN       ∅  a2n3p4  not-executed   Abandoned by decision D-022
```

ASCII mode:

```text
PLAN       Q  q2b3c4  to-review      Review runner analytics
PLAN       E  s4d5e6  executing      Running implementation
PLAN       !  t5e6f7  blocked        Gate: decision D-021
PLAN       X  u6f7g8  failed         Lane failed safely
PLAN       +  v7g8h9  executed       Verified and merged
```

## 15. Resolved decisions

- **D1:** Use single-character semantic markers, not multi-character badges, for lifecycle scanning.
- **D2:** Use `⚠︎` for blocked, `✘` for failed, `↩︎` for retry or recovery, and `↻` for reusable or
  recurring.
- **D3:** Use distinct active glyphs for review, execute, verify, integrate, and recover rather than one
  generic active symbol.
- **D4:** Keep the active subtypes one color so differentiation does not become visual noise.
- **D5:** Apply the resolved lifecycle treatment to both native status and artifact id6.
- **D6:** Preserve the status or activity word in human output and structured fields in machine output.
- **D7:** Treat live activity as a display overlay, never as an implicit stored transition.
- **D8:** Exclude work-kind from lifecycle presentation.
- **D9:** Centralize semantic data outside ANSI rendering and remove duplicate lifecycle tables.
- **D10:** Accept that Unicode ambiguous-width rendering varies by terminal, guarantee ASCII alignment,
  and keep width handling shared rather than allowing local guesses.

Added at review, 2026-09-13:

- **D11:** This spec is the single authority for lifecycle color and glyph and OVERRIDES the earlier
  per-surface palettes, on the maintainer's ruling. The authority covers DISPLAY only and changes no
  state, transition, exit code, or report section. Section 0.5 names what is superseded and requires the
  implementing plan to amend `25kzda` Section 5.6 rather than leave two live tables in the tree.
- **D12:** `needs_input` and `awaiting-human` both render as `waiting-input` (`…`, 214). Many native words
  to one stage is the design (Section 4.4a), and this keeps `6kwd2e` R4a.6 satisfied because 214 is
  distinct from `blocked`'s 208.
- **D13:** `ran` renders as `recovering` (`↩︎`, 220), NOT `done`. Rejected `done` because `25kzda` makes a
  `ran` item contribute non-success and exit 1, and because Section 7.2 of this spec already forbids
  styling unverified completion as verified success. Rejected a new 21st stage as disproportionate, and
  `unknown` because `ran` is precisely determined. Accepted cost: `↩︎` implies a pending retry when none is
  scheduled, so the printed word carries more weight in this row than in any other.
- **D14:** `unknown_outcome` renders as `failed`, not as this spec's generic `unknown`, because it is a
  real named terminal disposition owned by `c4gd2h` and collapsing it into the lookup-failure glyph would
  erase the distinction that spec's Section 0.0 exists to protect.
- **D15:** `quarantined` renders as `parked`. It is carried by a `- Quarantine:` field rather than a
  `- Status:` value, so a resolver reads it as a condition input per Section 8.

## 16. Open questions

### OQ-01: Must the accessibility lens's 256-color exception be widened, and does this spec owe a 16-color fallback?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution: RESOLVED 2026-09-13, AND THE QUESTION'S PREMISE WAS WRONG, which is the useful part. It
  assumed a conflict between this spec and the accessibility lens. THE LENS WAS SIMPLY STALE: the
  maintainer recalled having already ruled the ladder the other way, and DECISIONS **D42** confirms it,
  requiring terminal output to "degrade through 256/16/none", i.e. 256 as the TOP tier. That ruling was
  never written into the lens, whose body still read "Do not assume 256-color... prefer the 16 named
  colors". So the lens contradicted D42, and DECISIONS D133 had to be phrased as an `aw attention`-only
  "exception" to a rule D42 had already superseded. This spec was ALIGNED with D42 all along and needed no
  override.
  THREE THINGS FOLLOW, all ruled by the maintainer. (1) THE LENS IS CORRECTED, not overridden:
  `.aw/system/workflows/assess/lenses/accessibility.md` now states the 256/16/none ladder, folds D133's
  substance in as the general rule, adds that a user's explicit choice outranks detection while `NO_COLOR`
  outranks the choice, and keeps a short history note so a reader holding the old wording is not confused.
  (2) THIS SPEC CARRIES THE FULL LADDER, as new Section 9.3a with criteria A12a to A12d, including an
  AUTHORED 16-color palette whose acceptable collapses are named, because 11 distinct indices cannot be
  mapped mechanically onto 16 colors. (3) CONFIGURABILITY IS IN THIS SPEC TOO, not deferred.
  ON THAT LAST POINT THE REVIEWER WAS WRONG AND IS RECORDING IT: I proposed deferring configurability to a
  follow-on spec, arguing it was new surface. The maintainer asked what the advantage was, and there is
  none. Configured depth and detected depth answer ONE question at ONE seam, so splitting them means
  writing the resolver twice and reopening every call site's precedence. And detection cannot see the user:
  a terminal reporting 256-color says nothing about whether its user can distinguish 208 from 214, which is
  exactly the `blocked`/`waiting-input` pair, so deferring the override would strand the very users the
  lens protects. `config.CONFIG_SCHEMA` is also a declarative map, so a depth key is a schema entry rather
  than a mechanism, making the deferral argument weak on cost as well.
- Resolution or deferral rationale: THIS IS THE ONE CONFLICT THE OVERRIDE RULING DOES NOT SETTLE, because
  the counterparty is not a competing spec but a RUBRIC THIS SPEC SHOULD SATISFY.
  `.aw/system/workflows/assess/lenses/accessibility.md:56-63` says "Do not assume 256-color or truecolor;
  fall back through 16-color and then no-color" and "prefer the terminal's default fg/bg and the 16 named
  colors, which users theme for their own contrast", with a NARROW exception attributed to DECISIONS D133
  scoped to the `aw attention` human view alone. That lens is the binding rubric which spec
  `20260706-0000-01` Goal 9 delegates to, so it is not something this spec may simply override.
  THIS SPEC EXTENDS xterm-256 TO EVERY RENDERER IT NAMES (both runners, indexes, lint views, run viewers,
  status commands) and specifies NO 16-color degradation path at all. Two things follow and only a human
  can choose between them. EITHER the D133 exception is widened to every renderer here, in the same change
  that lands the resolver, accepting that a 16-color terminal gets approximate colors while the word and
  glyph still carry the meaning. OR this spec owes a 16-color fallback column beside its ASCII column,
  which is real added scope and a second table to keep correct.
  WHY IT BLOCKS: the lens is the standard a reviewer would hold an implementation to, so shipping the
  resolver without settling this leaves the implementing plan unable to satisfy both documents at once.
  THE ACCESSIBILITY COST IS ALREADY PARTLY MITIGATED and that is worth weighing: this spec never makes
  color the sole carrier (Section 11 item 2), so a user whose terminal renders 214 and 208 as the same
  orange still reads `waiting-input` versus `blocked` from the word and from `…` versus `⚠︎`. The residual
  risk is scanning speed on a dense board, not lost information.

### OQ-02: Should one of `needs_input` and `awaiting-human` retire once `run_gates` is wired?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: RAISED BY THE MAINTAINER AT REVIEW, who observed that the waiting
  states look near-identical. They are not identical (Section 4.4a sets out the three layers), but the
  observation exposed a genuine duplication UPSTREAM of presentation: two independent vocabularies exist
  for "a human is needed here", and the measured reason is that `run_gates.py` is UNWIRED TO BOTH RUNNERS
  (it greps to zero in each driver; spec `6kwd2e` Section 0.4 records the same fact). So `needs_input` and
  `awaiting-human` have never had to coexist in one running system, which is how two names for one
  situation get built without anyone choosing to.
  NOT BLOCKING, AND DELIBERATELY NOT THIS SPEC'S TO DECIDE. Collapsing two state vocabularies is a
  lifecycle change, which Section 3 excludes, and it would mean amending a reviewed spec's requirement
  from a presentation spec. Rendering both as `…` is correct today whether or not one later retires.
  WHAT WOULD CLOSE IT: whoever wires `run_gates` into the runners decides whether the gate status and the
  run disposition remain distinct or one becomes the single name. Recorded here so the observation is not
  lost with this review; this spec's tables need no change either way.
