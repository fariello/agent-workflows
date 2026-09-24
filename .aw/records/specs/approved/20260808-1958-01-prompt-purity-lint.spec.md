# Spec: prompt-purity lint (`aw prompts check`)

- Date: 2026-08-08
- Status: approved
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: a recurring maintainer correction ("prompts are supposed to be prompts, not instructions and prompts") that the existing AGENTS.md rule states but nothing enforces or reminds at author time.
- Relation to prior work: reuses `agent_workflows/artifact_core.py` (the `Drift`/`render_agent_drift`/`drift_exit_code` `--check` convention). Independent of, but stylistically aligned with, the attention-registry spec (`20260808-1945-01`).

## 1. One-line summary

A deterministic, stdlib-only checker (`aw prompts check`) that scans `.agents/prompts/**/*.md` and fails when a prompt file contains anything that is NOT the prompt itself (operator-directed instructions, upload/paste directions, delimiter markers, or non-comment content before the prompt body), so a staged prompt is always select-all-and-upload ready with nothing to strip.

## 2. Problem / motivation

AGENTS.md already requires (lines 15-17) that a prompt for another AI "contains ONLY the prompt itself, addressed to that AI. Put NO instructions for the user inside it" and be "self-contained, so the user can select-all-and-copy it." But:

- The rule is stated, not ENFORCED, and not surfaced at author time, so it is repeatedly violated (e.g. an "Operator note (do not upload this section)" header, "upload everything below the marker" directions, `=== BEGIN UPLOAD-READY PROMPT ===` delimiters). Each violation forces the maintainer to repeat the correction and forces a manual re-edit.
- A prompt file that mixes instructions-to-the-user with the prompt is, by the maintainer's definition, "not a prompt; it is something else." The failure is categorical, not stylistic.
- There is NO `aw` verb for the prompts tree at all today (unlike `aw plans` / `aw research`), and prompt filenames are only checked by `plan-names`. Nothing checks prompt CONTENT.

The fix: a deterministic content lint that makes prompt-purity a machine-checkable contract, plus a codified convention for the ONE kind of non-prompt content that is permitted (a leading HTML-comment metadata line, which is invisible when pasted into a chat).

## 3. The prompt-purity contract (what "just a prompt" means)

A conforming prompt file under `.agents/prompts/` (excluding the gitignored `local/` lane):

- P1 Its VISIBLE content (everything a chat would render when the file is pasted) is addressed to the target AI and is the prompt only.
- P2 It contains NO operator-directed / user-directed instructions: no "copy this", "paste below", "upload everything below", "do not upload", "operator note", "(not part of the prompt)", "run this against", or similar meta-instructions telling a human how to USE the prompt.
- P3 It contains NO delimiter/marker lines whose purpose is to separate a prompt region from a non-prompt region (e.g. `=== BEGIN UPLOAD-READY PROMPT ===`), because a pure prompt needs no such boundary.
- P4 The ONLY permitted non-prompt content is a SINGLE leading HTML comment carrying pipeline metadata (`<!-- aw-prompt: ... -->`), placed before the first visible line. HTML comments are invisible when pasted into a chat, so select-all-and-upload still yields a clean prompt. No YAML front-matter (it renders as text or as a stray table in many chat UIs and is not invisible).
- P5 The first VISIBLE line (after any leading `aw-prompt` HTML comment) is the start of the prompt body.

This contract replaces the current prompts-README expectation of YAML front-matter on prompt files (see Section 7 and OQ3): pipeline metadata moves into the leading HTML comment so the file stays pasteable.

## 4. Goals

