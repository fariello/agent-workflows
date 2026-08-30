# Workflow: research-prompt (research handoff prompt generator)

Turn a research topic into a house-conformant, upload-ready research handoff PROMPT for another AI (e.g. an external LLM with web search or specialized knowledge) and stage it into `.aw/records/prompts/pending/`.

This workflow is a PRODUCER: it drafts a prompt for another AI to execute. It does not execute the research itself, and it is distinct from `aw research new` (which creates a research document under `.aw/records/research/`).

## What this workflow does and does not do

- It PRODUCES one upload-ready research handoff prompt (`.prompt.md`), minted by `aw prompts new` into `.aw/records/prompts/pending/`. The verb derives the filename (`YYYYMMDD-HHMM-NN-<slug>.prompt.md`); never hand-name it.
- It is read-only with respect to product code and durable reference records.
- It writes a `Status: pending` draft and does NOT `git add`, stage, commit, or push the prompt file.
- It does NOT execute the research inquiry or write research result documents (the prompt instructs the target AI to produce the research report).

## Division of labor and naming distinction

- **`/aw research` (this producer workflow):** DRAFTS a prompt for another AI to conduct research. Staged under `.aw/records/prompts/pending/`.
- **`aw research new` / `aw research` (CLI doc verb):** Creates or manages durable research DOCUMENTS filed under `.aw/records/research/` once research results are returned.

## Memory kernel

Re-read before drafting and before the exit gate:

1. **AGENTS.md Prompt-Purity Contract (MANDATORY):**
   - **Only the prompt:** The emitted file contains ONLY the prompt addressed to the target AI. Put NO instructions for the user inside it (no "copy this", no "paste below the line", no user-facing instructions inside).
   - **Self-contained:** The prompt is completely self-contained, so the user can select-all-and-copy it, or upload it and say "read and execute the attached prompt", with nothing to edit or supply.
   - **Downloadable `.md`:** The prompt explicitly instructs the target AI to return its entire answer as a DOWNLOADABLE markdown (`.md`) file so the result can be saved directly.
2. **Leading HTML Comment Pipeline Metadata:** Pipeline metadata is a single leading HTML comment line (`<!-- aw-prompt: ... -->`), written by `aw prompts new`, not by hand. This comment is invisible when pasted into an LLM chat and preserves staging metadata without violating prompt purity.
3. **Target Tracked Pending Lane:** `aw prompts new` writes to `.aw/records/prompts/pending/` with `Status: pending`. Never auto-stage or commit.
4. **Leak Sanitizer Awareness:** Run `aw check-local-leaks` on the finished file before concluding.

## Inputs

`$ARGUMENTS`, if present, provides the research topic and initial scope. If no arguments are provided, ask the user for the research topic.

## Step 0: Discover context and conventions

1. Survey the repository for relevant background:
   - Check `AGENTS.md` for prompt authoring rules.
   - Check `.aw/records/prompts/README.md` for prompt staging conventions. Do NOT derive the filename yourself; `aw prompts new` owns it.
   - Check whether related research records exist under `.aw/records/research/` to avoid duplicate inquiries.

## Step 1: Gather topic, scope, and constraints

Clarify the inquiry with the user if needed:
- **Topic:** What specific technical, architectural, tooling, or domain question needs investigation?
- **Target AI / Host:** What model or environment will run this prompt (e.g. Gemini, Claude, GPT, Perplexity, external research agent with web search)?
- **Scope & Depth:** What specific hosts, libraries, versions, or benchmarks must be covered? What is out of scope?
- **Constraints & Prior Knowledge:** Known technical constraints, decisions already made, or previous approaches tried.

## Step 2: Formulate the research inquiry

