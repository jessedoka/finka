from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Awaitable, Callable
from collections.abc import Mapping

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
    fetch: Callable[[dict[str, Any]], Awaitable[Any]]
    projection_fields: list[ProviderField] = field(default_factory=list)

    # Which part gets monthly_contribution / growth_rate. "" means the whole source.
    projection_part: str = ""

    async def fetch_parts(self, config: dict[str, Any]) -> dict[str, Decimal]:
        """Fetch this source as named parts, normalising ALL failures.

        A provider returning one number becomes a single part named "".
        """
        try:
            value = await self.fetch(config or {})
        except ProviderError:
            raise
        except Exception as e:  # network, auth, parsing, provider-native errors
            raise ProviderError(f"{self.display_name}: {e}") from e
        raw = value if isinstance(value, Mapping) else {"": value}
        try:
            return {part: Decimal(str(v)) for part, v in raw.items()}
        except Exception as e:
            raise ProviderError(f"{self.display_name} returned a non-numeric value: {value!r}") from e

    async def fetch_gbp(self, config: dict[str, Any]) -> Decimal:
        """This source's total. Raises `ProviderError` and nothing else."""
        parts = await self.fetch_parts(config)
        return sum(parts.values(), Decimal("0"))

    def field_names(self) -> set[str]:
        return {f.name for f in self.fields} | {f.name for f in self.projection_fields}

    def secret_names(self) -> set[str]:
        return {f.name for f in self.fields if f.secret}

    def missing_required(self, config: dict[str, Any]) -> list[str]:
        return [f.name for f in self.fields if f.required and not config.get(f.name)]