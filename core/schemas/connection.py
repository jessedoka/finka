from typing import Any

from pydantic import BaseModel, ConfigDict


class ConnectionBase(BaseModel):
    provider: str
    label: str
    config: dict[str, Any] = {}
    is_active: bool = True
    is_long_term: bool = False


class ConnectionCreate(ConnectionBase):
    pass


class ConnectionUpdate(BaseModel):
    """All optional — PATCH only touches the fields that are provided."""
    label: str | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None
    is_long_term: bool | None = None


class ConnectionResponse(BaseModel):
    id: int
    provider: str
    label: str
    is_active: bool
    is_long_term: bool
    # Secret field values are never returned; this is the redacted config
    # (secrets replaced with a boolean "is set" marker under `_secrets`).
    config: dict[str, Any]
    # Sync health from the last snapshot — so the UI can show why an active
    # source isn't contributing.
    last_synced_at: str | None = None
    last_status: str | None = None
    last_error: str | None = None
    last_value: float | None = None
    model_config = ConfigDict(from_attributes=True)


class ProviderFieldSchema(BaseModel):
    name: str
    label: str
    secret: bool
    required: bool
    help: str
    placeholder: str


class ProviderSchema(BaseModel):
    key: str
    display_name: str
    fields: list[ProviderFieldSchema]
    projection_fields: list[ProviderFieldSchema]


class ConnectionTestRequest(BaseModel):
    provider: str
    config: dict[str, Any] = {}


class ConnectionTestResult(BaseModel):
    ok: bool
    value: float | None = None
    error: str | None = None
