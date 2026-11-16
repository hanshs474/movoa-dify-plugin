"""Official Python SDK for Movoa (https://movoa.ai), the AI video generator with sound.

    from movoa import generate_video
    clip = generate_video("a paper boat drifting down a rain gutter, low angle")
    still = generate_video("the camera slowly orbits the statue",
                           image_url="https://example.com/statue.jpg")

Create a key at https://movoa.ai/settings/apikeys and pass it as ``api_key=``
or set ``MOVOA_API_KEY``. Runs cost credits on your Movoa account, at the
prices on https://movoa.ai/pricing.

Standard library only.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional, Tuple

__version__ = "0.1.0"
__all__ = [
    "generate_video",
    "submit",
    "status",
    "wait",
    "credits",
    "MovoaError",
    "AuthError",
    "QuotaError",
    "PlanError",
    "BusyError",
    "RejectedError",
    "GenerationError",
    "TimeoutError",
    "MODELS",
    "DEFAULT_MODEL",
    "BASE_URL",
]

BASE_URL = "https://movoa.ai"
KEYS_URL = BASE_URL + "/settings/apikeys"

#: Model ids. ``minimax-h3`` is the default and the cheapest.
MODELS = (
    "minimax-h3",
    "veo-3-1-fast",
    "seedance-2-5",
    "seedance-2",
    "seedance-2-fast",
    "seedance-2-mini",
)
DEFAULT_MODEL = "minimax-h3"

POLL_EVERY = 10.0
TIMEOUT = 30 * 60.0


class MovoaError(RuntimeError):
    """Base class. Catch a subclass to decide what to do next.

    ``status`` is the HTTP status, ``code`` the envelope code (0, -1, -2, -3),
    ``reason`` the ``data.reason`` the service sent, if any.
    """

    def __init__(
        self,
        message: str,
        status: Optional[int] = None,
        code: Optional[int] = None,
        reason: Optional[str] = None,
        task_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.status = status
        self.code = code
        self.reason = reason
        self.task_id = task_id


class AuthError(MovoaError):
    """No API key, or the key is invalid or deleted. Create one at /settings/apikeys."""


class QuotaError(MovoaError):
    """The account does not have enough credits for this run."""


class PlanError(MovoaError):
    """This model or quality needs a plan, or the account has never bought credits."""


class BusyError(MovoaError):
    """Too many runs on this account are generating at once. Wait for one to finish."""


class RejectedError(MovoaError):
    """The content filter refused the prompt (code -2) or a cooldown is active (code -3). Reword it."""


class GenerationError(MovoaError):
    """The run was accepted but ended as failed or canceled.

    ``error_message`` and ``failure_kind`` carry what the service reported.
    """

    def __init__(self, message: str, task_id: str, error_message: Optional[str] = None, failure_kind: Optional[str] = None):
        super().__init__(message, task_id=task_id)
        self.error_message = error_message
        self.failure_kind = failure_kind


class TimeoutError(MovoaError):  # noqa: A001 - mirrors the SDK error set of every language
    """The wait ran out. The run may still finish; ``task_id`` lets you check it later."""


#: (method, url, body, headers) -> (http_status, raw_body_bytes). Raise OSError on network failure.
Transport = Callable[[str, str, Optional[dict], dict], Tuple[int, bytes]]


def _http(method: str, url: str, body: Optional[dict], headers: dict) -> Tuple[int, bytes]:
    data = json.dumps(body).encode() if body is not None else b""
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read() or b""


def _base(base_url: Optional[str]) -> str:
    return (base_url or os.environ.get("MOVOA_BASE_URL") or BASE_URL).rstrip("/")


def _key(api_key: Optional[str]) -> str:
    key = (api_key or os.environ.get("MOVOA_API_KEY") or "").strip()
    if not key:
        raise AuthError(f"No API key: pass api_key= or set MOVOA_API_KEY. Create a key at {KEYS_URL}")
    return key


def _raise_for(status_code: int, env: dict) -> None:
    """Map a refusal to the subclass that says what to do next.

    movoa.ai answers almost every refusal as HTTP 200 with a non-zero ``code``
    and a ``data.reason``, so the status code alone reads a refusal as success.
    """
    code = env.get("code") if isinstance(env.get("code"), int) else None
    data = env.get("data") if isinstance(env.get("data"), dict) else {}
    reason = data.get("reason") if isinstance(data.get("reason"), str) else None
    msg = str(env.get("message") or f"request failed (HTTP {status_code})")
    kw = dict(status=status_code, code=code, reason=reason)
    if status_code == 401:
        raise AuthError(f"{msg} (create a key at {KEYS_URL})" if KEYS_URL not in msg else msg, **kw)
    if code in (-2, -3):
        raise RejectedError(msg, **kw)
    if reason == "insufficient_credits":
        raise QuotaError(msg, **kw)
    if reason == "plan_required":
        raise PlanError(msg, **kw)
    if reason == "concurrency":
        raise BusyError(msg, **kw)
    if "no auth" in msg.lower():
        raise AuthError(f"{msg}. Create a key at {KEYS_URL}", **kw)
    raise MovoaError(msg, **kw)


def _call(path: str, body: Optional[dict], api_key: Optional[str], base_url: Optional[str], transport: Optional[Transport]) -> dict:
    headers = {
        "Authorization": f"Bearer {_key(api_key)}",
        "Content-Type": "application/json",
        "User-Agent": f"movoa-python/{__version__}",
    }
    st, raw = (transport or _http)("POST", _base(base_url) + path, body, headers)
    try:
        env = json.loads(raw) if raw else {}
    except ValueError:
        env = None
    if st == 401:
        _raise_for(401, env if isinstance(env, dict) else {})
    if not isinstance(env, dict):
        raise MovoaError(f"movoa.ai returned a non-JSON response (HTTP {st})", status=st)
    if st < 400 and env.get("code") == 0:
        return env
    _raise_for(st, env)
    raise AssertionError("unreachable")


def submit(
    prompt: str,
    model: str = DEFAULT_MODEL,
    image_url: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    transport: Optional[Transport] = None,
    **options: Any,
) -> str:
    """Start one run and return its task id without waiting.

    ``image_url`` (a public https image) makes it image-to-video, with the
    photo as the first frame. Extra keyword arguments go into ``options`` as
    they are, e.g. ``duration=6, resolution="768p", aspect_ratio="9:16"``.
    """
    if not str(prompt or "").strip():
        raise ValueError("prompt is required")
    opts: Dict[str, Any] = {"sound": True}
    opts.update({k: v for k, v in options.items() if v is not None})
    if image_url:
        opts["image_input"] = [image_url]
    body = {
        # The server routes by model; this only has to be non-empty.
        "provider": "auto",
        "mediaType": "video",
        "model": model,
        "scene": "image-to-video" if image_url else "text-to-video",
        "prompt": prompt,
        "options": opts,
    }
    env = _call("/api/ai/generate", body, api_key, base_url, transport)
    task_id = (env.get("data") or {}).get("id")
    if not task_id:
        raise MovoaError("movoa.ai accepted the run but returned no id")
    return str(task_id)


def status(
    task_id: str,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    transport: Optional[Transport] = None,
) -> Dict[str, Any]:
    """Return the run record. ``status`` is pending, processing, success, failed
    or canceled; ``videos`` holds the result URLs on success; ``queued`` and
    ``queueEta`` (seconds) are set while it waits in line."""
    env = _call("/api/ai/query", {"taskId": task_id}, api_key, base_url, transport)
    data = env.get("data")
    return data if isinstance(data, dict) else {}


def wait(
    task_id: str,
    *,
    api_key: Optional[str] = None,
    timeout: float = TIMEOUT,
    poll_every: float = POLL_EVERY,
    base_url: Optional[str] = None,
    transport: Optional[Transport] = None,
) -> str:
    """Poll a run every ``poll_every`` seconds until it finishes and return the video URL."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            data = status(task_id, api_key=api_key, base_url=base_url, transport=transport)
        except OSError:
            data = {}  # a dropped poll is not a failed generation
        state = str(data.get("status") or "").lower()
        if state == "success":
            videos = data.get("videos") or []
            if not videos:
                raise GenerationError(f"run {task_id} finished with no video", task_id)
            return str(videos[0])
        if state in ("failed", "canceled"):
            em = data.get("errorMessage")
            raise GenerationError(
                f"run {task_id} {state}" + (f": {em}" if em else ""), task_id, em, data.get("failureKind")
            )
        if time.monotonic() + poll_every > deadline:
            raise TimeoutError(
                f"run {task_id} is still generating after {timeout:g}s; check it later with status()",
                task_id=task_id,
            )
        time.sleep(poll_every)


def generate_video(
    prompt: str,
    model: str = DEFAULT_MODEL,
    image_url: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    timeout: float = TIMEOUT,
    poll_every: float = POLL_EVERY,
    base_url: Optional[str] = None,
    transport: Optional[Transport] = None,
    **options: Any,
) -> str:
    """Generate one clip with sound and return its URL."""
    task_id = submit(prompt, model, image_url, api_key=api_key, base_url=base_url, transport=transport, **options)
    return wait(task_id, api_key=api_key, timeout=timeout, poll_every=poll_every, base_url=base_url, transport=transport)


def credits(
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    transport: Optional[Transport] = None,
) -> int:
    """Return the remaining credits on the account."""
    env = _call("/api/user/get-user-credits", None, api_key, base_url, transport)
    return int((env.get("data") or {}).get("remainingCredits") or 0)
