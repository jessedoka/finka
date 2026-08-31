from importlib.metadata import entry_points
from integrations.contract import ProviderSpec, ProviderField, ProviderError
from http_connector import http_gbp

def _build_spec(manifest: dict) -> ProviderSpec:
    return ProviderSpec(
        key=manifest["key"],
        display_name=manifest["display_name"],
        fetch=manifest["fetch"],
        fields=[ProviderField(**f) for f in manifest["fields"]],
        projection_fields=[ProviderField(**f) for f in manifest.get("projection_fields", [])],
    )

def _discover_specs() -> dict[str, ProviderSpec]:
    specs = {"http": ProviderSpec(
            key="http",
            display_name="Generic HTTP (JSON)",
            fetch=http_gbp,
            fields=[
                ProviderField("url", "URL", help="An endpoint returning JSON with a balance."),
                ProviderField(
                    "value_path", "Value path",
                    help="Dotted path to the number, e.g. data.balance.amount or accounts.0.balance.",
                    placeholder="data.balance",
                ),
                ProviderField(
                    "method", "HTTP method", required=False, help="GET (default) or POST.",
                    placeholder="GET",
                ),
                ProviderField(
                    "headers", "Headers (JSON object)", secret=True, required=False,
                    help='Auth headers, e.g. {"Authorization": "Bearer …"}. Stored as-is.',
                ),
                ProviderField(
                    "multiplier", "Multiplier", required=False,
                    help="Scales the value — e.g. 0.01 to convert pennies to pounds. Also use to pre-convert currency (no FX built in).",
                    placeholder="1",
                ),
            ],
            projection_fields=[
                ProviderField(
                    "monthly_contribution", "Monthly contribution", required=False,
                    help="Recurring amount added each month. Held flat in the projection if unset.",
                ),
                ProviderField(
                    "growth_rate", "Annual growth rate (%)", required=False,
                    help="Expected yearly growth, as a percentage — e.g. 5 for 5%.",
                    placeholder="5",
                ),
            ],
        )}
    for ep in entry_points(group="finka.providers"):
        specs[ep.name] = _build_spec(ep.load())
    return specs

_SPECS = _discover_specs()

def list_specs() -> list[ProviderSpec]:
    return list(_SPECS.values())

def get(key: str) -> ProviderSpec:
    spec = _SPECS.get(key)
    if spec is None:
        raise ProviderError(f"Unknown provider '{key}'")
    return spec