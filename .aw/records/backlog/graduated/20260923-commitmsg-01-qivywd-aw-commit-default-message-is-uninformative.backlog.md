- Id: qivywd
- Status: graduated
- Graduated-To: commitmsg
- Set: commitmsg
- Priority: low
- Work-Kind: chore
- Summary: aw commit with a plan and no -m writes 'work: <full plan path>' as the whole commit message, which is uninformative and repo-style-nonconforming

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into plan isgno7 (Set commitmsg), re-verified live at HEAD.
- 2026-09-23 created (aw backlog): MEASURED while executing plan n9na1c on 2026-09-23. I ran 'aw commit <plan> -- <paths>' without -m, and the resulting commit message was exactly one line:

    work: .aw/records/plans/pending/20260922-gateinert-01-n9na1c-make-a-usable-not-mine-gate-answer-actually-release-the-inte.ipd.md

WHERE IT COMES FROM: work_cmd, at the commit call, 'message = getattr(args, "message", None) or f"work: {plan_rel}"'.

WHY IT IS WORTH FIXING, stated narrowly so it is not over-claimed. It is NOT a correctness bug: the commit is correct, the paths are correct, and -m is available and documented. The problem is that this repository's own history is uniformly Conventional-Commits-shaped ('feat(runner): ...', 'plan(<id6>): ...', 'lifecycle(<id6>): ...', 'integrate(aw oc run): ...'), and the execution contract tells agents to 'write a concise commit message that matches the repo style'. So the tool's DEFAULT produces the one shape the repo does not use, and it does it at the moment an agent is most likely to accept a default. The message also carries no id6 in a greppable position, no type, and no scope, while spending its entire subject line on a ~110-character path that is already recoverable from the diff.

I noticed it because I took the default, saw the result, and had to 'git commit --amend' to write a real message - which is a wasted round trip and, worse, an amend an agent might skip.

A CHEAP FIX EXISTS: derive the default from what the tool already has in hand, e.g. 'work(<id6>): <plan title or slug>', which is greppable by id6, matches the repo's type(scope) grammar, and stays honest about being a generic work commit. The plan's '- Id:' and its H1 title are both already parsed by the lint the same command runs. Alternatively refuse to guess and REQUIRE -m when a plan governs the commit, which is defensible but costs a round trip on every call.

Filed as a low-priority chore: nobody is blocked, no output is wrong, and the remedy is one format string plus a test.
