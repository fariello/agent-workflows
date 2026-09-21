- Id: f7a2kc
- Status: open
- Blocks-Release: next
- Set: f7a2kc
- Priority: medium
- Work-Kind: bug
- Summary: aw research set-assign and mv rename the file but never update its set/order/model frontmatter, so the verb emits the name-frontmatter-mismatch it just created

## Workflow history
- 2026-09-20 created (aw backlog): Reproduced at HEAD 9d02743b through the real CLI in a throwaway repo: set-assign left set: oldsetid / order: 03 after renaming to newsetid-01, and mv --model left model: empty. Cause: research_refs._apply_renames never opens the moved file; both planners return rename plans only. The generic backend already does this correctly in one transaction (artifact_rename._update_frontmatter_metadata), so this is an asymmetry between the research backend and the generic one. Checked against 4y4xo5 (different defect, same function, no frontmatter mention) before filing.

REPRODUCED AT HEAD 9d02743b in a throwaway repo, using the real CLI rather than the library, so this is the user-facing behavior and not an internal-call artifact.

    $ aw research set-assign aaaaaa --set newsetid --order 1 --apply
    renamed .../20260901-oldsetid-03-aaaaaa-a-demo-doc.notes.md
         -> .../20260920-newsetid-01-aaaaaa-a-demo-doc.notes.md
    reference/202609/20260920-newsetid-01-aaaaaa-a-demo-doc.notes.md:
        name-frontmatter-mismatch: set oldsetid != name newsetid

The file's own frontmatter still reads `set: oldsetid` / `order: 03` after the move. The second verb has the same shape:

    $ aw research mv aaaaaa --model sonnet5high --apply
    renamed ... -> ...-a-demo-doc.sonnet5high.notes.md
    $ grep '^model:' <the file>
    model:

`--model sonnet5high` reached the FILENAME and left `model:` empty in the frontmatter.

WHAT MAKES THIS WORTH FILING RATHER THAN SHRUGGING AT: the verb emits the violation IT JUST CREATED, in its own output, and does not fix it. A repair verb corrupts what it repairs, and the corruption is exactly what `aw research index --check` fails on, so the next `--check` run blames whoever touched the tree next.

CAUSE, by symbol. `research_refs._apply_renames` (agent_workflows/research_refs.py:244) performs the git move, the citing-document rewrites and the index regeneration, and never opens the moved file. Both planners return rename plans ONLY: `plan_set_assign` (:159) and `plan_mv` (:192) compute a new NAME from the parsed old name plus the requested change, and no frontmatter edit exists anywhere on either path.

THE FIX SHAPE IS ALREADY IN-REPO, WHICH IS WHY THIS IS AN ASYMMETRY AND NOT A MISSING FEATURE. The generic backend solves it in one transaction: `artifact_rename.run_group_generic` calls `_update_frontmatter_metadata` on the destination (artifact_rename.py:588), backed by `_update_or_inject_set_metadata` (:340), which updates `set:`/`order:` in fenced YAML AND `- Set:`/`- Order:` in bullet frontmatter, injecting the keys when absent. Measured contrast on the same operation:

    $ aw group plans bbbbbb --set fourth --order 4 --rename --apply
    renamed ...-oldset-03-bbbbbb-... -> ...-fourth-04-bbbbbb-...
    $ grep '^- Set:\|^- Order:' <the plan>
    - Set: fourth
    - Order: 4

Name and frontmatter agree. The research tree has its own backend that skipped this step. Note the generic backend handles `set`/`order` but has no `model` key, so the model facet needs adding for the `mv --model` half; `research_contract` already owns model normalization (`normalize_model`, used at research_refs.py:213), so the value to write is already computed and simply discarded.

NOT A DUPLICATE OF 4y4xo5, checked before filing as the handoff asked. `4y4xo5` is a DIFFERENT defect in the same function: `--order` defaulting to 0 and silently renumbering a set from zero. It is about which ORDER VALUE the name gets; this is about the frontmatter not being written AT ALL, for `set`, `order` and `model` alike. `grep -c 'frontmatter' 4y4xo5` is 0. They do share a fix site, so whoever fixes either should read both: `4y4xo5`'s own recommended fix (resolve an absent `--order` per record from front matter then filename NN) requires READING the frontmatter this item says is stale, so fixing 4y4xo5 alone on a tree corrupted by this item would preserve a wrong Order with a clean conscience. Sequence this one first, or fix both together.

OBSERVED IN THE REAL TREE, not only in the reproduction: five research docs in the `hostskill` set were left mismatched by these verbs during the 2026-09-20 inbox drain and were REPAIRED BY HAND in commit 97155d38 (one still carried `set: host-skill-runtime-discovery-and-authoring` while its name said `hostskill`). That hand repair is why the tree currently looks clean; the verbs are unchanged.

USER-PERCEPTIBLE IMPACT, stated as the bug rule requires. A maintainer who regroups a research set with the documented verb gets records that fail the toolkit's own `--check`, with no warning that a hand repair is required. The failure surfaces later, detached from the verb that caused it, and the recorded `set:`/`order:` are wrong in the meantime, which is what `aw find --set` and the INDEX read.
