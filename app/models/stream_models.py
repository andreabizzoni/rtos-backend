from pydantic import BaseModel
from typing import Union


class TextChunk(BaseModel):
    text: str


class ToolCallEvent(BaseModel):
    name: str


StreamEvent = Union[TextChunk, ToolCallEvent]
