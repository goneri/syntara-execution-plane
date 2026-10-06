# Combined AO + EP Kind demo: setup record

**Status:** the commands below describe the intended split-service topology;
this runbook has not yet been exercised against the current AO and EP PR heads.
Do not treat the feature-branch demo or an in-process EP worker fixture as
combined-service evidence.

The test target is one script workflow submitted through AO, accepted by the
separate EP API, run by the EP worker as a cold-start Job, returned over the
SDK gRPC protocol, committed to the EP completion outbox, and delivered to AO
for Temporal completion. AO and EP use distinct databases on the same local
PostgreSQL server.

## Required services and configuration

- AO API, Temporal, AO workers, and PostgreSQL from the Syntara checkout.
- EP API, EP worker, and Alembic migration from the standalone
  `syntara-execution-plane` checkout. Build an EP image from that checkout and
  set `EP_IMAGE` for the AO compose stack.
- A separate `execution_plane` database and EP runtime/migration roles. The AO
  compose bootstrap creates these; apply EP Alembic migrations with the same
  EP payload-encryption key that the API and worker use.
- A local Kind cluster with a CNI that enforces NetworkPolicy. The EP worker
  container must reach the Kubernetes API server and use a target credential
  scoped to the workload namespace.
- Valid TLS for the EP API and AO callback, plus the verified Kubernetes API
  CA for the target. Do not disable certificate validation to work around a
  missing or hostname-mismatched CA.
- A script node image pinned by digest and available to the Kind node.

## Flow to exercise

1. Start PostgreSQL, create the separate EP database/roles, run AO migrations,
   and run EP migrations independently.
2. Start the EP API/worker and AO/Temporal services. Configure AO's EP URL,
   AO JWT issuer/key, EP callback URL, and callback mTLS identity.
3. Create an OpenShift integration through AO's integration API or UI, using a
   ServiceAccount credential scoped to the Kind workload namespace and its
   verified CA. Wait for the integration sync status to report `ready`; do not
   write EP tables directly from AO or the demo harness.
4. Submit a script workflow through AO. Confirm one AO request ID maps to one
   EP WorkItem and one claim-generation Job. Confirm the result fields,
   including stdout/stderr, arrived through gRPC and the AO callback completed
   the Temporal activity.
5. Inspect the WorkItem and completion event in the EP database, AO's callback
   inbox/binding in the AO database, and the worker Job/NetworkPolicy lifecycle.
   Verify both databases remain inaccessible to the other service runtime role.
6. Repeat with callback outage, AO/EP restart, cancellation, startup failure,
   and an ambiguous Execute result. An uncertain attempt must remain visible as
   `reconciliation_required` and must not get a second Job automatically.

The current feature-branch Konflux scripts predate the service split: they run
Alembic from an AO backend container, write target rows directly to EP tables,
and configure EP to connect directly to Temporal. They are not valid for this
topology. The migration PRs must replace that harness before it is enabled as a
combined-service test. The correct evidence requires exact AO/EP image SHAs,
node image digest, Kind/Kubernetes version, CNI, and scenario results.
