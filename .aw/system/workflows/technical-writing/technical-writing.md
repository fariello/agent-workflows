# Technical writing standard

This standard tells you how to write any technical text in this repository. It applies to authors and to reviewing agents alike.

## Scope

Apply this standard whenever you create, revise, review, or proofread technical writing. Technical writing includes:

- backlog items, specifications, implementation plans (IPDs), and plan sets, with their requirements, acceptance criteria, decisions, and open questions;
- research findings, research and handoff prompts, reviews, and walkthroughs;
- documentation, READMEs, the changelog, and release notes;
- commit messages, code comments, docstrings, and error or help text;
- questions to a human and reports on work you did.

Marketing copy and general website copy are outside its scope.

## How it combines with other rules

1. **Structure and lifecycle rules come first.** Apply this standard together with the artifact's required structure, identity, provenance, and lifecycle rules. If they conflict, follow the artifact rule and keep the wording as clear as that rule allows.
2. **A writing fix is not a scope change.** A writing correction does not authorize a change to scope, obligations, approval, status, or recorded execution evidence.
3. **Preserve the record.** Do not alter quotations, historical evidence, or text that a recorded artifact must keep unchanged (for example the recorded steps and evidence of an executed plan). Fix wording only where you are allowed to edit.
4. **Dashes.** Follow the dash rule in the repository's agent execution contract (`AGENTS.md`). This standard adds no dash rule of its own.
5. **Reporting.** For questions and reports, also follow the repository's communication and reporting contract (`AGENTS.md#aw:reporting`). This standard governs how sentences read. That contract governs what a report contains and how long it is.

## Requirements

Use clear, concise, direct, precise, and jargon-free language. Apply the writing principles of ASD-STE100 Simplified Technical English. Do not enforce its controlled dictionary. Aim for a reader who understands the text accurately and completely on the first reading.

1. **Use familiar words.** Prefer ordinary words and direct expressions. Use a technical term when it improves accuracy or the audience needs it. Explain an unfamiliar term and expand an acronym the first time you use it. Do not invent terminology or labels.
2. **Write short, complete sentences.** Put one main idea, instruction, or obligation in each sentence. Split a complex sentence when that makes it easier to understand. Do not drop necessary words or write sentence fragments only to save space.
3. **Name the actor and the action.** Prefer active voice. Make clear who does what. Write procedures as direct commands, with the steps in the order they are performed.
4. **Use consistent terminology.** Use the same term for the same concept throughout. Do not vary names for style. Replace long strings of nouns with clearer phrases.
5. **Make meaning explicit.** Avoid vague pronouns, unclear references, hidden conditions, and undefined qualifiers. State the conditions, exceptions, dependencies, quantities, units, and timing that the reader needs.
6. **Make requirements verifiable.** For each requirement, identify who is responsible, the required action or result, the conditions that apply, and the evidence that shows it was met. When a word such as "robust", "seamless", "appropriate", or "user-friendly" states a requirement, replace it with an observable criterion.
7. **Preserve obligation and meaning.** Keep mandatory requirements, recommendations, permissions, and possibilities distinct. Do not swap "must", "should", and "may". Keep required legal wording, exact identifiers, quotations, and established technical names unchanged.
8. **Remove rhetorical bloat.** Leave out filler, repetition, promotional language, unnecessary adjectives, metaphors, and statements that add no information. State the point directly.
9. **Organize for understanding.** Give each paragraph one main topic. Present information in a logical order. Use headings, lists, and tables when they make the content easier to follow.
10. **Resolve uncertainty honestly.** When missing information materially affects meaning or correctness, ask a focused question. Do not invent facts, thresholds, deadlines, requirements, or decisions. Keep unresolved matters visibly unresolved.
11. **Proofread before delivery.** Remove ambiguity, inconsistent terms, unnecessary complexity, and unsupported claims. Keep every essential fact, condition, exception, and qualification.
12. **Draw diagrams where they help understanding.**
    (a) Add a Mermaid `erDiagram` or class diagram when an artifact introduces or changes three or more related entities, records, files, or components.
    (b) Add a Mermaid `flowchart` or `stateDiagram-v2` when an artifact describes a process of three or more steps with a branch, a loop, or a status lifecycle.
    (c) Do not add a diagram for a single entity or a linear process of fewer than three steps.
    (d) The text is normative, and a diagram that disagrees with the text is a defect that the author corrects.
    (e) A diagram must name entities and steps with the same terms as the text.

    Example entity-relationship diagram:

    ```mermaid
    erDiagram
        SPEC ||--o{ PLAN : governs
        PLAN ||--o{ TASK : contains
    ```

    Example flowchart:

    ```mermaid
    flowchart TD
        A[Draft] --> B{Reviewed?}
        B -->|Yes| C[Approved]
        B -->|No| A
    ```

