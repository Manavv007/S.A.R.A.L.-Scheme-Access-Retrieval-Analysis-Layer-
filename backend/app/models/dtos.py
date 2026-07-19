"""
Data Transfer Objects (DTOs) for the chat API endpoints.
"""

from typing import Optional
from pydantic import BaseModel


class UserProfile(BaseModel):
    """Demographic profile used for personalised scheme matching."""
    age: int
    occupation: str          # e.g. Farmer, Student, Business
    state: str
    income: str              # e.g. "2.5 Lakh"
    caste: Optional[str] = None
    language: str = "English"


class ChatRequest(BaseModel):
    """Incoming chat request from the frontend."""
    query: str
    history: list = []
    profile: UserProfile | None = None


class ChatResponse(BaseModel):
    """Outgoing chat response to the frontend."""
    answer: str
    source_docs: list = []


class TTSRequest(BaseModel):
    """Text-to-speech synthesis request."""
    text: str
    language: str = "English"


class ConverseRequest(BaseModel):
    """A single turn in the live voice conversation."""
    message: str = ""
    profile: dict = {}
    history: list = []
    phase: str = "greet"
    language: str = "English"


class ConverseResponse(BaseModel):
    """The assistant's reply plus updated dialogue state."""
    reply: str
    profile: dict
    phase: str
    done: bool = False
    schemes: list = []
