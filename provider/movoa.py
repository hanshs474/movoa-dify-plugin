from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools import _client as movoa


class MovoaProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """Check the key with a read-only account lookup; it starts no run."""
        key = (credentials.get("api_key") or "").strip()
        if not key:
            raise ToolProviderCredentialValidationError("API key is required")
        try:
            movoa.credits(api_key=key)
        except movoa.MovoaError as e:
            raise ToolProviderCredentialValidationError(str(e))
