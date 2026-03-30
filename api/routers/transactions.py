from fastapi import APIRouter

router = APIRouter(prefix="/api/transactions", tags=['transactions'])

@router.get("/")
async def list_transactions():
    return {"message": "not implemented yet"}

