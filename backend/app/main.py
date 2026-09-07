from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    products,
    inventory,
    smart_cart,
    sale_event,
    purchase,
    orders,
    support,
    chat,
)


app = FastAPI(
    title="Agentic Retail Assistant API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(smart_cart.router)
app.include_router(sale_event.router)
app.include_router(purchase.router)
app.include_router(orders.router)
app.include_router(support.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {
        "message": "Agentic Retail Assistant API",
        "status": "running",
    }