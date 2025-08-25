# app/models/database.py
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, JSON, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmake, Session, relationship
from sqlalchemy.sql import func

from app.config import get_settings

settings = get_settings()
SQLALCHEMY_DATABASE_URL = settings.database_url

engine = create_engine(
  SQLALCHEMY_DATABASE_URL,
  connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- DB Models ---
class Culture(Base):
  __tablename__ = "cultures"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String(50), nullable=False, unique=True)
  code = Column(string(10), nullable=False, unique=True, index=True)
  description = Column(Text)
  config = Column(JSON, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  syllable_patterns = relationship("SyllablePattern", back_populates="culture", cascade="all, delete-orphan")
  generated_names = relationship("GeneratedName", back_populates="culture", cascade="all, delete-orphan")

  def __repr__(self):
    return f"<Culture(name='{self.name}', code='{self.code}')>"

Class SyllablePattern(Base):
  __tablename__ = "syllable_patterns"

  id = Column(Integer, primary_key=True, index=True)
  culture_id = Column(Integer, ForeignKey("cultures.id"), nullable=False)
  pattern_type = Column(String(20), nullable=False)
  pattern = Column(String(20), nullable=False)
  weight = Column(Float, default=1.0)
  gender = Column(String(20), nullable=True)

  culture = relationship("Culture", back_populates="syllable_patterns")

  __table_args__ = (
    Index('idx_culture_pattern_type', 'culture_id', 'pattern_type'),
    Index('idx_culture_gender', 'culture_id', 'gender'),
  )

  def __repr__(self):
    return f"<SyllablePattern(type='{self.pattern_type}', pattern='{self.pattern}')>"

class GeneratedName(Base):
  __tablename__ = "generated_names"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String(50), nullable=False, index=True)
  culture_id = Column(Integer, ForeignKey("cultures.id"), nullable=False)
  gender = Column(String(20), nullable=True)
  pronunciation = Column(String(100))
  syllables = Column(JSON)
  score = Column(Float, index=True)
  parameters = Column(JSON)
  usage_count = Column(Integer, default=0)
  created_at = Column(DateTime, default=datetime.utcnow, index=True)

  culture = relationship("Culture", back_populates="generated_names")

  __table_args__ = (
    Index('idx_culture_gender_score', 'culture_id', 'gender', 'score'),
    Index('idx_name_culture', 'name', 'culture_id', unique=True),
  )

  def __repr__(self):
    return f"<GeneratedName(name='{self.name}', culture='{self.culture.code if self.culture else 'unknown'}', score={self.score})>"
    
class NameRequest(Base):
  __tablename__ = "name_requests"

  id = Column(Integer, primary_key=True, index=True)
  request_id = Column(String(36), unique=True, index=True)
  culture_code = Column(String(10))
  gender = Column(String(20))
  count = Column(Integer)
  min_score = Column(Float)
  response_time_ms = Column(Float)
  success = Column(Integer, default=1)
  created_at = Column(DateTime, default=datetime.utcnow, index=True)

  def __repr__(self):
    return f"<NameRequest(id='{self.request_id}', culture='{self.culture_code}'>"

# --- DB Utilities ---
def get_db() -> Session:
  """
  Dependency to get database session.
  Use in FastAPI routes:

  @app.get("/")
  def read_root(db: Session = Depends(get_db)):
    return db.query(Culture).all()
  """
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

def init_db():
  Base.metadata.create_all(bind=engine)

def drop_all_tables():
  Base.metadata.drop_all(bind=engine)

# --- Helper functions ---
def get_culture_by_code(db: Session, code: str) -> Optional[Culture]:
  return db.query(Culture).filter(Culture.code == code).first()

def get_random_names(db: Session, culture_id: int, limit: int = 10) -> list:
  return db.query(GeneratedName)\
    .filter(GeneratedName.culture_id == culture_id)\
    .order_by(func.random())\
    .limit(limit)\
    .all()

def increment_usage_count(db: Session, name_id: int):
  name = db.query(GeneratedName).filter(GeneratedName.id == name_id).first()
  if name:
    name.usage_count += 1
    db.commit()
