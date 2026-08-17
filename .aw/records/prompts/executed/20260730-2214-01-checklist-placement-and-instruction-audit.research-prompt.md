You are a senior researcher in human-and-LLM instruction design and prompt engineering, with hands-on knowledge of how current AI coding agents (both strong frontier models and faster/smaller models) read and comply with long instruction documents. Be rigorous, evidence-driven, and skeptical: challenge the premise, cite sources where they exist, distinguish established evidence from informed inference, and say plainly where the evidence is thin or absent. Do not flatter and do not agree by default. Return your answer as a single downloadable Markdown (`.md`) file.

## Background you need

A tool-agnostic framework defines a document type called an IPD (Implementation Plan Document): a plan an AI coding agent authors, a human approves, and then an AI coding agent EXECUTES step by step, committing code and pasting real test output. Two checklists live inside each IPD:

1. A `## Detailed Implementation Checklist (TODO)`: the EXECUTION plan (tickable `- [ ]` items covering every action, edit, test, and commit). The executing agent ticks these as it works. It is the primary progress tracker for an agent that has no external task tool.
2. A `## Validation and cross-check` checklist: a SEPARATE verification pass whose items map 1:1 to the execution items and demand concrete per-item evidence (command output, file:line, artifact paths) BEFORE the agent may claim the work done.

The framework's current convention places the EXECUTION checklist near the TOP of the document (right after a short Goal, before the findings/rationale sections) and the VALIDATION checklist near the END (right before the approval/completion gate). This placement was adopted on intuition, NOT on evidence: the maintainer assumed that an execution checklist near the top and a verification checklist near the bottom would be followed more reliably by an LLM that is "prone to messing things up from time to time." The maintainer now wants that assumption tested, because the convention is about to be hardened into always-loaded, shipped instructions that affect every future plan and every consumer repository, and because a capable model authoring these documents recently DRIFTED the execution checklist to the bottom despite the written rule, suggesting the current instructions do not reliably produce or enforce the intended placement.

The executing and authoring population spans a wide capability range: strong frontier models (e.g. large Claude, GPT, and Gemini tiers) and deliberately faster/smaller models (e.g. small/flash tiers) that are more prone to skipping steps, declaring completion prematurely, and losing mid-document instructions.

## What to determine

Answer TWO questions. Keep them distinct so the answers stay honest.

### Q1. Evidence on checklist placement and ordering for reliable LLM compliance

For a LONG instruction/plan document that an LLM agent must both (a) EXECUTE faithfully and (b) then VERIFY honestly, what does the evidence and known model behavior say about the optimal PLACEMENT and ORDER of an execution checklist versus a verification checklist? Address at least:

- Serial-position / primacy-recency effects and "lost in the middle" behavior in long-context LLMs: which document regions get the most reliable attention, and how does that bear on where each checklist should sit? Cite primary sources (papers, model-provider guidance, reproducible tests) with dates; distinguish what is empirically established from plausible inference.
- Read-order vs act-order tension: when an agent reads a document top to bottom and THEN acts, is the execution checklist better near the top (framing/priming), near the bottom (most-recently-read before acting), duplicated in both places, or restated just before execution? What does the evidence say, and how does it differ between strong and weak/fast models?
- Compliance and premature-completion: does placing the verification checklist LAST measurably reduce the "claimed done without doing every step" failure, or is position secondary to other factors (explicit per-item evidence requirements, a hard gate, an external todo tool, re-reading)? Identify what actually drives compliance, ranked.
- Alternatives to weigh explicitly: (i) execution-top / validation-bottom (the current convention); (ii) execution-bottom (last thing read before acting); (iii) execution checklist duplicated top-and-bottom; (iv) a single merged checklist; (v) execution restated immediately before each action; (vi) placement made machine-checkable/enforced by tooling rather than by prose. Give the trade-offs of each for both strong and weak/fast models.
- State clearly: is the maintainer's top/bottom intuition supported, contradicted, or unresolved by the available evidence? If unresolved, say what specific experiment would settle it.

### Q2. Audit of the actual instruction set (attached)

Several files from this framework are attached VERBATIM (their names and roles are listed below). They are the authoring instructions that PRODUCE an IPD and the review instructions that CHECK one. Scrutinize them as an expert editor whose goal is faithful execution by diverse agents WITH appropriate discretion (strong rules obeyed as strong; strong-guidance not misread as absolute; and vice versa). For the attached set, report:

- Placement/ordering: does the wording reliably PRODUCE the intended checklist placement, and reliably CATCH a misplaced checklist in review? Given that a capable model drifted the execution checklist to the bottom despite the rule, identify WHY the current wording failed and what wording or structure would prevent it (for both authoring and review).
- Any other instructions likely to be misread, skipped, or faked by a weak/fast agent; any strong-guidance likely to be over-literalized by a strong agent; any contradictions or ambiguous antecedents. Quote the offending text and cite the file and approximate location.
- Concrete rewrite recommendations: for each problem, give the specific replacement text or structural change, and say whether it should be a prose rule, a template-structural change, a machine-checkable rule (e.g. a linter that asserts section order), or a combination. Prefer the SIMPLEST change that reliably works, and note where a tool would beat prose.
- Whether the two-checklist design itself is sound, over-engineered, or under-specified for the stated goal (faithful execution + honest verification across diverse agents). Recommend keeping, simplifying, or restructuring it, with reasons.

The attached files (each provided verbatim; treat their own punctuation as the source's, and do not assume anything about the framework beyond what they and this prompt state):

- `ipd.md` (the IPD authoring TEMPLATE: section structure, the two checklists, the completion rule, and the split-into-a-Set guidance).
- `ipd-spec.md` (the canonical spec: what an IPD must contain, section order, the mandatory checklists, and the completion rule).
- `plan-review.md` (the single-file plan-review workflow: how a reviewer assesses a plan, including the dual-checklist reviewer duty and the engineering rubric).
- `03-resolve-and-finalize.md` and `review-rubric.md` (the multi-file plan-review variant's finalize step and rubric, kept in parity with the single-file workflow).

If any expected attachment is missing, say so explicitly and answer as far as the available material allows.

## How to answer

- Prefer primary sources (papers, model-provider documentation, reproducible experiments) over blog hearsay; date every claim and flag anything you could not verify.
- Separate ESTABLISHED EVIDENCE from INFORMED INFERENCE from OPINION, and label which is which.
- Be explicit about negative and unknown results; "the evidence does not settle this; here is the experiment that would" is a valuable finding.
- Where you make a recommendation, state the capability tier(s) it is optimized for and any case where it would backfire.

## Required deliverable format (return as a downloadable `.md` file)

1. Executive summary: a direct verdict on the maintainer's top/bottom intuition (supported / contradicted / unresolved), and the single highest-impact change you recommend.
2. Q1 findings: placement/ordering evidence, the ranked drivers of compliance, and the alternatives table with trade-offs by capability tier. Cite sources with dates.
3. Q2 findings: the per-file audit, with quoted offending text, the reason each is a risk, and a concrete recommended rewrite or structural/tooling change for each.
4. A consolidated recommendation: the specific placement + structure for the two checklists, and the specific instruction/tooling changes to make the convention reliably followed by strong AND weak/fast agents.
5. Open questions and the experiment(s) that would resolve anything the evidence leaves unsettled.
6. A list of every source with URL and access date.

Return the complete report as one downloadable Markdown (`.md`) file.
