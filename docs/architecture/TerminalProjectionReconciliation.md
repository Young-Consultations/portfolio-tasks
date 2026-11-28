# A2.4 terminal source lifecycle repair (#173)

Candidate only; no historical issue mutation or replay authorized. The exact terminal comment is the outcome. Clear obsolete queued/approved projections for the same current material identity; never mark done or close an issue. No new label vocabulary or settings. Closed issues and unknown/human lifecycle labels block mutations. Late routing acknowledgement uses the per-source result and missing-result concurrency key; GitHub concurrency can cancel a pending job, and the API lacks atomic conditional label writes. Re-read and verify; incomplete projection requires operator reconciliation, not execution replay.

The fresh authenticated receiver dispatch must have a matching trusted receipt. Forwarded is written after dispatch, so validate it if present, require it for historical planning. Support exact v3.0.3, v4.0.0 and v5.0.0 trust policies and one durable admission per source issue; other identities/releases or newer material stop. This intentionally denies ambiguous multi-delivery history. V5 missing-result recovery additionally requires the exact consulting adapter and no trusted terminal receipt or forwarding evidence. The repair does not replace the pre-execution replay gate (#111).

## Historical #167 read-only plan

After review, using the reviewed source checkout and an existing read-only credential, the operator can obtain an evidence-bound plan:

    ISSUE_NUMBER=167 DELIVERY_ID=task-f43f483eeeb455cfeaea98f94a4dbddd \
      PROJECTION_MODE=plan python -m portfolio_tasks.terminal_projection

If exact identity and evidence pass: failed, remove status:queued, no new labels/comment, mutation_authorized=false. Body hash and current labels are emitted; mismatch blocks. No manual mutation workflow included. The original editorial task is unfulfilled. Separate approval of the exact plan and fresh readback are required before changing #167. Never reapprove or replay. Tests use synthetic API state and trap subprocess/socket calls. Normal CI has no source mutation.

A matching forwarding marker arriving between source reads is allowed after complete revalidation. A receipt arriving before queued mutation blocks the write; one arriving during the label update causes visible incomplete-projection failure pending the terminal projector. Conflicting/forged evidence results in a failed workflow with SOURCE_PROJECTION_BLOCKED, without writing a quarantine label based on untrusted or mismatched source state. Operator review of that failure is required; this deliberately changes the old quarantine-label side effect. No automatic repair or dispatch on failure.

## V5.10 source adoption

Normal V5 result and queue projection replace the maintenance-only exception.
For V5, recompute the visible effect from the immutable receiver at
`3cce887fc393fa80ed8f79308ca9b9c7241ce622`. Managed drafts use one effect class, but
an exact trusted receipt digest remains necessary for each projected result.
The historical maintenance issue #176 and reservation marker are retired;
no new admission, projection or recovery of the smoke is allowed.
The historical plan remains read-only. No live verification is authorized.
