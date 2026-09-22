- Id: nvymif
- Status: open
- Set: nvymif
- Priority: medium
- Work-Kind: chore
- Summary: The R5.5 teardown gate refuses every interrupted lane, because an absent collection receipt reads as uncollected even for a lane that submitted nothing

## Workflow history
- 2026-09-22 created (aw backlog): The R5.5 teardown gate refuses every interrupted lane, because an absent collection receipt reads as uncollected even for a lane that submitted nothing

MEASURED 2026-09-22 while executing plan 65cuw0 (laneorph Order 01), on a real git lane with a real run directory and a real queue item:

    PROVABLY EMPTY LANE, inventory with a REAL run_dir and item:
      readable            : True
      dirty_tracked       : ()
      unknown_untracked   : ()
      unknown_ignored     : ()
      uncollected_submission: True
      submission_detail   : no attempt-keyed collection receipt at 01-aaaaaa-attempt-1.json; absence means NOT collected (spec R2.5)
      classified          : False
      reason_codes        : ('uncollected-submission',)

WHERE: lane_containment.submission_retention (:3100-3116) plus LaneInventory.classified (:2919).

WHY IT MATTERS: an INTERRUPTED lane never has a completed collection receipt, by definition, so
lane_containment.teardown_lane_if_classified refuses EVERY lane on the interrupt path regardless of how
clean it is. That made it impossible for plan 65cuw0 to route the pre-existing provably-empty reclaim
through the one teardown gate as spec 7ckptx R6.1 would prefer: doing so turned action='reclaimed' into
'preserved' for the empty case and for the review sweep lane, and red-ed
tests/test_lane_allocation_idempotent.py and tests/test_review_lane_isolation.py. The plan therefore
scoped the gate to the NEW merged case only (decision 08-65cuw0-D1), leaving two teardown paths on the
interrupt route where R6.1 would prefer one.

THE DISTINCTION THAT IS MISSING: spec R2.5's 'absence means NOT collected' is correct for a lane that
WROTE a submission, and is the wrong answer for a lane that PROVABLY wrote none (zero commits, empty
porcelain, no lane-submissions tree at all). Today the two are indistinguishable.

NOT FILED AS A BUG: no user-visible wrong answer and no user-perceptible latency; the consequence is a
design compromise inside one plan, not an incorrect result. Resolving it is a spec R2.5 question (what
does an absent receipt mean for a lane that submitted nothing?) and needs its own plan.

EVIDENCE: decision record 08-65cuw0-D1 in the run's decisions-and-questions register; plan 65cuw0's
V-05 observed evidence.
