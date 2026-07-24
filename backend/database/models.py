from sqlalchemy import String, Column, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    budget = Column(Integer)
    expected_completion = Column(String)
    sector = Column(String)
    status = Column(String, nullable=False)
    description = Column(String)
    date = Column(String)
    source = Column(String, nullable=False)
    scraped_at = Column(String, nullable=False)


