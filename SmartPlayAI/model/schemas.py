# This allow us to config the database, how data is validated and serialzied for API requests and response using pydantics
from datetime import datetime, timezone
from pydantic import BaseModel, AwareDatetime, Field, ConfigDict
from typing import List, Optional

# Player Schemas
# Create, update for sending json data to api
# out for receiving data from api as ORM object , not just dict so we can return the model object instance directly from the endpoint


class PlayerBase(BaseModel):
    name: str
    score: Optional[int] = 0
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    disabled: bool = False


class PlayerCreate(PlayerBase):
    """Schema for creating a new player"""
    pass


class PlayerUpdate(BaseModel):
    """Schema for updating player information"""
    score: Optional[int] = None
    username: Optional[str] = None
    disabled: Optional[bool] = None


class PlayerOut(PlayerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PlayerInDB(PlayerBase):
    """Player schema for database operations"""
    password_hash: str

# Question Schemas


class QuestionBase(BaseModel):
    theme: str
    question_text: str


class QuestionCreate(QuestionBase):
    """Schema for creating a new question"""
    pass


class QuestionOut(QuestionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ListQuestionsOut(BaseModel):
    questions: List[QuestionOut]
    user_id: int
    model_config = ConfigDict(from_attributes=True)

# Response Schemas


class ResponseBase(BaseModel):
    player_id: int
    question_id: int
    response_text: str
    score: Optional[int] = 0
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


class ResponseCreate(ResponseBase):
    """Schema for creating a new response"""
    pass


class ResponseOut(ResponseBase):
    model_config = ConfigDict(from_attributes=True)


# Helper schemas

class PlayerWithResponses(PlayerOut):
    """Player schema including their responses"""
    responses: list[ResponseOut] = []
