from sqlalchemy import Column, Integer, String, Date, Enum, TIMESTAMP, text, JSON, Boolean, ForeignKey, Float
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

    # リレーションシップ
    responses = relationship("UserResponse", back_populates="user")
    face_measurements = relationship("FaceMeasurement", back_populates="user")

class StyleQuestion(Base):
    __tablename__ = "style_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_type = Column(String(50), nullable=False)
    question_text = Column(String(500), nullable=False)
    display_order = Column(Integer, nullable=False)
    options = Column(JSON)
    multiple_select = Column(Boolean, default=False)

    # リレーションシップ
    responses = relationship("UserResponse", back_populates="question")

class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)
    preference_value = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(String(1000))
    color_code = Column(String(7))

    # リレーションシップ
    responses = relationship("UserResponse", back_populates="preference")

class UserResponse(Base):
    __tablename__ = "user_responses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("style_questions.id"), nullable=False)
    selected_preference_id = Column(Integer, ForeignKey("preferences.id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(
        TIMESTAMP,
        server_default=text('CURRENT_TIMESTAMP'),
        server_onupdate=text('CURRENT_TIMESTAMP'),
        nullable=False
    )

    # リレーションシップ
    user = relationship("User", back_populates="responses")
    question = relationship("StyleQuestion", back_populates="responses")
    preference = relationship("Preference", back_populates="responses")

class FaceMeasurement(Base):
    __tablename__ = "face_measurements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    face_width = Column(Float, nullable=False)      # 顔の幅
    eye_distance = Column(Float, nullable=False)    # 目の間の距離
    cheek_area = Column(Float, nullable=False)      # 頬の面積
    nose_height = Column(Float, nullable=False)     # 鼻の高さ
    temple_position = Column(Float, nullable=False) # こめかみの位置
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), nullable=False)

    # リレーションシップ
    user = relationship("User", back_populates="face_measurements")