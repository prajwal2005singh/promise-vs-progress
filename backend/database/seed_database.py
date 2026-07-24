import json

from database.db import SessionLocal
from database.models import Project
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
json_file = BASE_DIR / "data" / "projects.json"

with open(json_file, "r", encoding="utf-8") as f:
    projects = json.load(f)

db = SessionLocal()

for item in projects:
    project = Project(
        name=item["name"],
        location=item["location"],
        budget=item["budget"],
        expected_completion=item["expected_completion"],
        sector=item["sector"],
        status=item["status"],
        description=item["description"],
        date=item["date"],
        source=item["source"],
        scraped_at=item["scraped_at"],
    )

    db.add(project)

db.commit()
db.close()

print("Database seeded successfully!")