import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.requests import Request

from routes.projects import router as project_router
from routes.auth import router as auth_router
from routes.proposals import router as proposal_router
from routes.evidence import router as evidence_router
from routes.blockchain import router as blockchain_router
from routes.observations import router as observations_router

app = FastAPI(
    title="Promise VS Progress",
    version="1.0.0"
)

# Dev origins for the Vite dev server (default port 5173, but Vite falls
# back to the next free port if it's taken, so a small range is allowed).
# In production the React build is served by this same FastAPI app, so
# requests are same-origin and CORS doesn't come into play at all.
DEV_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5174",
    "http://localhost:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All API routes live under /api. This is what the React app calls in
# both dev (proxied by Vite, see frontend-react/vite.config.js) and
# production (same-origin, since FastAPI serves the built frontend too).
app.include_router(project_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(proposal_router, prefix="/api")
app.include_router(evidence_router, prefix="/api")
app.include_router(blockchain_router, prefix="/api")
app.include_router(observations_router, prefix="/api")


# --- Serve citizen-uploaded evidence photos -----------------------------
# routes/evidence.py writes here (backend/uploads/evidence/) and returns
# image_url pointing at this mount, e.g. "/uploads/evidence/<id>.jpg".
# Kept separate from /assets (the built React app) so the two never clash.
UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory=UPLOADS_DIR),
    name="uploads"
)


# --- Serve the built React app (production) ---------------------------
# `npm run build` in frontend-react/ outputs straight into backend/static
# (see frontend-react/vite.config.js). If that folder doesn't exist yet
# (e.g. fresh clone, dev-only workflow), the API still runs fine on its
# own -- just without the static frontend attached.
STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=STATIC_DIR / "assets"),
        name="assets"
    )

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str, request: Request):
        """
        Catch-all so React Router's client-side routes (e.g. /projects/12)
        work on a hard refresh: any path that isn't /api/... or a static
        asset gets index.html, and React Router takes it from there.
        """

        candidate = STATIC_DIR / full_path

        if full_path and candidate.is_file():
            return FileResponse(candidate)

        return FileResponse(STATIC_DIR / "index.html")