- G1 `[Must]` Provide `aw prompts check` (with `--agent` machine-readable output and a nonzero exit on any violation), reusing the `Drift`/`render_agent_drift`/`drift_exit_code` convention, so it is pre-commit/CI wireable.
- G2 `[Must]` Detect P2 (operator-directed phrasing), P3 (region-delimiter markers), and P4/P5 (disallowed non-comment content before the prompt, e.g. YAML front-matter or a user-directed heading) deterministically, with LOW false positives.
- G3 `[Must]` Codify the leading-HTML-comment metadata pattern (P4) in AGENTS.md and `.agents/prompts/README.md` as the ONLY permitted non-prompt content, so authors have a rule that matches the lint.
- G4 `[Should]` Provide an author-time REMINDER: a one-line pointer in the prompts README and (if a prompts-authoring workflow exists) in that workflow, plus a clear violation message that tells the author exactly what to remove.
- G5 `[Must]` Stdlib only; zero runtime deps; Python 3.9; ship in the importable package as `aw prompts check` and `python -m agent_workflows prompts check`.
- G6 `[Should]` Wire `aw prompts check` into the repo's own pre-commit and the setup-repo secret/format checks family, and (in this repo) run clean on all existing prompts after the review prompt fix.

## 5. Non-goals

- NOT judging prompt QUALITY, tone, or effectiveness; only PURITY (no non-prompt content).
- NOT checking prompt filenames (that is `plan-names`) or lifecycle disposition (directories).
- NOT scanning the gitignored `local/` quarantine lane (raw/WIP prompts live there deliberately).
- NOT scanning `.agents/docs/prompts/` (the evergreen copy-paste LIBRARY) unless a later phase opts it in (OQ4).
- NOT an LLM-based classifier; the check is a small, deterministic ruleset (phrase list + structural rules).

## 6. Functional design

- A new module `agent_workflows/prompts_lint.py` with `run(args) -> int`, wired at the two CLI edit points in `cli.py` (`_build_parser` adds a `prompts` subparser with a `check` subcommand; `_dispatch` routes it). This also establishes the `aw prompts <verb>` namespace for future prompt tooling.
- `aw prompts check [dir]`:
  - Walks `.agents/prompts/**/*.md` via `artifact_core.iter_scan_files` (scoped to the prompts root), EXCLUDING `local/` and `README.md`.
  - For each file, applies the ruleset:
    - R1 (P4/P5) The file may begin with at most one `<!-- aw-prompt: ... -->` comment; any OTHER content before the prompt body (YAML `---` front-matter, a `# Operator ...` heading, etc.) is a violation.
    - R2 (P2) Any line matching the operator-directed phrase set (case-insensitive; a curated, extensible list: "operator note", "do not upload", "upload everything", "upload this", "copy this", "paste below", "paste this", "not part of the prompt", "run this against", "run separately and compare", "save the returned", "move this prompt to", etc.) is a violation. The list lives in one place with a documented extension mechanism (like the research `KINDS` vocab).
    - R3 (P3) Any region-delimiter marker line (e.g. a line that is only `=`/`-` fences framing a "PROMPT" label, or contains "BEGIN ... PROMPT"/"END ... PROMPT") is a violation.
  - Emits one `Drift(location=file:line, rule=<R1|R2|R3>, detail=<the offending text/why>)` per finding; `--agent` prints tab-separated records; exit `drift_exit_code` (0 clean / 1 violations). Exit 2 reserved for could-not-run.
  - Human (non-`--agent`) mode prints a short remediation hint per file: "Move pipeline metadata into a leading `<!-- aw-prompt: ... -->` comment and delete user-directed instructions; the file must be pure prompt."
- The phrase set is intentionally conservative to keep false positives low; a legitimate prompt that must quote such a phrase can be handled by OQ2 (an allow mechanism).

## 7. Convention change (docs)

- AGENTS.md "Writing prompts for another AI": add the HTML-comment metadata pattern (P4) as the sanctioned way to carry lifecycle metadata without breaking pasteability, and reference `aw prompts check` as the gate.
- `.agents/prompts/README.md`: REPLACE the "Prompt files are named ... front-matter `Kind:`" expectation with the leading-`aw-prompt`-HTML-comment convention (Section 3), and state the purity contract + the checker. (This is the one substantive convention change; OQ3 confirms whether any tooling reads the old YAML front-matter and must be updated in the same phase.)

## 8. Requirements