Deconstruct the topic into a structured inquiry for the target AI:
1. **Persona & Core Objective:** Define the specific expert persona (e.g. senior developer-tooling researcher, distributed systems engineer) and primary goal.
2. **Background & Architecture Context:** Concrete background on what the project is building and why this research is needed.
3. **Specific Questions to Answer:** Structured, numbered questions with concrete detail (per-host or per-technology breakdowns, mechanisms, edge cases, trade-offs).
4. **Synthesis & Comparative Analysis:** Requirements for comparison tables, trade-off matrices, migration/back-compat recommendations, or concrete adoption decisions.
5. **Rigorous Research Rules:**
   - Mandate citations with official URLs and access dates for all nontrivial claims.
   - Distinguish verified facts from inferences.
   - Prioritize current documentation and note version numbers.
   - Be concrete: provide literal syntax, schemas, or file paths rather than generalities.
6. **Deliverable Specification:** Instruct the target AI to return its complete output as a single DOWNLOADABLE markdown (`.md`) file, naming the expected filename and required section layout.

## Step 3: Draft the prompt body

Draft the PROMPT BODY only. The leading `<!-- aw-prompt: ... -->` metadata comment is written for you by `aw prompts new` in Step 4, so do not compose or copy one by hand:

```markdown
You are a <expert persona>. <Clear statement of the primary research objective>.

# Background (what I am building)
<Self-contained background explanation of the system and context>

# The core questions to answer
<Numbered, rigorous questions covering mechanisms, trade-offs, edge cases>

# Synthesis and recommendations
<Comparison requirements, decision criteria, trade-off matrix>

# Rules for your report
- Prioritize official documentation; cite every nontrivial claim with a URL and date.
- Distinguish documented facts from inference. If something is undocumented or unknown, state that plainly.
- Be concrete: give exact file paths, schemas, commands, and code snippets.
- Do not pad with generic background; focus on the specific questions.

# Deliverable
Return your entire answer as a single DOWNLOADABLE markdown file named `<topic>-research-report.md` (provide it as a downloadable `.md` file, not only inline), structured as:
1. Executive summary and recommended design/decision.
2. Detailed findings per area/technology.
3. Comparison and trade-off table.
4. Concrete risks, unknowns, and edge cases.
5. References list with URLs and access dates.
```

## Step 4: Mint the file with `aw prompts new`, then write the body into it

1. MINT the staged file with the verb. It derives the filename and writes the metadata comment; you supply the metadata fields:

   ```bash
   aw prompts new --kind research \
     --slug <topic-slug> \
     --author '<agent> (<model>)' \
     --targets '<target-ai-models>' \
     --concerns '<short-summary>' \
     --apply
   ```

   Omit `--apply` first if you want to preview the path it will use. The verb prints the path it wrote; use that path for the remaining steps. Do NOT compute a timestamp or sequence number, and do NOT hand-write the `<!-- aw-prompt: ... -->` comment: both are the verb's job, and hand-writing them is what drifted the existing corpus.

2. APPEND your Step 3 prompt body to that file, after the metadata comment the verb wrote. Add nothing else: no user-facing instructions, no delimiters, no template scaffolding.
3. Run `aw check-local-leaks <the-file>` (or `python3 -m agent_workflows check-local-leaks <the-file> --agent`) to ensure no machine or maintainer identifying leaks were introduced.
4. Do NOT stage or commit the file.

## Exit gate (satisfy every item before reporting done)

- [ ] File was MINTED by `aw prompts new` (not hand-named, not hand-written metadata) and landed under `.aw/records/prompts/pending/`.
- [ ] Emitted prompt contains ONLY the prompt addressed to the target AI (no user-facing instructions inside it).
- [ ] Emitted prompt is completely self-contained.
- [ ] Emitted prompt instructs the target AI to return its output as a DOWNLOADABLE markdown (`.md`) file.
- [ ] File begins with the single-line `<!-- aw-prompt: Kind: research | Status: pending ... -->` metadata comment the verb emitted, with nothing before it.
- [ ] `aw check-local-leaks` run on the finished file with zero violations.
- [ ] No product code modified; prompt file is NOT auto-staged or committed.
- [ ] User informed of the staged prompt path and how to upload/paste it to the target AI.

## Reminders

- Read-only with respect to product code and durable reference records.
- `/aw research` produces a prompt for another AI; `aw research new` creates a research document once results return.
- `aw prompts new` mints the staged file; you never hand-name a prompt or hand-write its metadata comment.
- Never auto-commit the generated prompt.
