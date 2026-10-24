from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .db import engine, Base
from . import models
from .auth import router as auth_router
from .routes import router
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    yield
app = FastAPI(title="BlastRadius", lifespan=lifespan)
@app.middleware("http")
async def browser_safety(request: Request, call_next):
    # Same-origin browser writes only; non-browser API clients use a session cookie.
    if request.method not in {"GET","HEAD","OPTIONS"} and request.headers.get("sec-fetch-site") == "cross-site":
        return JSONResponse(status_code=403,content={"detail":"Cross-site writes are not allowed"})
    response = await call_next(request)
    response.headers["Cache-Control"]="no-store"
    response.headers["X-Content-Type-Options"]="nosniff"
    return response
@app.get("/health")
def health(): return {"status":"ok"}
app.include_router(auth_router)
app.include_router(router)
from .analysis_routes import router as analysis_router
app.include_router(analysis_router)
