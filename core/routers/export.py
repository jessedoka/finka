from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response
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
    format: Literal["json", "csv"] = Query("json"),
):
    """Full dump of the current user's data — accounts, connections and
    net-worth snapshots — as a downloadable attachment. `format=csv` returns
    a zip of one CSV per entity instead of the single JSON document."""
    stamp = date.today().isoformat()

    if format == "csv":
        content = await service.export_csv(user)
        return Response(
            content=content,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="finka-export-{stamp}.zip"'
            },
        )

    data = await service.export_user(user)
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f'attachment; filename="finka-export-{stamp}.json"'
        },
    )
