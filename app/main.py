from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.correlation import router as correlation_router
from app.api.neat import router as neat_router
from app.api.report import router as report_router
from app.api.simulate import router as simulate_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks (currently noop)."""
    yield


app = FastAPI(
    title="SID Portfolio Optimization API",
    description=(
        "Multi-objective evolutionary optimization (MOEP + NSGA-II) with TOPSIS "
        "arbitration, PSD-safe covariance handling, HV/IGD indicators, and "
        "Excel export. Live convergence streaming via Server-Sent Events."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(correlation_router, prefix="/api", tags=["correlation"])
app.include_router(simulate_router, prefix="/api", tags=["simulate"])
app.include_router(report_router, prefix="/api", tags=["report"])
app.include_router(neat_router, prefix="/api", tags=["neat"])


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": "sid-api", "version": "1.0.0"}


@app.get("/", tags=["meta"])
async def root():
    return {
        "service": "SID Portfolio Optimization API",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }
