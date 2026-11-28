# Proposed V5.6 maintenance verification exception

**Historical record only. V5.10 retires this exception and removes its workflow,
runtime and tests. Do not follow the historical execution instructions below.**
Preserve [issue #176](https://github.com/Young-Consultations/portfolio-tasks/issues/176),
[wrapper run 45906558087](https://github.com/Young-Consultations/portfolio-tasks/actions/runs/45906558087),
and [receiver/target run 45906615092](https://github.com/Young-Consultations/consulting-playbook/actions/runs/45906615092).
No replay or live dispatch is authorized.

**Owner accepted this temporary exception in principle on 2026-11-25.**
Draft implementation and exact-head merge acceptance remain separate; no
operational authority is granted. The exception applies only to the dedicated
verify-only maintenance path, not the label-only production admission baseline.
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
is exposed. Final owner acceptance of the exact corrected implementation
under requirements/README.md is required before merge.

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
The v2 marker binds workflow ref, SHA, run ID and exact task revision. Read
GitHub run metadata to verify first-attempt owner dispatch and its canonical
run title; projection additionally requires successful prepare job/reservation
step evidence from attempt one. Both source workflows use Actions read only
for this evidence. Freeze source main until projection completes: the
projection checkout SHA must match the reserved smoke run SHA. This is a
run-metadata binding, not an independently signed comment provenance proof;
other privileged workflows/owner edits remain outside the trust boundary.
Failure after reservation is terminal for that issue. Ambiguous write/readback
stops, never delete the reservation or rerun. If no reservation was created,
stop and review instead of retrying the same issue. Concurrent external edits
or labels are not atomically locked by GitHub; hold all source approvals and
do not edit or label the smoke issue through completion.

The normal receiver sends results through the existing authenticated source
projector. The temporary v5 exception accepts only result-mode for the exact
reserved verify-only issue, using the exact v5 trust policy, correlated
admission and receipt, exact recomputed v5 effect class and digest (including
forwarding if present), no branch/PR, and no lifecycle status labels. All
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
