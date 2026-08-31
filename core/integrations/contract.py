from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Awaitable, Callable

class ProviderError(RuntimeError):
    """Raised when a provider can't produce a balance from its config."""


@dataclass(frozen=True)
class ProviderField:
    name: str
    label: str
    secret: bool = False
    required: bool = True
    help: str = ""
    placeholder: str = ""

@dataclass(frozen=True)
class ProviderSpec:
    key: str
    display_name: str
    fields: list[ProviderField]
    # The raw adapter. Call `fetch_gbp()` instead — it enforces the contract.
    fetch: Callable[[dict[str, Any]], Awaitable[Any]]
    # Optional projection knobs a connection may set in its config; listed so the
    # projection service and the UI know which extra keys are meaningful.
    projection_fields: list[ProviderField] = field(default_factory=list)

    async def fetch_gbp(self, config: dict[str, Any]) -> Decimal:
        """Fetch this source's value as a Decimal, normalising ALL failures.

        The contract every caller relies on: this raises `ProviderError` and
        nothing else. Aggregation (net_worth_service) catches only ProviderError
        so one broken source contributes 0 instead of sinking the whole
        snapshot — a provider leaking a raw httpx/parse error would defeat that.
        Enforced here, centrally, so a new provider can't forget it.
        """
        try:
            value = await self.fetch(config or {})
        except ProviderError:
            raise
        except Exception as e:  # network, auth, parsing, provider-native errors
            raise ProviderError(f"{self.display_name}: {e}") from e
        try:
            return Decimal(str(value))
        except Exception as e:
            raise ProviderError(f"{self.display_name} returned a non-numeric value: {value!r}") from e

    def field_names(self) -> set[str]:
        return {f.name for f in self.fields} | {f.name for f in self.projection_fields}

    def secret_names(self) -> set[str]:
        return {f.name for f in self.fields if f.secret}

    def missing_required(self, config: dict[str, Any]) -> list[str]:
        return [f.name for f in self.fields if f.required and not config.get(f.name)]