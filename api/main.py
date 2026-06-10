from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import transactions, accounts, categories, net_worth

app = FastAPI(
    title="Finka API",
    description="Personal finance dashboard API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
    allow_headers=['Content-Type', 'Authorization']
)

app.include_router(transactions.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(net_worth.router)

@app.get('/health')
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment
    }