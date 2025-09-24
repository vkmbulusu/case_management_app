from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite database
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, echo=False)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db():
    from models import Base
    Base.metadata.create_all(bind=engine)
