from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from config import CORS_ORIGINS
from sqlalchemy import inspect, text

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
# Additive schema compatibility: preserve existing order rows.
with engine.begin() as connection:
    columns = {column['name'] for column in inspect(connection).get_columns('orders')}
    if 'claimed_at' not in columns:
        connection.execute(text('ALTER TABLE orders ADD COLUMN claimed_at TIMESTAMP NULL'))



# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="ERB - Easy Print & Collect",
    version="1.0.0"
)


# ============================================================
# Allow browser requests only from explicitly configured frontend origins.
# ============================================================

if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=['GET', 'POST', 'OPTIONS'],
        allow_headers=['Content-Type', 'X-Device-Token'],
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