- Id: yvcdw1
- Status: open
- Blocks-Release: next
- Set: yvcdw1
- Priority: low
- Work-Kind: bug
- Summary: aw find prompts shows no status because the front-matter reader cannot see a directory-carried lane

## Workflow history
- 2026-09-20 created (aw backlog): aw find prompts shows no status because the front-matter reader cannot see a directory-carried lane

MEASURED 2026-09-20 while executing plan `9zvl2w` (noticed verifying the converted `aw find` lifecycle column).

`aw find prompts` renders `-` (no status) for 16 of 17 prompts:

    $ aw find prompts --no-color | awk '{print $1}' | sort | uniq -c
         16 -
          1 superseded

CAUSE: `cli._find_type_records`'s generic branch reads the status with `selectors._read_status`, i.e. from a `- Status:` FRONT-MATTER line. But prompt status is carried by DIRECTORY, not by a status enum: `prompts.py` defines only `DEFAULT_STATUS` and `PROMPT_KINDS`, and spec `uonrjg` Section 6.5 states the same thing ('Native status or lane', mapping the five LANE names `pending`/`executed`/`reusable`/`superseded`/`not-executed`). The one row that DOES show a status has a literal `- Status:` line; the other 16 sit in lane directories that the reader never consults.

USER-PERCEPTIBLE: `aw find prompts` cannot answer 'which prompts are still pending?', and the column is not merely uncolored but EMPTY, so the information is absent rather than plain.

NOT A REGRESSION FROM `9zvl2w`: that plan converted how the value is STYLED, and this is about the value not being READ. Before the conversion these rows printed an unstyled `-`; after it they print `·` `-`, which is Section 6.7's honest 'no lifecycle here' rendering of the same missing datum.

FIX SHAPE: fall back to the lane directory for `prompts` (`ipd_lint._dir_of` already anchors the five lane names, and `lifecycle_style.FAMILY_PROMPTS` already maps them, so the mapping exists and only the READ is missing). Deliberately NOT done inside `9zvl2w`: changing which value `aw find` reports is a data-source change, outside a presentation plan's scope, and it needs its own test.
