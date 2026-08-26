"""Estimate and persist a project's GIS corridor.

Usage:
    cd backend
    python dev_scripts/estimate_project_geometry.py 1
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database.db import SessionLocal
from services.gis_service import GISServiceError, estimate_project_geometry, persist_estimated_geometry
from services.project_service import get_project_by_id


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python dev_scripts/estimate_project_geometry.py <project_id>")
        return 2

    try:
        project_id = int(sys.argv[1])
    except ValueError:
        print("project_id must be an integer")
        return 2

    db = SessionLocal()
    try:
        project = get_project_by_id(db, project_id)
        if project is None:
            print(f"Project {project_id} not found")
            return 1

        result = estimate_project_geometry(project)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get("geometry") is None:
            print("\nNo geometry persisted because the estimator could not build a usable corridor.")
            return 1

        persist_estimated_geometry(project, result)
        db.commit()
        print(f"\nPersisted {result['geometry_status']} geometry for project {project.id}.")
        return 0
    except GISServiceError as exc:
        print(f"GIS error: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
