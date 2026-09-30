# Open Syntara PRs carried into the migration

The migration branch is based on the merged `feat/ANSTRAT-1803` branch snapshot. These PRs are not included in that snapshot and have not been recreated or closed. Their original Syntara PRs remain the source of truth until follow-up work is split across the two repositories.

| Original PR | Planned follow-up |
| --- | --- |
| [#725 — target metadata and platform mapping](https://github.com/syntara-orchestration/syntara/pull/725) | EP models, registries, placement and migrations here; Syntara integration/schema/contracts in Syntara. |
| [#723 — Kubernetes worker manager](https://github.com/syntara-orchestration/syntara/pull/723) | EP worker manager/protocol here; Syntara dispatch, configuration and compose in Syntara. |
| [#701 — SDK node containers](https://github.com/syntara-orchestration/syntara/pull/701) | Decide node/protocol ownership with #723 before splitting images, runtime and Syntara workflow routing. |
| [#673 — workload data sharing](https://github.com/syntara-orchestration/syntara/pull/673) | Reconcile and move EP documentation here. |
| [#632 — cluster/target/scheduler design](https://github.com/syntara-orchestration/syntara/pull/632) | Reconcile against merged docs and move remaining EP design here. |
| [#648 — OpenShift cold-start POC](https://github.com/syntara-orchestration/syntara/pull/648) | Keep as a historical POC until it is compared with #723/#701; port only unmerged work that remains needed. |

The Syntara feature branch and its PRs remain available. The source branch archive and `execution-plane-pr-inventory.json` retain the inspected baseline and PR metadata for this migration.