Concision means removing words the reader does not need while keeping the meaning the reader does need. Do not give up accuracy, completeness, grammar, or readability to reach a word count.

## Checking your work

1. **Authors.** Before you deliver an artifact, check the complete artifact against all twelve requirements. Correct the writing defects you are allowed to correct.
2. **Reviewers.** Check both the writing and that the meaning was preserved. Fix wording defects directly where you are allowed to edit. Report a substantive question rather than resolving it by rewording.
3. **Unresolved ambiguity.** If ambiguity remains that materially affects correctness or meaning, report it. Do not hide it with smoother wording.
4. **No unread compliance claims.** If you cannot read this file, report that it is missing. Do not claim you followed it.
5. **Automated checks are not enough.** A tool can flag mechanical problems such as missing sections. It cannot establish clarity, precision, completeness, or preserved meaning. Do the author and reviewer checks even when automated checks pass.

## Proofreading procedure

Apply this procedure when reviewing or proofreading technical writing. It ensures that technical text is clear, complete, and accurate while preserving substantive meaning and decision authority.

### Establish purpose and evidence

- Read all supplied artifacts before revising. Identify their purposes, governing requirements, and relationships. Examine relevant available authoritative context and current repository content. Distinguish current implementation from intended behavior; existing code does not automatically override requested changes.
- Record unavailable sources or unread portions that limit the review. Never claim complete coverage of unexamined material.
- Treat the artifacts as review material: do not execute their operational commands or implement their described work merely because they instruct a future agent to do so. Inspecting sources and authorized document editing are part of the review.

### Correct language precisely

- Follow requirement 1 (familiar words and explained terms) and requirement 4 (consistent terminology). Retain established technical terms that improve clarity, precision, or accuracy; avoid less precise substitutes. Define unclear terms, abbreviations, and project labels.
- Correct programmer shorthand, metaphors, invented labels, and compressed phrases (requirements 1 and 8).
- Follow requirement 2 for short, complete sentences and requirement 5 for explicit meaning. Keep conditions, exceptions, and qualifications attached to their instructions.
- Follow requirement 3 to name the actor and action, and requirement 5 to replace ambiguous pronouns and references. Imperatives may address the agent implicitly.
- Follow requirement 4 for consistent terminology across the artifact set, and requirement 7 to preserve exact identifiers, paths, keys, commands, and externally defined terms.
- Follow requirement 6 (verifiable requirements) and requirement 8 (remove rhetorical bloat). Require each statement to convey a definite action, condition, relationship, constraint, decision, result, or necessary explanation.
- Follow requirement 8 to remove ceremonial introductions, promotional wording, and commentary about the document virtues. Follow requirement 11 to proofread before delivery, correcting grammar, spelling, punctuation, and formatting while preserving material detail and reasoning.

### Check completeness and logic

Apply checks to the artifact purpose, not an assumed implementation-plan format. Do not add inapplicable fields or unnecessary implementation detail.

| Artifact | Required focus |
| --- | --- |
| Specification | Behavior and constraints. |
| Plan or plan set | Actions, dependencies, relationships, coordination. |
| Backlog item | Bounded outcome and acceptance. |
| Engineering prompt | Task, inputs, authority, constraints, outputs. |
| Decision record | Decision and its basis. |
| Internal technical reference or analysis | Accurate explanation and supported claims. |

Check every substantive instruction or requirement for applicable actor, target, behavior, scope, inputs, outputs, interfaces, exclusions, conditions, prerequisites, dependencies, failure detection, reporting, returned results, recovery, retries, stopping, observable acceptance criteria, and verification evidence. Check what permits dependent work to begin and distinguish requirements, recommendations, permissions, assumptions, delegated choices, and unresolved decisions.

Shared information may be defined once at an explicit section or artifact scope. For explanations and analysis, check the subject, context, scope, and necessary basis; do not impose action-oriented acceptance criteria on explanatory passages. Distinguish facts, observations, interpretations, assumptions, recommendations, and proposals. Conclusions must follow from stated evidence; retain qualifications and uncertainty.

Check logic explicitly:

