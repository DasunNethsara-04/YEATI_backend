import os

# Limit OpenBLAS, OMP, MKL to 1 thread to prevent memory exhaustion on multi-core Windows
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from route.locations import router as locations_router
from route.crops import router as crops_router
from route.analytics import router as analytics_router
from route.admin import router as admin_router
from route.courses import router as courses_router
from route.schedules import router as schedules_router

app: FastAPI = FastAPI(
    title="AgriPiyasa API",
    description="Smart Agricultural Advisory Platform for Sri Lanka",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(locations_router)
app.include_router(crops_router)
app.include_router(analytics_router)
app.include_router(admin_router)
app.include_router(courses_router)
app.include_router(schedules_router)


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    return {"message": "AgriPiyasa API is running"}
