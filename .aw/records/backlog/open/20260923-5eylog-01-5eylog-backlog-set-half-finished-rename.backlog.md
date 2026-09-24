- Id: 5eylog
- Status: open
- Blocks-Release: next
- Set: 5eylog
- Priority: medium
- Work-Kind: bug
- Summary: aw backlog set done commits the new path but leaves the old path deletion merely staged

## Workflow history
- 2026-09-23 created (aw backlog): MEASURED on main 2026-09-23. 'aw backlog set done 87aj3i --yes' moved the item from open/ to done/ and committed, reporting 'Committed 1 path(s): 25099e64 .aw/records/backlog/done/<item>'. But 25099e64 contains ONLY the insertion of the new done/ copy (git show --stat: '1 file changed, 11 insertions(+)'); the deletion of the open/ path was left STAGED in the index, so immediately after the setter reported success 'git status --short' read 'D  .aw/records/backlog/open/<item>' and BOTH paths existed in the committed tree. Two consequences. FIRST, the item is momentarily counted twice by anything that scans the trees, and its status is ambiguous (open/ and done/ disagree). SECOND, and worse in a SHARED CHECKOUT, the setter leaves a staged deletion behind for whoever commits next to sweep up, which is exactly the index pollution the AGENTS.md commit protocol warns about; it was only caught here because the protocol requires re-verifying the staged set. Closed by hand in 79fc0626. EXPECTED: a rename is one atomic commit containing both the addition and the deletion, and the setter leaves a CLEAN index. Where: the 'aw backlog set' status-mutation path that performs the tree move (the same code that prints 'Committed N path(s)').
