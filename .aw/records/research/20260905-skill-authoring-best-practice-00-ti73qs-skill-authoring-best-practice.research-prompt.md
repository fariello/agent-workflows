---
id: ti73qs
created: 20260905
set: skill-authoring-best-practice
order: 00
topic: [skills, authoring, prompt-design]
model:
kind: research-prompt
status: todo
outcome: none-yet
summary: How to author and generate SKILL.md routers that agents reliably select and execute, for a pointer-based toolkit with 45 workflows
consumed-by: []
priority: medium
---
# Research request: how should SKILL.md routers be authored so agents select and execute them reliably?

You are researching PROMPT AND DOCUMENT DESIGN for agent "skill" files: what actually makes an
agent pick the right skill and then carry out its instructions correctly. Prefer measured
evidence, vendor guidance, and real examples over intuition. Say plainly where no evidence exists.

RETURN YOUR ANSWER AS A DOWNLOADABLE MARKDOWN (`.md`) FILE. Do not answer only in chat.

## The codebase under discussion

The toolkit asking this question is public and you may read it:

    https://github.com/fariello/agent-workflows

It GENERATES its skill files rather than hand-writing them, which shapes the whole question: any
recommendation must be expressible as a deterministic template driven by workflow metadata, not as
advice to an author. The generator is `agent_workflows/host_adapters.py`
(`build_skill_package`, `_render_skill_main_file`, `_render_trigger_description`,
`validate_skill_package`). Read a few generated `SKILL.md` files in a repo that installed it, and
critique what you find; the author's own assessment is that they look "very far from optimized for
safe, effective, reliable execution".

Three constraints are deliberate and NOT up for negotiation, so work within them:

1. ONE SOURCE OF TRUTH. Authoritative instructions live in a canonical workflow body. The skill
   must POINT at that body (`read and execute <path>`), never duplicate it. A validator actively
   fails a package that inlines canonical content. Any recommendation that amounts to "copy the
   instructions into the skill" is rejected; recommend how to make the POINTER work instead.
2. GENERATED, NOT AUTHORED. There are roughly 45 workflows, so the answer must be a template plus
   metadata rules, deterministic and diffable.
3. A BYTE BUDGET exists for the router, because a skill that eats the context window defeats
   itself. Recommend a budget if you have evidence for one.

## Question 1: what makes an agent select the RIGHT skill?

- What does each major host match against: the frontmatter `description`, the file name, the whole
  body, an embedding, an LLM decision? Cite per host and per version.
- Is there evidence about description wording that fires reliably: length, imperative versus
  descriptive voice, naming the triggering user phrasing, listing negative cases ("do NOT use
  when ...")? Prefer vendor guidance or measured results; label folklore as folklore.
- What causes MIS-selection, where a host picks the wrong skill or none? This matters more than
  the happy path: with 45 similarly-shaped workflows, confusability is the likeliest failure.
- Does the number of installed skills degrade selection accuracy? Is there a practical ceiling?

## Question 2: what makes the agent EXECUTE the skill correctly once selected?

- Structure: what ordering of sections, headings, and imperative steps produces the most reliable
  compliance? Is there evidence that instructions early in a file are followed more reliably than
  the same instructions late?
- How should a skill express hard prohibitions so they are actually honored? Is there evidence
  about capitalization, repetition, or explicit "never do X" phrasing, or is that folklore?
- THE POINTER PROBLEM specifically: when a router says "read and execute <path>", how often does
  an agent actually open the file versus improvising from the router? What phrasing or structure
  makes the redirect more reliable? Name the observed failure modes.
- Should a router restate the skill's PRECONDITIONS and SAFETY RULES even though the canonical body
  also carries them, given the pointer might not be followed? That is a genuine tension between
  "one source of truth" and "the agent may never open the target"; give a reasoned answer.

## Question 3: frontmatter and metadata

- What keys does each host require, allow, and ignore? Quote the schemas.
- Are unknown keys tolerated or fatal? The toolkit adds a non-standard `semantic-digest` key, so
  say whether that is safe on each host.
- Is there a portable subset that works across hosts without per-host variants?

## Question 4: concrete critique and a recommended template

- Show 3 to 5 real SKILL.md files you judge WELL-DESIGNED, from vendors or reputable projects,
  and explain specifically what each does well. Quote them.
- Show at least one you judge poorly designed, and say why. A negative example is instructive.
- Then propose a CONCRETE TEMPLATE for this toolkit's generated router: exact section order,
  what belongs in frontmatter, what the invocation line should say, what to include about
  preconditions, and a recommended byte budget with your reason for the number.
- Note explicitly which of your recommendations are evidence-backed and which are your judgement.

## How to answer

- Separate VERIFIED (primary source, cited, with version and date) from REPORTED (community or
  secondary) from JUDGEMENT (your reasoning). Do not blend them.
- Quote schemas and examples exactly; paraphrase loses what matters.
- Where the honest answer is "nobody has measured this", say so. An unmeasured area named clearly
  is more useful than a confident guess, because the toolkit can then measure it.
- Keep every recommendation compatible with the three constraints above, and say so when a
  common piece of advice conflicts with them.
