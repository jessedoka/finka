from fastapi import APIRouter

router = APIRouter(prefix="/api/accounts", tags=['accounts'])

@router.get("/")
async def list_accounts():
    return {"message": "not implemented yet"}

