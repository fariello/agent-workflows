- Id: 6b9zd9
- Status: open
- Blocks-Release: next
- Set: modelvocab
- Priority: high
- Work-Kind: bug
- Summary: Research model vocabulary is a closed list in code, so aw refuses correct artifacts from any new model or variant (Gemini 4, GPT-5.5, DeepSeek, a new reasoning tier); make it an editable data file with an add verb and a warn-not-refuse validator

## Workflow history
- 2026-09-20 created (aw backlog): Research model vocabulary is a closed list in code, so aw refuses correct artifacts from any new model or variant (Gemini 4, GPT-5.5, DeepSeek, a new reasoning tier); make it an editable data file with an add verb and a warn-not-refuse validator

MEASURED 2026-09-20 while filing three skill-runtime research reports. The third was written by
Google Gemini 3.1 Pro with variant "Deep Think". `aw research mv i5gj61 --model gemini31prodeepthink`
REFUSED:

    error: unknown model 'gemini31prodeepthink'; did you mean 'gemini31pro'?

There is no way to record the true author, so the artifact is filed with an EMPTY `model:` facet in a
three-model comparison set whose other two members ARE named. The provenance the field exists to carry
is simply lost.

## The defect

`agent_workflows/research_contract.py:109` defines `MODELS` as a frozenset, and `normalize_model`
(line 246) is a bare membership test with NO escape hatch. Every one of these is refused TODAY:
Gemini 4, GPT-5.5, DeepSeek 4, any future reasoning tier of an existing family, and any model from a
vendor not already enumerated. The maintainer's objection, 2026-09-20: "That seems extremely limiting
and short-sighted."

## Why the enumeration is the wrong shape here

`<kind>` (research-report, findings, reconciliation-report) is a genuinely closed vocabulary: THIS
repo defines those categories and they change only when the repo changes. `<model>` is an OPEN set
the OUTSIDE WORLD extends without asking. Vendors ship new models and new reasoning variants
continuously. Treating both as one kind of enumeration is the error.

## The gate does not buy what it claims

Its stated purpose (research_contract.py:104-108) is to prevent filing a report under a model that
did not write it. But the check only verifies a token is ON A LIST, never that it is CORRECT: a
Sonnet report can be labelled `gpt56` today and nothing objects. So the closed list REFUSES an
unknown-but-true model while PERMITTING a known-but-false one. It protects against the wrong failure.

What it legitimately does buy, and what the fix must keep: consistent spelling, so `gpt-56` and
`gpt56` do not split one model across two names in a comparison set, and typos stay visible.

## Measured 100 percent failure rate on new models

The list has been extended exactly once, 2026-09-08 (`6f628533`, awmetastore ingest). That commit's
own rationale records the SAME failure: the contract "blocked ingesting real artifacts" because a
genuine high-effort Sonnet or Gemini report COULD NOT BE NAMED. So this is the second occurrence of
one defect, and both times a correct artifact was refused. Every new model encountered so far has hit
it.

## Required fix (maintainer-specified, 2026-09-20)

1. WARN, DO NOT REFUSE. An unrecognized model is recorded with a warning, not rejected. This inverts
   the failure mode from "correct artifact refused" to "new model recorded, flagged for review", which
   is the right direction when the input comes from outside the repo. `MODEL_NORMALIZATIONS` keeps
   doing the real work of collapsing spelling drift.
2. THE WARNING MUST TEACH THE FIX. It must state how to add the model or variant, naming the exact
   command. A warning that only says "unknown model" leaves the user where this defect found them.
3. A CLI VERB TO ADD ONE. Adding a model must be a one-command act from the terminal, not a source
   edit plus a spec amendment. (Today the extension mechanism at research_contract.py:100 requires
   editing Python AND amending spec section 5.4 in the same change, which is why this was escalated
   to the maintainer mid-task instead of being fixed in passing.)
4. THE KNOWN LIST MOVES OUT OF CODE into an editable config/data file. Precedent already in the repo:
   `.aw/config/local-leaks-allowlist.toml` is a tracked, hand-editable, commented data file read by a
   3.9-safe minimal TOML reader, with a per-user additive layer beside it. Note there is currently NO
   `agent_workflows/data/` directory and NO package data in `pyproject.toml` (packages = only
   `agent_workflows`), so shipping a package-default data file needs a packaging decision; the
   `force-include` block at pyproject.toml:130 is the existing hook.

## Consequences to handle in the design

- A typo (`sonnet5hgih`) would now be RECORDED rather than rejected, so the warning must be loud and
  `aw research index --check` should report an unrecognized model as drift, keeping a mechanical
  surface that catches it.
- Spec `20260730-2152-01-agents-artifact-organization` requirement E3 makes `<model>` an ENUMERATED
  `[Must]` and section 5.4 carries the vocabulary plus the extension rule. E3 ITSELF must change, not
  just the token list, so this is a real spec amendment and not a list edit.
- The reasoning-effort-in-identity decision from the 2026-09-08 amendment is CORRECT and must survive:
  two efforts of one model must not collide on one name.

## Blocked work

`.aw/records/research/20260920-hostskill-02-i5gj61-agent-skill-runtimes-research.research-report.md`
carries an empty `model:` that should read `gemini31prodeepthink`. Fix it when this lands. The
interim unblock (adding the single token under the existing mechanism) is tracked separately.
