# Proposed V5.6 maintenance verification exception

**Draft proposal; not approved operational authority.** Review and merge require
explicit owner approval of this narrowly scoped exception to the current
label-only source admission baseline and the one supported production path.
The normal label-triggered v4 route, historical reconciliation policy, target
activation and target conformance evidence remain unchanged.

Trace: FR-GOV-02–04, FR-RTE-01–04, FR-OUT-01, BR-01/03/04/09/12/13/16/25/27/28,
and the immutable organization v5 contract. The existing requirements and
interfaces are not silently amended. The proposed temporary maintenance
approval action is an authenticated owner manual dispatch with exact current
source revision and exact reviewed main SHA, NOT a status:approved label
(which would invoke the v4 route). The closed task payload contains approved
only after those checks and an authenticated, durable one-use reservation.
No implementation mode, arbitrary task body, target, actor or release input
is exposed. This proposal requires explicit acceptance of the temporary
approval-semantics exception under requirements/README.md before merge.

## Separately authorized future use (DO NOT RUN NOW)

After V5.6 prerequisites, environment protection and exact binding are accepted,
refresh the delivery drain, verify the paid approval hold and obtain a distinct
V5.7 owner authorization. Create a new owner-authored open issue with title
and body exactly as TITLE and BODY in portfolio_tasks/verify_smoke.py, no
labels, events or comments, not a PR, created within 24 hours. Inspect its
canonical task ID using revision_from(issue, source). Do not edit it or apply
status:approved. Dispatch the main-branch wrapper only at the reviewed merged
SHA with exact issue number, task ID, main SHA and confirmation verify-v5-once.
No run is authorized by this document.

The wrapper serializes maintenance attempts, denies reruns and consumes a
github-actions[bot] reservation before calling the existing immutable router.
Failure after reservation is terminal for that issue. Ambiguous write/readback
stops, never delete the reservation or rerun. If no reservation was created,
stop and review instead of retrying the same issue. Concurrent external edits
or labels are not atomically locked by GitHub; hold all source approvals and
do not edit or label the smoke issue through completion.

The normal receiver sends results through the existing authenticated source
projector. The temporary v5 exception accepts only result-mode for the exact
reserved verify-only issue, using the exact v5 trust policy, correlated
admission and receipt, no branch/PR, and no lifecycle status labels. All
ordinary v5 source deliveries remain denied before migration. A failed smoke
must retain evidence, not replay. Verify fresh trusted admission, target
verify-only path and result/receipt/forward/source projection, zero model
calls, no branch/PR and terminal verified outcome; router success alone is
not acceptance. Journal and projection writes are intended effects, not
zero-effect SIM. The result must be reviewed independently before adoption.

Remove the maintenance exception/wrapper with the separately reviewed source
migration after evidence is accepted; preserve historical records. Do not
enable targets, alter credentials, change source pins, dispatch live smoke,
or execute AI as part of this draft PR.
