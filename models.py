from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    username = Column(String(100))
    preferred_name = Column(String(100))
    language_code = Column(String(10), default="he")
    timezone = Column(String(50), default="Asia/Jerusalem")
    gender_preference = Column(String(20))
    total_messages = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    notifications_enabled = Column(Boolean, default=True)
    encrypted_data = Column(Text)
    preferences = Column(JSON)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    message_type = Column(String(50), default="text")

class UserMemory(Base):
    __tablename__ = "user_memory"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    memory_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    importance = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
