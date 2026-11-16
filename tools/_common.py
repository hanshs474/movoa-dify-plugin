from tools import _client as movoa

WAIT_SECONDS = 240.0
POLL_SECONDS = 10.0


def explain(err: "movoa.MovoaError") -> str:
    if isinstance(err, movoa.AuthError):
        return f"Movoa: the API key is missing or invalid; create one at {movoa.KEYS_URL} ({err})"
    if isinstance(err, movoa.PlanError):
        return f"Movoa: this model or quality requires a plan, see https://movoa.ai/pricing ({err})"
    if isinstance(err, movoa.QuotaError):
        return f"Movoa: not enough credits for this run ({err})"
    if isinstance(err, movoa.BusyError):
        return f"Movoa: too many runs are generating at once on this account; wait for one ({err})"
    if isinstance(err, movoa.RejectedError):
        return f"Movoa: the content filter refused the prompt; reword it rather than retrying ({err})"
    if isinstance(err, movoa.GenerationError):
        return f"Movoa: the run failed ({err}); reword the prompt rather than retrying it as is"
    return f"Movoa: {err}"
