# AO and EP service integration

AO owns workflow authorization, Temporal activities, integrations, user-facing
status, and Temporal task tokens. EP owns accepted work, execution targets,
cluster credentials, attempt state, result persistence, and completion delivery.
Both services may use the existing PostgreSQL server, but EP has its own
database and runtime/migration roles. AO does not read or write EP tables.

## Submission and completion

AO's script activity validates the node parameters and sends a versioned
`invocation`, selected `image`, and `output_config` to EP over authenticated
HTTP. AO saves its encrypted request and Temporal token binding before
submission. A stable request ID makes lost HTTP acknowledgements and Temporal
activity retries idempotent; retries use the originally saved payload.

EP stores work in its own database and returns accepted state. Completion is
committed with EP's outbox event and delivered over mutually authenticated HTTP
to AO. AO persists and deduplicates the callback in its inbox, then completes
or fails the original Temporal activity. AO can also reconcile a missing
callback against EP status. EP never connects to Temporal.

Cancellation intent is stored on AO's side and retried through EP's HTTP API by
stable request ID. EP maps it to the current execution attempt and gRPC node
protocol. A terminal result observed during cancellation wins the race.

## Integration and target configuration

AO remains the source of integration configuration. Its integration-sync
outbox sends revisioned desired state to EP over an authenticated API. EP
reconciles that state to its own cluster and target records and returns an
observed revision/status. AO displays `pending`, `ready`, or a safe error while
the two services converge; neither database participates in a cross-service
transaction.

The first deployment uses the existing PostgreSQL server with a distinct EP
database, database roles, and migration chain. EP encrypts persisted invocation
payloads and cluster-management credentials with its own configured key.

## Node communication

For the first release AO is the only configured EP client and script is the
only dispatched node type. AO chooses the container image and invocation. EP's
cold-start backend uses an authenticated Kubernetes API port-forward as a
tunnel for the SDK gRPC protocol. That protocol carries inputs, execution
events, returned output, and any stdout/stderr fields. Pod logs, workload input
Secrets, exec, and stdin/stdout control channels are not part of the service
contract.

See [cold-start-node-dispatch.md](cold-start-node-dispatch.md) for worker
allocation and recovery semantics, and
[service-isolation-revisit-decisions.md](service-isolation-revisit-decisions.md)
for defaults that need review as EP gains clients and backends.
