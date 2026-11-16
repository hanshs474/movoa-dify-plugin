from __future__ import annotations

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import _client as movoa
from tools._common import explain


class CheckStatusTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        task_id = (tool_parameters.get("task_id") or "").strip()
        if not task_id:
            yield self.create_text_message("task_id is required")
            return
        try:
            t = movoa.status(task_id, api_key=self.runtime.credentials.get("api_key"))
        except movoa.MovoaError as err:
            yield self.create_text_message(explain(err))
            return
        state = str(t.get("status") or "")
        videos = t.get("videos") or []
        if state == "success" and videos:
            yield self.create_link_message(str(videos[0]))
            yield self.create_json_message({"task_id": task_id, "status": "success", "url": videos[0]})
        elif state in ("failed", "canceled"):
            yield self.create_text_message(
                f"Movoa: the run {state} ({t.get('errorMessage') or 'no reason given'})"
            )
        elif t.get("queued"):
            yield self.create_text_message(
                f"Movoa: task {task_id} is waiting in the queue; check again later."
            )
            yield self.create_json_message(
                {"task_id": task_id, "status": "queued", "queue_eta_seconds": t.get("queueEta")}
            )
        else:
            yield self.create_text_message(
                f"Movoa: task {task_id} is still generating; check again shortly."
            )
            yield self.create_json_message({"task_id": task_id, "status": state or "processing"})
