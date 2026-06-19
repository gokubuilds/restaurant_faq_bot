"""
database.py — SQLAlchemy SQLite setup for RAG Chatbot
Tables:
  chat_history   — conversation log
  knowledge_base — tracks which PDF is currently active in the vector store
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./chatbot.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id         = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(100), index=True, nullable=False)
    role       = Column(String(20), nullable=False)   # "user" | "assistant"
    content    = Column(Text, nullable=False)
    timestamp  = Column(DateTime, default=datetime.utcnow, nullable=False)


class KnowledgeBase(Base):
    """Tracks the PDF that is currently embedded in the vector store."""
    __tablename__ = "knowledge_base"

    id          = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename    = Column(String(255), nullable=False)
    filepath    = Column(String(512), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active   = Column(Boolean, default=True, nullable=False)


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency injector: yields a DB session, then closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
