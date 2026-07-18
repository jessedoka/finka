from fastapi import APIRouter

router = APIRouter(prefix="/api/categories", tags=['categories'])

@router.get("/")
async def list_categories():
    return {"message": "not implemented yet"}

