from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from route.locations import router as locations_router
from route.crops import router as crops_router

app: FastAPI = FastAPI(
    title="YEATI API",
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


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    return {"message": "YEATI API is running 🌿"}
