from pydantic import BaseModel
from typing import Union


class TextChunk(BaseModel):
    text: str


class ToolCallEvent(BaseModel):
    name: str


class AudioChunk(BaseModel):
    data: str  # base64-encoded audio bytes
    mime_type: str = "audio/mpeg"


StreamEvent = Union[TextChunk, ToolCallEvent, AudioChunk]
