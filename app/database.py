from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DB_URL = "postgresql+psycopg2://neondb_owner:npg_yjwS1ZTPgH0A@ep-sparkling-sea-a1g0npt0-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(
    DB_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()