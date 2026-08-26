"""
One-time SQLite migration for the Context/Image Engine integration.

Run from backend/:
    python database/migrate_observation_engine.py
"""

from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import inspect, text
from database.db import engine
from models import Base

# Import all models through models/__init__.py before create_all.
Base.metadata.create_all(bind=engine)

project_columns = {
    "location_geometry": "JSON",
    "location_geofence_m": "FLOAT",
    "location_geometry_status": "VARCHAR",
    "location_geometry_source": "VARCHAR",
    "location_geometry_confidence": "FLOAT",
    "location_geometry_length_km": "FLOAT",
    "location_geometry_metadata": "JSON",
}

evidence_columns = {
    "ai_broad_stage": "VARCHAR",
    "ai_stage": "VARCHAR",
    "ai_stage_completion": "VARCHAR",
    "ai_confidence": "FLOAT",
    "ai_evidence": "VARCHAR",
    "ai_activities": "VARCHAR",
    "context_status": "VARCHAR",
    "location_status": "VARCHAR",
    "time_status": "VARCHAR",
    "provenance_status": "VARCHAR",
    "distance_to_project_m": "FLOAT",
    "location_match_type": "VARCHAR",
    "capture_age_days": "FLOAT",
}

inspector = inspect(engine)
project_existing = {c["name"] for c in inspector.get_columns("projects")}
evidence_existing = {c["name"] for c in inspector.get_columns("evidence")}

with engine.begin() as conn:
    for name, sql_type in project_columns.items():
        if name not in project_existing:
            conn.execute(text(f"ALTER TABLE projects ADD COLUMN {name} {sql_type}"))
    for name, sql_type in evidence_columns.items():
        if name not in evidence_existing:
            conn.execute(text(f"ALTER TABLE evidence ADD COLUMN {name} {sql_type}"))

# Observation table is created by metadata; show the current state.
inspector = inspect(engine)
print("Migration complete.")
print("Evidence columns now include:")
print(sorted(c["name"] for c in inspector.get_columns("evidence")))
print("Observation table exists:", "observations" in inspector.get_table_names())
