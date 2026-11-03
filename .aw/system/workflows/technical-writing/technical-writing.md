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

Concision means removing words the reader does not need while keeping the meaning the reader does need. Do not give up accuracy, completeness, grammar, or readability to reach a word count.

## Checking your work

1. **Authors.** Before you deliver an artifact, check the complete artifact against all eleven requirements. Correct the writing defects you are allowed to correct.
2. **Reviewers.** Check both the writing and that the meaning was preserved. Fix wording defects directly where you are allowed to edit. Report a substantive question rather than resolving it by rewording.
3. **Unresolved ambiguity.** If ambiguity remains that materially affects correctness or meaning, report it. Do not hide it with smoother wording.
4. **No unread compliance claims.** If you cannot read this file, report that it is missing. Do not claim you followed it.
5. **Automated checks are not enough.** A tool can flag mechanical problems such as missing sections. It cannot establish clarity, precision, completeness, or preserved meaning. Do the author and reviewer checks even when automated checks pass.

## Using the standard outside this repository

When the target agent cannot read this repository (for example an external AI receiving a research prompt), attach this file to the request. A path the agent cannot open does not give it the contents. Use this instruction with the attachment:

```text
Read and follow the attached technical writing standard for all technical
text you produce in this task. Before delivery, check the complete text
against all eleven numbered requirements. Preserve all substantive meaning
and report unresolved ambiguity that affects correctness.
```
