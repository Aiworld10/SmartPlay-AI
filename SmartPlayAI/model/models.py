# This define my sqlalchemy models classes for the database tables to work with postgresql
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, PrimaryKeyConstraint, func, select
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import event
from sqlalchemy.orm import Mapped, mapped_column
Base = declarative_base()


class Player(Base):
    __tablename__ = 'players'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False)
    # Optional password field
    password_hash: Mapped[str] = mapped_column(String(128), nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    # Relationship to responses
    responses = relationship(
        "Response",
        back_populates="player",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Player(id={self.id}, name={self.name}, score={self.score})>"


class Question(Base):
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    theme: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship to responses
    responses = relationship(
        "Response",
        back_populates="question",
        lazy="raise"  # Prevent lazy loading
    )

    def __repr__(self):
        return f"<Question(id={self.id}, theme={self.theme})>"


class Response(Base):
    __tablename__ = 'responses'

    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('players.id'), nullable=False)
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('questions.id'), nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Score for this specific response
    score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    llm_feedback: Mapped[str] = mapped_column(Text, nullable=True)
    liked: Mapped[bool] = mapped_column(Boolean, nullable=True)
    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('player_id', 'question_id'),
    )

    # Relationships
    player = relationship("Player", back_populates="responses")
    question = relationship("Question", back_populates="responses")

    def __repr__(self):
        return f"<Response(player_id={self.player_id}, question_id={self.question_id}, score={self.score})>"


@event.listens_for(Response, "after_insert")
def update_player_score(mapper, connection, target):
    # target = the Response instance object
    connection.execute(
        Player.__table__.update().
        where(Player.id == target.player_id).
        values(score=Player.score + target.score)
    )
