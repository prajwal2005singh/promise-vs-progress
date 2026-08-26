import json
from pathlib import Path
from datetime import datetime
from models.user import User
from auth.hashing import hash_password

from database.db import SessionLocal
from models.project import Project

BASE_DIR = Path(__file__).resolve().parent.parent
json_file = BASE_DIR / "data" / "projects.json"

with open(json_file, "r", encoding="utf-8") as f:
    projects = json.load(f)

db = SessionLocal()
admin = (
    db.query(User)
    .filter(User.email == "admin@pvp.com")
    .first()
)

if admin is None:

    admin = User(
        name="System Administrator",
        email="admin@pvp.com",
        phone="9999999999",
        password_hash=hash_password("Admin@123"),
        google_id=None,
        role="ADMIN",
        is_verified=True,
        status="ACTIVE"
    )

    db.add(admin)
    db.commit()

    print("Default admin created.")

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
        location_geometry=item.get("location_geometry"),
        location_geofence_m=item.get("location_geofence_m"),
        budget=item.get("budget"),
        status=item["status"],
        progress_percent=item.get("progress_percent", 0),
        expected_completion=datetime.fromisoformat(
            item["expected_completion"]
        ) if item.get("expected_completion") else None,
        start_date=datetime.fromisoformat(
            item["start_date"]
        ) if item.get("start_date") else None,
        created_by=admin.id
    )

    db.add(project)

db.commit()
db.close()

print("Database seeded successfully!")