from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routes.health import router as health_router
from routes.upload import router as upload_router
from routes.pricing import router as pricing_router
from routes.orders import router as orders_router

from models.database import engine, Base
from models.order import Order


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="ERB - Easy Print & Collect",
    version="1.0.0"
)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(health_router)
app.include_router(upload_router)
app.include_router(pricing_router)
app.include_router(orders_router)


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/",
    StaticFiles(
        directory="../frontend",
        html=True
    ),
    name="frontend"
)