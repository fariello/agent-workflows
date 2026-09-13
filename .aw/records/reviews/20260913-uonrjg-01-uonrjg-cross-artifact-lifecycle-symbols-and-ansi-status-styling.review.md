# Review findings: spec uonrjg

- Subject-Id: uonrjg
- Subject-Type: spec
- Reviewed-At: 2026-09-13
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `d09ba69d`, revisions committed at `e8a43d62`. Structural preflight `aw specs check`
CONFORMED (exit 0) before and after revision. PRE-REVIEW SNAPSHOT: `d09ba69d`, and it is ONE STEP LATE,
disclosed in its own commit message. The maintainer's priority/gate change was applied with `aw specs set`
BEFORE the snapshot, so the pristine `aw specs new` text is not in git history. It was not reconstructed
because undoing it would mean hand-deleting a `## Workflow history` record, which the setter owns.

THE DESIGN IS SOUND AND THE SPEC IS UNUSUALLY COMPLETE FOR A FIRST DRAFT. It correctly separates stored
status from live activity, keeps the native word authoritative with glyph and color as redundant aids,
reserves green for completion so readiness cannot masquerade as success, refuses animation and background
color, mandates text-presentation variation selectors, and states its own alignment limits honestly. Its
Section 15 already carried ten recorded decisions. None of that needed changing, and the findings below
are almost entirely about COVERAGE and about its relationship to other specs, not about its judgement.

THE MAINTAINER RULED THAT THIS SPEC OVERRIDES CONFLICTS, and the override is now recorded as Section 0.5
with its boundary stated: it governs DISPLAY only and changes no state, transition, exit code, or report
section. The one palette that genuinely needed overriding is `25kzda` Section 5.6, which is `approved`
AND `Blocks-Release: next` like this spec now is, and which mandates a five-color runner scheme that
collapses `running` with `verifying`, makes green mean verified, and folds needs-input into yellow. Two
weaker palettes were also cleared: a `superseded` spec's 16-color wizard rule, and the accessibility lens
(which is NOT overridable and is the subject of the open question below).

