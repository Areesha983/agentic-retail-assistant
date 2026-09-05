from fastapi import FastAPI

from app.api.products import router as products_router
from app.api.inventory import router as inventory_router
from app.api.smart_cart import router as smart_cart_router
from app.api.sale_event import router as sale_event_router
from app.api.purchase import router as purchase_router
from app.api.orders import router as orders_router
from app.api.support import router as support_router

app = FastAPI(
    title="Agentic Retail Assistant",
    description="Backend API for the Agentic AI Retail Assistant",
    version="1.0.0"
)


app.include_router(products_router)
app.include_router(inventory_router)
app.include_router(smart_cart_router)
app.include_router(sale_event_router)
app.include_router(purchase_router)
app.include_router(orders_router)
app.include_router(support_router)

@app.get("/")
def root():
    return {
        "message": "Agentic Retail Assistant API is running"
    }