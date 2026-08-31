from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from integrations import registry
from models.connection import Connection
from models.user import User
from schemas.connection import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionTestRequest,
    ConnectionTestResult,
    ConnectionUpdate,
    ProviderSchema,
)
from services.auth import get_current_user
from services.connection_service import ConnectionService, redact_config

router = APIRouter(prefix="/api/connections", tags=["connections"])


def get_service(db: AsyncSession = Depends(get_db)) -> ConnectionService:
    return ConnectionService(db)


def _to_response(conn: Connection) -> ConnectionResponse:
    spec = registry.get(conn.provider)
    return ConnectionResponse(
        id=conn.id,
        provider=conn.provider,
        label=conn.label,
        is_active=conn.is_active,
        is_long_term=conn.is_long_term,
        config=redact_config(spec, conn.config or {}),
        last_synced_at=conn.last_synced_at.isoformat() if conn.last_synced_at else None,
        last_status=conn.last_status,
        last_error=conn.last_error,
        last_value=float(conn.last_value) if conn.last_value is not None else None,
    )


@router.get("/providers", response_model=list[ProviderSchema])
async def list_providers():
    """The registry manifest — drives the dynamic connect form on the frontend."""
    return [
        ProviderSchema(
            key=spec.key,
            display_name=spec.display_name,
            fields=[f.__dict__ for f in spec.fields],
            projection_fields=[f.__dict__ for f in spec.projection_fields],
        )
        for spec in registry.list_specs()
    ]


@router.get("/", response_model=list[ConnectionResponse])
async def list_connections(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ConnectionService, Depends(get_service)],
):
    conns = await service.list_connections(user.id)
    return [_to_response(c) for c in conns]


@router.post("/", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    body: ConnectionCreate,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ConnectionService, Depends(get_service)],
):
    conn = await service.create(user.id, body)
    return _to_response(conn)


@router.post("/test", response_model=ConnectionTestResult)
async def test_connection(
    body: ConnectionTestRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ConnectionService, Depends(get_service)],
):
    """Dry-run a provider config without saving — returns the fetched GBP value or the error."""
    return await service.test(body.provider, body.config)


@router.patch("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: int,
    body: ConnectionUpdate,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ConnectionService, Depends(get_service)],
):
    conn = await service.update(connection_id, user.id, body)
    return _to_response(conn)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: int,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ConnectionService, Depends(get_service)],
):
    await service.delete(connection_id, user.id)
