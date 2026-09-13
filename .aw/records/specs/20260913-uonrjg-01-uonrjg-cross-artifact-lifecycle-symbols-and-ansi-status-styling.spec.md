# Spec: Cross-artifact lifecycle symbols and ANSI status styling

- Date: 2026-09-13
- Status: to-review
- Priority: high
- Blocks-Release: next
- Id: uonrjg
- Author: aw specs new
- Scope: A single accessible glyph and ANSI vocabulary for artifact statuses, artifact id6s, and live runner activity across human terminal views.

## Workflow history
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
| stale projected `abandoned?` or another inference | unknown |

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
  when Unicode is supported.
- **A12** `AW_ASCII_ONLY=1` and `FORCE_ASCII=1` use the exact fallbacks in section 5 and retain words.
- **A13** `FORCE_COLOR=1` enables ANSI according to existing precedence but does not override ASCII stream
  capability.
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

There are no open design questions in this spec.
