from sqlalchemy import create_engine, inspect

engine = create_engine("sqlite:///projects.db")

inspector = inspect(engine)

print(inspector.get_columns("project_proposals"))