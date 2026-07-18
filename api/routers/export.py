from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from services.auth import get_current_user
from services.export_service import ExportService

router = APIRouter(prefix="/api/export", tags=["export"])


def get_service(db: AsyncSession = Depends(get_db)) -> ExportService:
    return ExportService(db)


@router.get("/")
async def export_all(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ExportService, Depends(get_service)],
):
    """Full JSON dump of the current user's data — accounts, categories,
    transactions and net-worth snapshots — as a downloadable attachment."""
    data = await service.export_user(user)
    stamp = data["meta"]["generated_at"][:10]
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f'attachment; filename="finka-export-{stamp}.json"'
        },
    )
