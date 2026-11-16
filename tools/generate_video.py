from __future__ import annotations

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools import _client as movoa
from tools._common import POLL_SECONDS, WAIT_SECONDS, explain


class GenerateVideoTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        prompt = (tool_parameters.get("prompt") or "").strip()
        if not prompt:
            yield self.create_text_message("prompt is required")
            return
        key = self.runtime.credentials.get("api_key")
        model = (tool_parameters.get("model") or movoa.DEFAULT_MODEL).strip()
        image_url = (tool_parameters.get("image_url") or "").strip() or None
        options = {
            "duration": int(tool_parameters["duration"]) if tool_parameters.get("duration") else None,
            "resolution": tool_parameters.get("resolution") or None,
            "aspect_ratio": tool_parameters.get("aspect_ratio") or None,
        }
        try:
            task_id = movoa.submit(prompt, model, image_url, api_key=key, **options)
        except movoa.MovoaError as err:
            yield self.create_text_message(explain(err))
            return
        try:
            url = movoa.wait(task_id, api_key=key, timeout=WAIT_SECONDS, poll_every=POLL_SECONDS)
        except movoa.TimeoutError:
            yield self.create_text_message(
                f"Movoa: still generating. Task id {task_id}; call check_status with it in a minute or two."
            )
            yield self.create_json_message({"task_id": task_id, "status": "generating"})
            return
        except movoa.MovoaError as err:
            yield self.create_text_message(explain(err))
            return
        yield self.create_link_message(url)
        yield self.create_json_message({"task_id": task_id, "status": "success", "url": url})