THE OVERRIDE RULING DID NOT DISPOSE OF THE BIGGEST DEFECT, and the maintainer's follow-up questioning is
what surfaced it properly. FIVE REAL STATUS WORDS APPEARED IN NO MAPPING TABLE: `ran` and `needs_input`
(`25kzda`'s normative outcome enum, with `needs_input` also a live constant in `run_gates.py`),
`awaiting-human` (`6kwd2e` R3.1, a spec advanced to `reviewed` earlier in this same session),
`unknown_outcome` (owned by `c4gd2h`, `implementing`), and `quarantined` (canonical `ipd-spec` Section
13.3, emitted by `ipd_lint`). Each would have resolved to `unknown` and printed a gray `?`. That is not a
conflict to override; it is a table row missing from a spec whose own Section 6 says "Falling through
silently to gray for a known status is a defect" and whose A2 demands tests that FAIL on exactly that.

ONE OF THOSE FIVE WAS A DECISION I GOT WRONG AND THE MAINTAINER CAUGHT. I proposed `ran` -> `done`. The
spec refutes it twice: `25kzda` states a `ran` item "contributes non-success to aggregate calculation and
therefore exit 1", and THIS spec's own Section 7.2 already says "Unverified completion MUST NOT be styled
as verified success merely because work was performed." Green would have painted an exit-1 item as
success, the precise collapse Section 5 exists to prevent. Ruled `recovering` instead.

I ALSO CORRECTED A CLAIM OF MY OWN THAT WAS SIMPLY FALSE. An earlier draft of Section 12a asserted that
`yaxr4i` OQ-01 (whether non-TTY stdout selects agent mode) was unresolved, and made this spec's A11
conditional on it. It is `- Status: resolved`: the maintainer ruled Option B on 2026-09-10, correct the
document, so piped output stays human-readable. A11 is now unconditional and cites the ruling, with the
warning that `docs/cli-output-contract.md` still carries the unretracted promise until `yaxr4i` E-05 lands.
Had that error survived, an implementer would have treated a settled contract as open.

THE MAINTAINER ASKED WHY THREE WAITING NAMES EXIST, and the answer turned out to be a finding rather than
an explanation. They are not peers: `waiting-input` is this spec's presentation stage, `needs_input` is one
of six gate statuses in `run_gates.ALL_GATE_STATUSES`, and `awaiting-human` is a non-terminal run
disposition. Many words to one glyph is the design. But the duplication the maintainer sensed is real and
UPSTREAM: `run_gates.py` is unwired to both runners (it greps to zero in each driver), so the two
vocabularies have never had to coexist, which is how two names for one situation get built without anyone
choosing to. Recorded as OQ-02 for whoever wires it, not resolved here.

ON EXECUTION ORDER, asked directly: implementing after `yaxr4i` is SAFE and is the recommended order,
and the reverse is the risk. `yaxr4i` adds the `--color`/`--no-color` surface A11 to A13 assume (`--color`
has no flag form today and `--no-color` is missing from 25 of 219 subcommands), rewrites the output
contract doc, and carries the ruling A11 depends on. Section 12a now REQUIRES a re-review of this spec
after `yaxr4i` executes, at the maintainer's direction, plus a declared `executed:yaxr4i` dependency edge.
File overlap with the four `render_stream.py` plans is deliberately NOT reported as a hazard: lanes are
isolated and merge through revalidation.

VERDICT IS `REVIEWED - OPEN QUESTIONS` RATHER THAN APPROVE-WITH-REVISIONS, for one reason: OQ-01 is
blocking, is genuinely the maintainer's, and cannot be resolved from repository evidence. Everything else
is fixed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-401 | HIGH | IN-SCOPE | C. acceptance criteria cover the requirements; A. correctness | `grep` for each token in the spec's tables returning 0; `run_gates.py:31` (`GATE_STATUS_NEEDS_INPUT`); `6kwd2e:252-254` (`awaiting-human`); `25kzda:1038-1042` (`ran`, `needs_input`); `c4gd2h` Section 0.0 (`unknown_outcome`); `ipd_lint.py:1019` (`quarantined`) | **FIVE REAL STATUS WORDS WERE IN NO MAPPING TABLE AND WOULD HAVE RENDERED AS A GRAY `?`.** `ran`, `needs_input`, `awaiting-human`, `unknown_outcome` and `quarantined` all exist in shipped code or in a normative spec enum, and none appeared anywhere in Sections 6 or 7. Under Section 8 rule 5 each resolves to `unknown`. This directly violates the spec's own Section 6 preamble ('Falling through silently to gray for a known status is a defect') and criterion A2, which demands tests that fail when a status lacks a mapping. In four of five cases the spec ALREADY contained the right stage and simply never listed the word, so this was missing coverage rather than a design gap. | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium | FIXED | Four rows added to Section 7.2 with per-word reasoning: `needs_input` and `awaiting-human` -> `waiting-input` (mechanical, and it satisfies `6kwd2e` R4a.6 because 214 differs from `blocked`'s 208); `ran` -> `recovering` (see SR-402); `unknown_outcome` -> `failed`; `quarantined` -> `parked` (noted as a `- Quarantine:` FIELD, so a resolver reads it as a Section 8 condition input rather than a native status). Each records its rejected alternatives. Recorded as D12, D13, D14, D15. |
| SR-402 | HIGH | IN-SCOPE | A. correctness; D. decisions with rationale | `25kzda:1049` ('contributes non-success to aggregate calculation and therefore exit 1'); this spec's own Section 7.2 ('Unverified completion MUST NOT be styled as verified success merely because work was performed') | **MY OWN PROPOSED MAPPING FOR `ran` WAS WRONG AND WOULD HAVE PAINTED AN EXIT-1 ITEM GREEN.** I recommended `ran` -> `done`. The maintainer rejected it, and the repository refutes it twice over: a `ran` item contributes non-success and exits 1 by default, and this spec's own Section 7.2 already forbids styling unverified completion as verified success. `done`'s green `✓` would have been exactly the readiness-versus-success collapse Section 5 exists to prevent. Recorded as a finding rather than a silent correction because a reviewer's own bad recommendation reaching a spec is the failure mode a review record exists to make visible. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | Ruled `recovering` (`↩︎`, 220) by the maintainer after being shown both citations. Section 7.2 carries the full reasoning including the four rejected options (`done` falsifies the exit code, `unknown` is for undeterminable states, `waiting-input` implies something is being asked, a 21st stage is disproportionate) and the accepted cost, that `↩︎` implies a pending retry when none is scheduled so the printed word carries more weight in this row than any other. Recorded as D13. |
| SR-403 | HIGH | IN-SCOPE | F. scope excludes what neighbours own; G. it can be planned from | `25kzda:997-1001` (the five-color scheme), `- Status: approved`, `- Blocks-Release: next`; `20260809-2211-01:370-375` (16 named colors), `- Status: superseded` | **THE SPEC REPLACED OTHER SPECS' PALETTES WITHOUT SAYING SO, INCLUDING ANOTHER RELEASE BLOCKER'S.** Section 1 named the code-level duplication (`term.py`, `attention.py`, `render_stream.py`) but no SPEC-level conflict. `25kzda` Section 5.6 is a normative color contract for the same runner surface and is both `approved` and release-gating; this spec contradicts it three ways (distinct glyphs for running versus verifying, green reserved for done, orange for blocked). Left unstated, two live and contradictory color tables would sit in the tree with nothing telling an implementer which governs. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New Section 0.5 records the maintainer's override ruling with an explicit boundary (display only; no state, transition, exit code or report section changes) and a table of what is superseded and why. It also REQUIRES the implementing plan to amend `25kzda` Section 5.6 and declare that spec in `Scope-Paths`, because an override recorded only in the winning spec leaves the losing spec still contradicting it. Recorded as D11. |
| SR-404 | HIGH | UNDER-SCOPE | F. honest limits; A. the spec satisfies its governing rubric | `.aw/system/workflows/assess/lenses/accessibility.md:56-63`; `20260706-0000-01:53-58` delegating Goal 9 to that lens; DECISIONS D133; `term.py:90-113` (`should_color` returns bool, no depth detection) | **THE SPEC ASSUMES 256-COLOR EVERYWHERE AGAINST A RUBRIC THAT FORBIDS ASSUMING IT, AND OFFERS NO FALLBACK.** The accessibility lens says 'Do not assume 256-color or truecolor; fall back through 16-color and then no-color', with a narrow exception scoped to `aw attention` alone per D133. That lens is the binding rubric spec `20260706-0000-01` Goal 9 delegates to, so it is NOT overridable the way a competing spec is. This spec extends xterm-256 to every renderer it names and specifies no 16-color path. Measured: `should_color` is boolean and the package has ZERO color-depth detection, so a fallback is a new mechanism, not a second table column. | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium-High | FIXED | ESCALATED, then RESOLVED 2026-09-13 with the premise corrected: there was no conflict, the LENS WAS STALE. The maintainer recalled ruling this already and DECISIONS D42 confirms it ("degrade through 256/16/none"), so 256 was always the intended top tier and D133 was an exception to a rule D42 had superseded. Three fixes: the lens now states the ladder (`accessibility.md`, D133 folded in as the general rule, user-choice-outranks-detection added, `NO_COLOR` still supreme); this spec gains Section 9.3a with the full ladder, one depth resolver, and an AUTHORED 16-color palette whose collapses are named; and criteria A12a-A12d were added. Configurability is IN this spec, not deferred: see D-405. |
| SR-405 | MEDIUM | IN-SCOPE | G. it can be planned from; dependency direction | `yaxr4i` `- Status: approved` declaring `term.py`, `cli.py`, `result_types.py`, `docs/cli-output-contract.md`; its measurement of `--no-color` missing on 25 of 219 subcommands and `--color` at 0 | **AN APPROVED, RUNNABLE PLAN OWNS THE OVERRIDE SURFACE THIS SPEC'S CRITERIA ARE WRITTEN AGAINST, AND THE SPEC NEVER MENTIONED IT.** A11 to A13 assert `NO_COLOR`, `FORCE_COLOR` and ASCII behavior 'according to existing precedence', but `yaxr4i` is about to CHANGE that precedence: it adds `--color` (which has no flag form at all today), adds `--no-color` to 25 subcommands, and rewrites `docs/cli-output-contract.md`. Landing this spec's resolver first would validate three criteria against a surface about to move. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New Section 12a classifies all eight approved plans touching these files (one dependency, four merge-friction, three compatible), answers the safety question directly (after `yaxr4i` is safe and recommended; the reverse is the risk), and imposes two obligations on the implementing plan: declare `executed:yaxr4i`, and RE-REVIEW this spec once `yaxr4i` lands, at the maintainer's direction. File overlap with the four `render_stream.py` plans is explicitly NOT reported as a hazard, since lanes are isolated and merge through revalidation. |
| SR-406 | MEDIUM | IN-SCOPE | A. correctness of a cited dependency | `yaxr4i` OQ-01 `- Status: resolved`, maintainer ruling 2026-09-10 Option B; contrasted with an earlier draft of this spec's Section 12a | **A REVISION I WROTE DURING THIS REVIEW ASSERTED A RESOLVED QUESTION WAS OPEN, AND MADE A CRITERION CONDITIONAL ON IT.** My first draft of Section 12a said `yaxr4i` OQ-01 (non-TTY stdout selecting agent mode) was unresolved, and rewrote A11 to be conditional. It is `- Status: resolved`: Option B, correct the document, so piped output stays human-readable and `--agent` remains the only route to JSONL. Left standing, an implementer would have treated a settled contract as an open question and possibly weakened A11 for a path that will keep emitting human text. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | A11 restored to unconditional, now CITING the ruling in its own text, plus a warning that `docs/cli-output-contract.md` still carries the unretracted promise until `yaxr4i` E-05 rewrites it, so anyone validating from that document rather than the ruling reaches the wrong answer. Section 12a point 3 rewritten and the correction disclosed there rather than silently amended. |
| SR-407 | MEDIUM | IN-SCOPE | A. the spec describes the current state; F. honest limits | `render_stream.py:98-111` measuring five of ten event glyphs as East Asian Width `A`, including `▶` U+25B6 and `◇` U+25C7; no `wcwidth`/`display_width` symbol anywhere in the package | **SECTION 9.4's WIDTH PROBLEM IS ALREADY MEASURED IN THE TREE FOR TWO OF THIS SPEC'S OWN GLYPHS, AND THE SPEC DID NOT CITE IT.** `render_stream.py` carries a width policy recording that `▶` (this spec's `executing`) and `◇` (this spec's `parked`) are ambiguous-width, that its own padding uses `len` and is therefore exact only for single-width glyphs, and that a true width helper was 'deliberately NOT built'. That is prior art agreeing with Section 9.4 and narrowing the work; without it an implementer might either re-derive the measurement or assume a helper exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Section 9.4 gains the prior art with citations, notes that the two overlapping glyphs make the ambiguity measured rather than hypothesized, records that NO width helper exists today so one would be new work, and points at the cheaper proven route (an ASCII table behind one capability flag, as `render_stream` already does) which satisfies 9.4 without a width helper. |
| SR-408 | MEDIUM | IN-SCOPE | E. open questions are dispositioned; F. honest limits | `run_gates` greps to ZERO in both `oc_runipd.py` and `agy_runipd.py`; `6kwd2e:144` recording the same fact; `run_gates.ALL_GATE_STATUSES`; `6kwd2e` R3.1 | **TWO INDEPENDENT VOCABULARIES EXIST FOR 'A HUMAN IS NEEDED' AND THE SPEC RENDERED BOTH WITHOUT NOTING THE DUPLICATION.** Raised by the maintainer, who observed the waiting states look identical. They are distinct (three different layers), but the reason two exist is measurable and worth recording: `run_gates.py` is unwired to both runners, so `needs_input` and `awaiting-human` have never had to coexist in one running system. A spec that maps both to one glyph without saying why they both exist invites a reader to conclude the table is redundant. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New Section 4.4a explains that many native words to one stage is the design (citing the four `blocked` variants as existing precedent), sets out the three layers in a table so the names are not read as peers, and records the upstream duplication with its measured cause. Raised as non-blocking OQ-02 for whoever wires `run_gates`, since collapsing two state vocabularies is a lifecycle change this spec's Section 3 excludes. |
| SR-409 | LOW | IN-SCOPE | A. measured claims; C. criteria are evaluable | `term.py:224-227` implementing `AW_ASCII_ONLY` and `FORCE_ASCII` | **A12's TWO ENVIRONMENT VARIABLES WERE UNVERIFIED IN THE RECORD.** The criterion names `AW_ASCII_ONLY=1` and `FORCE_ASCII=1` as though shipped. They ARE (both read in `term.py`), so the criterion is evaluable, but the spec asserted rather than cited it. Checked because the neighbouring A13 rests on `FORCE_COLOR` precedence that `yaxr4i` is actively changing, so which env behavior is settled and which is in flight matters to an implementer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Verified at review and recorded in this record rather than adding prose to the spec: both variables are shipped in `term.py`, so A12 rests on existing behavior while A13's precedence is the part `yaxr4i` moves. No spec edit needed; Section 12a already flags A13. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-401 | Should this spec override the conflicting palettes, or should each conflict be reconciled pairwise in the other specs? | OVERRIDE, on the maintainer's explicit ruling, but with the boundary stated and an obligation on the implementing plan to amend the superseded spec. | (a) Pairwise reconciliation, rejected by the maintainer as slower and because it would mean editing an approved release-gating spec's normative section from several directions. (b) Override silently, rejected as the defect SR-403 identifies: two live contradictory tables with nothing naming the winner. (c) Override without bounding it, rejected because an unbounded 'this spec wins' would appear to license changing states and exit codes, which Section 3 excludes. | the maintainer's ruling of 2026-09-13; `25kzda:997-1001` versus this spec's Section 5; Section 3's existing non-goals | no |
| D-402 | The five orphan words could be added as mappings, or the spec could stay silent and let them resolve to `unknown`. | ADD ALL FIVE, with the two mechanical ones cited and the three judgement calls ruled by the maintainer. | (a) Stay silent, rejected because it violates the spec's own Section 6 preamble and A2, and would ship five states rendering `?`. (b) Add only the two obvious ones and defer three, offered to the maintainer and declined in favour of deciding all five now. (c) Decide all five on my own authority, rejected for the three ambiguous ones because they are presentation judgements about states the maintainer understands better, which is why they were asked. | the spec's Section 6 preamble and A2; each word's owning spec or shipped constant; the maintainer's answers of 2026-09-13 | yes |
| D-403 | Is `unknown_outcome` this spec's generic `unknown`, given both contain the word? | NO. It maps to `failed`, because it is a real named terminal disposition and `unknown` means undeterminable. | (a) Map to `unknown`, rejected: it would erase the distinction `c4gd2h` Section 0.0 exists to protect (that section exists BECAUSE two definitions of this token already collided once in this repository), and it would make a determined outcome look like a lookup failure, which is the very defect SR-401 is fixing. (b) Leave unmapped, rejected as the same defect. | `c4gd2h` Section 0.0's term-ownership clause; this spec's own definition of `unknown` as 'State cannot be determined safely' | yes |
| D-404 | Should the file overlap between this spec and eight approved plans be reported to the maintainer as an execution hazard? | NO for seven of them, and NOT as a file-overlap hazard for any. Only `yaxr4i` was raised, and as a sequencing dependency. | (a) Report all eight as contention, rejected because the runner isolates each execute turn in its own worktree and returns changes through the merge-and-revalidate gate, so file overlap is not a runtime hazard; reporting it would waste the maintainer's time on a solved question. (b) Report none, rejected because `yaxr4i` genuinely changes the surface three criteria are written against, which is a real ordering constraint rather than an overlap. | each plan's declared `- Scope-Paths:`; `yaxr4i`'s own 'prior art, not a conflict' note on `STATUS_COLOR_256`; the runner's worktree isolation and merge gate | yes |
| D-405 | Should configurability of the color scheme and depth live in this spec, or be deferred to a follow-on spec? | IN THIS SPEC (R9.3a.4). The reviewer proposed deferring; the maintainer asked what the advantage was, and there is none. | (a) Defer to its own spec, REJECTED and this was MY OWN recommendation, withdrawn: configured depth and detected depth answer ONE question at ONE seam, so deferring means writing the resolver with a single input and reopening it plus every call site's precedence later. Worse on accessibility grounds, detection CANNOT SEE THE USER - a terminal reporting 256-color says nothing about whether its user can distinguish 208 from 214, which is precisely this spec's `blocked`/`waiting-input` pair - so deferring strands the users the lens exists to protect. My cost argument was also weak: `config.CONFIG_SCHEMA` is a declarative `ConfigKeySpec` map, so a depth key is a schema entry, not a mechanism. (b) Ship 256-only and add tiers later, rejected for the same reopening cost across every renderer. | DECISIONS D42's 256/16/none ladder; `config.CONFIG_SCHEMA`'s declarative shape; `term.should_color` being boolean with zero depth detection; the 208/214 adjacency in Section 5 | yes |

### Deferred and open

None. Nine findings, all FIXED; none deferred, none REPLAN, no question left open. SR-404 was escalated as
blocking OQ-01 and then RESOLVED in the same session once the maintainer identified that the lens, not this
spec, was the stale document (see the SR-404 row and D-405).

WHAT CHANGED OUTSIDE THIS SPEC as a result, recorded because a review that edits a shared rubric must say
so: `.aw/system/workflows/assess/lenses/accessibility.md` was corrected to state DECISIONS D42's
256/16/none ladder, to fold D133's substance in as the general rule rather than an `aw attention`-only
exception, and to add that a user's explicit choice outranks detection while `NO_COLOR` outranks the
choice. That file is INSTALLED INTO EVERY MANAGED REPO by the engine, so the correction reaches downstream
consumers on their next install; that is the intended blast radius, and it is why the paragraph keeps a
short history note rather than silently replacing the old wording.

### Honest limits of this review

- NOTHING IN THIS SPEC IS IMPLEMENTED, so every criterion is prospective. This review verified the spec's
  CITATIONS and its relationship to other specs and to shipped code; it could not verify the design by
  execution.
- I DID NOT AUDIT ALL 21 CRITERIA AGAINST THE CODE. A11, A12 and A13 were checked because `yaxr4i` moves
  their surface; A2's coverage was checked exhaustively because it is the criterion the orphan words
  violated. The rest were read for refusability, not measured.
- THE GLYPH AND COLOR CHOICES THEMSELVES WERE NOT SECOND-GUESSED beyond the two cases where the repository
  contradicted them (`ran` and the 208/214 adjacency). Whether `◔` reads as 'awaiting review' to a new user
  is an empirical question no review can settle.
- 214 VERSUS 208 IS AN ADJACENT-ORANGE PAIR and may be indistinguishable to some users. Acceptable here
  only because the word always prints, which is the spec's own accessibility rule, but the mitigation is
  the word rather than the color.
- THE OVERRIDE IS RECORDED, NOT YET EFFECTED. `25kzda` Section 5.6 still says the opposite until the
  implementing plan amends it, which Section 0.5 now requires.
