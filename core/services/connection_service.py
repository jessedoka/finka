"""CRUD + validation + dry-run testing for user data-source connections.

Secrets never leave the API: reads return a redacted config where secret fields
are replaced by a `_secrets: {field: bool}` map of which are set. On update, a
secret the client omits is retained from the stored config (the frontend can't
resend a value it was never given).
"""

from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from integrations import registry
from integrations.registry import ProviderError, ProviderSpec
from models.connection import Connection
from schemas.connection import ConnectionCreate, ConnectionUpdate


def _spec_or_400(provider: str) -> ProviderSpec:
    try:
        return registry.get(provider)
    except ProviderError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


def redact_config(spec: ProviderSpec, config: dict[str, Any]) -> dict[str, Any]:
    """Config with secret values stripped, plus a `_secrets` set/unset map."""
    secrets = spec.secret_names()
    visible = {k: v for k, v in (config or {}).items() if k not in secrets}
    visible["_secrets"] = {name: bool((config or {}).get(name)) for name in secrets}
    return visible


def merge_config(spec: ProviderSpec, existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """New config, retaining a stored secret when the client omits/blanks it."""
    incoming = {k: v for k, v in (incoming or {}).items() if k != "_secrets"}
    merged = dict(incoming)
    for name in spec.secret_names():
        if not merged.get(name) and (existing or {}).get(name):
            merged[name] = existing[name]
    return merged


class ConnectionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_connections(self, user_id: UUID) -> list[Connection]:
        result = await self.db.scalars(
            select(Connection)
            .where(Connection.user_id == user_id)
            .order_by(Connection.created_at)
        )
        return list(result.all())

    async def create(self, user_id: UUID, data: ConnectionCreate) -> Connection:
        spec = _spec_or_400(data.provider)
        config = {k: v for k, v in (data.config or {}).items() if k != "_secrets"}
        missing = spec.missing_required(config)
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields for {spec.display_name}: {', '.join(missing)}",
            )
        conn = Connection(
            user_id=user_id,
            provider=data.provider,
            label=data.label,
            config=config,
            is_active=data.is_active,
            is_long_term=data.is_long_term,
        )
        self.db.add(conn)
        await self.db.commit()
        await self.db.refresh(conn)
        return conn

    async def update(self, connection_id: int, user_id: UUID, data: ConnectionUpdate) -> Connection:
        conn = await self._get_owned(connection_id, user_id)
        fields = data.model_dump(exclude_unset=True)
        if "config" in fields and fields["config"] is not None:
            spec = _spec_or_400(conn.provider)
            fields["config"] = merge_config(spec, conn.config or {}, fields["config"])
        for field, value in fields.items():
            setattr(conn, field, value)
        await self.db.commit()
        await self.db.refresh(conn)
        return conn

    async def delete(self, connection_id: int, user_id: UUID) -> None:
        conn = await self._get_owned(connection_id, user_id)
        await self.db.delete(conn)
        await self.db.commit()

    async def test(self, provider: str, config: dict[str, Any]) -> dict[str, Any]:
        """Dry-run: fetch a balance from submitted config without saving."""
        spec = _spec_or_400(provider)
        config = {k: v for k, v in (config or {}).items() if k != "_secrets"}
        try:
            value = await spec.fetch_gbp(config)
            return {"ok": True, "value": float(value), "error": None}
        except ProviderError as e:
            return {"ok": False, "value": None, "error": str(e)}

    async def _get_owned(self, connection_id: int, user_id: UUID) -> Connection:
        conn = await self.db.scalar(
            select(Connection).where(
                Connection.id == connection_id, Connection.user_id == user_id
            )
        )
        if conn is None:
            raise HTTPException(status_code=404, detail="Connection not found")
        return conn