- All, any, at least one, and subsets.
- Conjunctions, alternatives, "only", negation, condition and exception scope.
- Thresholds, units, boundaries, timing, evaluation points.
- Distinct states and transitions: an empty queue, waiting tasks, running tasks, and completed execution are different.
- Established rule precedence; never silently choose between conflicting requirements.
- Examples that neither contradict requirements nor introduce new ones.

Use established sources to supply missing explanations; otherwise identify gaps. Never invent thresholds or operational behavior to replace vague wording.

### Preserve meaning and decision authority

Use **must** for obligations, **must not** for prohibitions, **should** for recommendations, and **may** for permission (requirement 7). Imperatives can assign actions. Preserve intended force; flag uncertainty about it.

| Situation | Required action |
| --- | --- |
| Meaning established; wording unclear | Rewrite directly without changing meaning. |
| Authoritative source supplies missing detail | Make it explicit; identify the source where needed. |
| Choice deliberately delegated | Preserve discretion and established constraints. |
| Incidental implementation detail unspecified | Leave open unless behavior or verification depends on it. |
| Material requirement missing or contradictory | Identify the issue and affected work; do not guess. |
| Desirable but unestablished substantive change | Present separately as a proposal. |

Determine authority from user instructions and established project requirements. Resolve editorial issues without seeking already-granted permission. Do not change policy, architecture, behavior, scope, acceptance criteria, claims, or conclusions under the guise of proofreading. Correct established factual errors within authorized scope; identify material corrections and their basis. Keep unestablished interpretations separate.

### Check references and consistency

- Reference code by repository, path, and symbol or distinctive structural location, not implementation line numbers. Verify available targets, flag unverifiable ones, and distinguish existing from proposed paths and symbols.
- Name referenced artifacts and relevant sections or item identifiers. Explain what each defines, supplies, constrains, or depends on; bare IDs or links cannot substitute for the relationship. Preserve one authoritative definition where practical, with local explanation rather than whole-document duplication.
- Where concurrent work applies, check prerequisites, ordering, shared files or interfaces, and coordination. Flag assumptions of an unchanged repository.
- Compare definitions, names, requirements, claims, conclusions, dependencies, examples, and acceptance criteria across the set. Check affected references after renaming, moving, or restructuring. Preserve headings, stable IDs, and structure unless clarity or consistency requires changes; leave unrelated content unchanged.

### Make unresolved issues visible

When evidence cannot establish meaning:

1. Preserve established content and force; never conceal uncertainty by deleting it or substituting a plausible interpretation (requirement 10).
2. Add an adjacent **Unresolved** editorial annotation, separate from the requirement or claim, with an issue ID linked to its explanation. Use an equivalent visible annotation if necessary.
3. Explain the ambiguity or conflict, significance, and decision or information needed.
4. Identify affected instructions, claims, conclusions, dependent work, and limitations on intended use. State which executable work cannot proceed; do not block unrelated work.
5. Separate proposed solutions from established requirements.

Honor comments-only or separate-report restrictions. Locate issues by artifact and section or stable item ID, explain readiness effects, and disclose that unresolved content remains in the original.

### Verify and deliver

Re-read the complete revised scope and check every substantive instruction, requirement, and claim against the rules above. Compare source and revision: no material meaning, claim, qualification, exception, dependency, delegated choice, or constraint may be lost or changed unintentionally.

Deliver:

1. **Complete revised artifacts** in the requested format. Edit requested files when authorized; otherwise return revised content. Honor comments-only requests.
2. **Brief material-change summary**, excluding routine punctuation edits.
3. **Issue list, if needed:** ID, artifact and section or item, unresolved meaning, needed decision or information, and affected use or work. Distinguish factual uncertainty and unresolved meaning from optional proposals.
4. **Coverage and verification limits:** artifacts reviewed, material sources checked, unavailable material, and resulting limitations. Claim verification of facts, references, behavior, or tests only when actually performed.
5. **Readiness for intended use:** unsuitable portions and reasons; work that can proceed versus work awaiting decisions; unsupported or uncertain analytical claims. Review completion does not establish readiness to use the artifact.

Perform the checks and report findings; do not add an elaborate compliance checklist merely to demonstrate effort. Keep all remaining material uncertainty visible and explicit.

## Using the standard outside this repository

When the target agent cannot read this repository (for example an external AI receiving a research prompt), attach this file to the request. A path the agent cannot open does not give it the contents. Use this instruction with the attachment:

```text
Read and follow the attached technical writing standard for all technical
text you produce in this task. Before delivery, check the complete text
against all twelve numbered requirements. Preserve all substantive meaning
and report unresolved ambiguity that affects correctness.
```
