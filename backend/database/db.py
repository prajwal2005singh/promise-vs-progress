from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

DATABASE_URL = "sqlite:///projects.db"


print("Database path:", Path("projects.db").resolve())

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()