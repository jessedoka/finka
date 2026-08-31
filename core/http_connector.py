import httpx
from decimal import Decimal
from typing import Any 

from integrations.contract import ProviderError

def _extract(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as e:
                raise ProviderError(f"value_path segment '{part}' not found in list") from e
        elif isinstance(current, dict):
            if part not in current:
                raise ProviderError(f"value_path segment '{part}' not found in response")
            current = current[part]
        else:
            raise ProviderError(f"value_path segment '{part}' can't index a {type(current).__name__}")
    return current


async def http_gbp(config: dict[str, Any]) -> Decimal:
    url = config.get("url")
    if not url:
        raise ProviderError("Generic HTTP connector needs a url")
    method = (config.get("method") or "GET").upper()
    headers = config.get("headers") or {}
    value_path = config.get("value_path") or ""
    try:
        multiplier = Decimal(str(config.get("multiplier", 1)))
    except Exception as e:
        raise ProviderError(f"multiplier must be a number: {e}") from e

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.request(method, url, headers=headers)
        resp.raise_for_status()
        payload = resp.json()
    except httpx.HTTPError as e:
        raise ProviderError(f"HTTP request failed: {e}") from e
    except ValueError as e:
        raise ProviderError(f"Response was not JSON: {e}") from e

    raw = _extract(payload, value_path)
    try:
        return Decimal(str(raw)) * multiplier
    except Exception as e:
        raise ProviderError(f"Extracted value '{raw}' is not a number: {e}") from e