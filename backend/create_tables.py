from database.db import engine
from models import Base



# Recreate everything
Base.metadata.create_all(bind=engine)

print("Database created successfully!")