- F1 `aw prompts check` implements R1-R3, `--agent`, and the exit convention (G1, G2).
- F2 The operator-directed phrase set is single-sourced and extensible with a documented mechanism.
- F3 `local/` and `README.md` are excluded; `.agents/docs/prompts/` is out of scope in v1.
- F4 AGENTS.md + prompts README codify P4 and reference the checker (G3).
- F5 Running `aw prompts check` on this repo after the fix exits 0 (the review prompt already conforms).
- N1 Stdlib only, zero deps, Python 3.9. N2 ships in the package as `aw prompts check`. N3 reuses `artifact_core`; no fork. N4 deterministic; stable across runs. N5 no em/en dashes in authored output.

## 9. Acceptance criteria

- A1 A prompt file with an "Operator note (do not upload this section)" header fails with an R2 (and R1) violation naming the line.
- A2 A prompt file with a `=== BEGIN UPLOAD-READY PROMPT ===` marker fails with an R3 violation.
- A3 A prompt file that begins with YAML `---` front-matter fails with an R1 violation; the same file with that metadata moved into a leading `<!-- aw-prompt: ... -->` comment passes.
- A4 The current `.agents/prompts/pending/20260808-1948-01-...external-review.md` (post-fix) passes clean.
- A5 A normal prompt that legitimately says "return a downloadable .md file" does NOT trip R2 (low false positive on target-AI-directed instructions vs user-directed instructions).
- A6 `--agent` emits tab-separated `location<TAB>rule<TAB>detail`; exit 1 with violations, 0 clean.
- A7 Full unittest suite green with new tests covering R1-R3, the exclusions, and A5's false-positive guard.

## 10. Constraints and dependencies

- Depends on `artifact_core` and the CLI wiring pattern. Establishes the `aw prompts` namespace (none exists today). The convention change (Section 7) must land WITH the checker so docs and gate agree. The distinction R2 must draw (user-directed vs target-AI-directed instructions) is the main correctness risk and drives the phrase-set curation.

## 11. Risks and open questions

- OQ1 The precise operator-directed phrase set and how to keep false positives low while catching real violations. Should R2 be phrase-list-only, or also structural (e.g. a second-person imperative in a section titled for the operator)?
- OQ2 An escape hatch for a prompt that must legitimately quote a banned phrase (e.g. an inline `aw-prompt-allow: <rule>` comment, or fenced-code exemption). Needed, or YAGNI?
- OQ3 Does any existing tool READ the prompts YAML front-matter today (does replacing it with the HTML comment break anything)? If so, update in the same phase. (Initial read: only `plan-names` touches prompts, and it checks filenames, not front-matter.)
- OQ4 Should `.agents/docs/prompts/` (the reusable library) also be purity-checked, or is a library prompt allowed to carry usage notes? (Leaning: out of scope; library prompts may document usage.)
- OQ5 Should `check` gain a companion `--fix`/`aw prompts scaffold` that emits a conformant skeleton (leading `aw-prompt` comment + body) so authors start pure by construction? (Leaning: a later phase; scaffold prevents the error better than lint catches it.)
- OQ6 Verb placement: `aw prompts check` (new namespace, recommended) vs folding into `plan-names` or a setup check. (Leaning: new `aw prompts` namespace, matching `aw plans`/`aw research`.)

## 12. Out-of-scope / future

- `aw prompts scaffold` (pure-by-construction authoring) and `aw prompts` lifecycle verbs (move between disposition dirs) are natural future members of the namespace, out of scope here.
- Applying the purity notion to `.agents/docs/prompts/` (OQ4).

## 13. Next step

Drafted to `Status: to-review` and paused. Next: review (internal `/plan-review` or external, maintainer's call), then HUMAN APPROVAL before authoring the IPD. Do NOT begin an IPD until approved.

## Workflow history
- 2026-08-08 /spec (opencode its_direct/pt3-claude-opus-4.8-1m-us): drafted the prompt-purity-lint spec to Status: to-review, prompted by the maintainer's recurring "prompts must be just prompts" correction; codifies the leading-HTML-comment metadata pattern and an aw prompts check gate.
- 2026-08-08 migrated (aw specs): normalized status to `to-review` (was: to-review (2026-08-08; drafted by opencode, awaiting review and human approval). Design rationale + functional contract; a follow-on IPD implements it. Open que)
- 2026-08-18 reviewed (aw specs): I reviewed.
- 2026-08-18 approved (aw specs, --by-human): I approved this message.
