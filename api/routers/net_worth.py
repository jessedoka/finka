from fastapi import APIRouter

router = APIRouter(prefix="/api/net-worth", tags=['net-worth'])

@router.get("/")
async def list_net_worth():
    return {"message": "not implemented yet"}

