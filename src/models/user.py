from sqlalchemy import Column, Integer, String, Date, Enum, TIMESTAMP, text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    gender = Column(Enum('male', 'female', 'other', name='gender'), nullable=False)
    birth_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(
        TIMESTAMP,
        server_default=text('CURRENT_TIMESTAMP'),
        server_onupdate=text('CURRENT_TIMESTAMP'),
        nullable=False
    )

class StyleQuestion(Base):
    __tablename__ = "style_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_type = Column(String(50), nullable=False)
    question_text = Column(String, nullable=False)
    display_order = Column(Integer, nullable=False)
    options = Column(JSON)
    multiple_select = Column(Boolean, default=False)

class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)
    preference_value = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(String)
    color_code = Column(String(7)) 