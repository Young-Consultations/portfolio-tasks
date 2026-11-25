# A2.4 terminal source lifecycle repair (#173)

Candidate only; no historical issue mutation or replay authorized. The exact terminal comment is the outcome. Clear obsolete queued/approved projections for the same current material identity; never mark done or close an issue. No new label vocabulary or settings. Closed issues and unknown/human lifecycle labels block mutations. Late routing acknowledgement uses the per-source result and missing-result concurrency key; GitHub concurrency can cancel a pending job, and the API lacks atomic conditional label writes. Re-read and verify; incomplete projection requires operator reconciliation, not execution replay.

The fresh authenticated receiver dispatch must have a matching trusted receipt. Forwarded is written after dispatch, so validate it if present, require it for historical planning. Support only exact v3.0.3 and v4.0.0 trust policies and one durable admission per source issue; other identities/releases or newer material stop. This intentionally denies ambiguous multi-delivery history. Existing missing-result recovery is unchanged. The repair does not replace the pre-execution replay gate (#111).

## Historical #167 read-only plan

After review, using the reviewed source checkout and an existing read-only credential, the operator can obtain an evidence-bound plan:

    ISSUE_NUMBER=167 DELIVERY_ID=task-f43f483eeeb455cfeaea98f94a4dbddd \
      PROJECTION_MODE=plan python -m portfolio_tasks.terminal_projection

If exact identity and evidence pass: failed, remove status:queued, no new labels/comment, mutation_authorized=false. Body hash and current labels are emitted; mismatch blocks. No manual mutation workflow included. The original editorial task is unfulfilled. Separate approval of the exact plan and fresh readback are required before changing #167. Never reapprove or replay. Tests use synthetic API state and trap subprocess/socket calls. Normal CI has no source mutation.
