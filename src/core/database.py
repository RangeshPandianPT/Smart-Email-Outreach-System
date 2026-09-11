from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

SQLALCHEMY_DATABASE_URL = "sqlite:///./crm.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_connection():
    """
    Backwards compatibility context manager 
    for places where we used raw sqlite3.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from src.core.models import Base
    Base.metadata.create_all(bind=engine)
