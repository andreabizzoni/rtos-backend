from pydantic import BaseModel, Field
from typing import Optional


class DateTimeData(BaseModel):
    dateTime: str = Field(
        ..., description="Time formatted according to ISO: YYYY-MM-DD HH:MM:SS."
    )
    timeZone: str = Field(default="UTC", description="Timezone code.")


class CalendarEvent(BaseModel):
    summary: str = Field(..., description="The title of the event.")
    start: DateTimeData = Field(..., description="The event start time.")
    end: DateTimeData = Field(..., description="The event end time.")
    description: str = Field(..., description="A description of the event.")
    location: Optional[str] = Field(
        default="", description="The location of the event."
    )


class CalendarEventResponse(CalendarEvent):
    id: str = Field(..., description="Event identifier in the calendar.")
    htmlLink: str = Field(..., description="Link to the event in Google Calendar.")
    status: str = Field(..., description="The response status.")


class CalendarEventToolCall(BaseModel):
    summary: str
    start: str
    end: str
    description: str
    location: Optional[str] = None
