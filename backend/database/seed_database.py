import json
from pathlib import Path
from datetime import datetime

from database.db import SessionLocal
from models.project import Project

BASE_DIR = Path(__file__).resolve().parent.parent
json_file = BASE_DIR / "data" / "projects.json"

with open(json_file, "r", encoding="utf-8") as f:
    projects = json.load(f)

db = SessionLocal()

for item in projects:

    project = Project(
        name=item["name"],
        description=item["description"],
        category=item["category"],
        department=item["department"],
        mla_name=item.get("mla_name"),
        constituency=item.get("constituency"),
        location_name=item["location_name"],
        latitude=item["latitude"],
        longitude=item["longitude"],
        budget=item.get("budget"),
        status=item["status"],
        expected_completion=datetime.fromisoformat(
            item["expected_completion"]
        ) if item.get("expected_completion") else None,
        start_date=datetime.fromisoformat(
            item["start_date"]
        ) if item.get("start_date") else None,
        created_by=None
    )

    db.add(project)

db.commit()
db.close()

print("Database seeded successfully!")