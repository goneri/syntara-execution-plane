"""WorkerManager protocol — the swappable backend interface.

Concrete implementations (VanillaK8sWorkerManager, OpenShellWorkerManager) live
in submodules. The Task Executor selects an implementation at startup based on the
pool's backend_type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from execution_plane.models.work_item import WorkItem


class WorkerManager(Protocol):
    """Obtains a backend worker, dispatches one logical work item, and returns its result."""

    async def dispatch(self, work_item: WorkItem) -> dict[str, Any]:
        """Dispatch through the selected backend; application data moves over its node protocol."""
        ...
