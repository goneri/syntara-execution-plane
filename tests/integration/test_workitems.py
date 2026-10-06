"""Submit a script work item against a running compose + kind stack.

Uses ``execution_plane.work_item_client``, the same helpers as
``tools/submit_work_item.py``. Skipped unless ``EP_LIVE_STACK=1``.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import pytest

from execution_plane.work_item_client import (
    DEFAULT_PROJECT_ID,
    build_payload,
    default_api_url,
    default_node_image,
    ep_service_token,
    list_execution_targets,
    submit_work_item,
    wait_for_work_item,
)

LIVE_STACK = os.environ.get("EP_LIVE_STACK") == "1"

pytestmark = [
    pytest.mark.live_stack,
    pytest.mark.skipif(not LIVE_STACK, reason="requires compose+kind (EP_LIVE_STACK=1)"),
]


def _ready_targets(api_url: str, token: str) -> list[dict[str, Any]]:
    return [
        target
        for target in list_execution_targets(api_url, token)
        if target.get("status") == "active" and target.get("enabled")
    ]


def test_script_work_item_completes_on_kind_target() -> None:
    api_url = default_api_url()
    token = ep_service_token(DEFAULT_PROJECT_ID)
    targets = _ready_targets(api_url, token)
    assert targets, "No ready execution target; run tools/deploy_kind_execution_target.py first"

    marker = uuid.uuid4().hex
    request_id = str(uuid.uuid4())
    payload = build_payload(
        language="python",
        code=f"print({marker!r})",
        timeout_seconds=60,
        environment={},
        image=default_node_image(),
    )
    submitted = submit_work_item(
        api_url,
        token,
        request_id=request_id,
        work_correlation_id=uuid.uuid4(),
        payload=payload,
    )
    assert submitted["request_id"] == request_id
    assert submitted["status"] in {"pending", "claimed", "dispatched", "completed"}

    finished = wait_for_work_item(api_url, token, request_id, timeout_seconds=300)
    assert finished["status"] == "completed", finished
    result = finished.get("result") or {}
    output = result.get("output") or result
    stdout = str(output.get("stdout", ""))
    assert marker in stdout or marker in str(result)
