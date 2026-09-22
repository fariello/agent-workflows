- Id: 7qvj1c
- Status: open
- Set: selfmdialect
- Priority: medium
- Work-Kind: followup
- Summary: The resolver cannot match research metadata at all now that the bullet readers are region-bounded

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing IPD 76w6mq, and already designed: this is the gap plan xo3244 (Set selfmdialect, From-Backlog 05aqbj) exists to close, filed so the CONSEQUENCE of 76w6mq is carried explicitly rather than living only in that plan's prose. 76w6mq bounds the three bullet readers (_read_id/_read_status/_read_setid) to the metadata region. A research record's region is its YAML --- envelope, which contains no bullet-style '- Id:'/'- Status:'/'- Set:' at all, so all three readers now return None for every research record (measured: 110 of 117 tracked research files are ---fenced). That is the CORRECT outcome for 76w6mq (it stops a false claim without inventing a true one) but it means research id6/status/setid are reachable ONLY by filename substring. Before the fix they were reachable by accident on exactly the two documents that quoted a plan's bullet block, i.e. wrongly. Nothing regressed for any correct query; the pre-existing dialect gap is simply now the only path. No action needed if xo3244 lands.
