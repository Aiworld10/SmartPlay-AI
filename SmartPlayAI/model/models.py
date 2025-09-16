# This define my sqlalchemy models classes for the database tables to work with postgresql
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, PrimaryKeyConstraint, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime


Base = declarative_base()


class Player(Base):
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    # Optional password field
    password_hash = Column(String(128), nullable=True)
    score = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    # Relationship to responses
    responses = relationship("Response", back_populates="player")


class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True, index=True)
    theme = Column(String(50), index=True, nullable=False)
    question_text = Column(Text, nullable=False)

    # Relationship to responses
    responses = relationship(
        "Response",
        back_populates="question",
        lazy="raise"  # Prevent lazy loading
    )


class Response(Base):
    __tablename__ = 'responses'

    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    response_text = Column(Text, nullable=False)
    # Score for this specific response
    score = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=func.now())

    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('player_id', 'question_id'),
    )

    # Relationships
    player = relationship("Player", back_populates="responses")
    question = relationship("Question", back_populates="responses")
