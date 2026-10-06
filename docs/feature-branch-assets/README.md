# Historical feature-branch assets

These files are retained as source context from `feat/ANSTRAT-1803`. Their
deployment and Konflux scripts predate the service split: they configure an
in-process worker, run EP migrations from the AO backend, or write directly to
EP tables. Do not apply these manifests or use these scripts for the isolated
service topology.

Use the current standalone manifests in [`deploy/kubernetes/base`](../../deploy/kubernetes/base/)
and target-cluster dispatcher RBAC in
[`deploy/kubernetes/execution-target/rbac.yaml`](../../deploy/kubernetes/execution-target/rbac.yaml),
and follow the combined-service procedure in [`kind-demo-runbook.md`](../kind-demo-runbook.md).
