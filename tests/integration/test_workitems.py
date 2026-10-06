"""Submit a script work item against a running compose + kind stack.

These checks reuse ``tools/submit_work_item.py``. They stay skipped unless
``EP_LIVE_STACK=1`` so the default unit suite does not need the local API.
"""

from __future__ import annotations

import importlib.util
import os
import uuid
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LIVE_STACK = os.environ.get("EP_LIVE_STACK") == "1"

pytestmark = [
    pytest.mark.live_stack,
    pytest.mark.skipif(not LIVE_STACK, reason="requires compose+kind (EP_LIVE_STACK=1)"),
]


def _load_submit_work_item() -> object:
    path = PROJECT_ROOT / "tools" / "submit_work_item.py"
    spec = importlib.util.spec_from_file_location("ep_submit_work_item", path)
    if spec is None or spec.loader is None:
        msg = f"Could not load {path}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def submit() -> object:
    return _load_submit_work_item()


def _ready_targets(submit: object, api_url: str, token: str) -> list[dict[str, Any]]:
    status, payload = submit.ep_request("GET", f"{api_url.rstrip('/')}/v1/execution-targets", token)
    assert status < 400, f"Listing execution targets failed ({status}): {payload}"
    assert isinstance(payload, list)
    return [target for target in payload if target.get("status") == "ready" and target.get("enabled")]


def test_script_work_item_completes_on_kind_target(submit: object) -> None:
    api_url = os.environ.get("EP_API_URL", submit.DEFAULT_API_URL)
    project_id = submit.DEFAULT_PROJECT_ID
    token = submit.ep_service_token(project_id)
    targets = _ready_targets(submit, api_url, token)
    assert targets, "No ready execution target; run tools/deploy_kind_execution_target.py first"

    marker = uuid.uuid4().hex
    request_id = str(uuid.uuid4())
    payload = submit.build_payload(
        language="python",
        code=f"print({marker!r})",
        timeout_seconds=60,
        environment={},
        image=os.environ.get("EP_NODE_IMAGE", submit.DEFAULT_IMAGE),
    )
    submitted = submit.submit_work_item(
        api_url,
        token,
        request_id=request_id,
        work_correlation_id=uuid.uuid4(),
        payload=payload,
    )
    assert submitted["request_id"] == request_id
    assert submitted["status"] in {"pending", "claimed", "dispatched", "completed"}

    finished = submit.wait_for_work_item(api_url, token, request_id, timeout_seconds=300)
    assert finished["status"] == "completed", finished
    result = finished.get("result") or {}
    output = result.get("output") or result
    stdout = str(output.get("stdout", ""))
    assert marker in stdout or marker in str(result)
