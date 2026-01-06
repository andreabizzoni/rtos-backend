from pydantic import BaseModel, Field
from typing import Optional


class DateTimeData(BaseModel):
    dateTime: str = Field(..., description="Time formatted according to ISO: YYYY-MM-DD HH:MM:SS.")
    timeZone: str = Field(default="UTC", description="Timezone code.")


class CalendarEvent(BaseModel):
    id: Optional[str] = Field(default=None, description="The unique identifier of the event.")
    status: Optional[str] = Field(default=None, description="The status of the event.")
    summary: str = Field(..., description="The title of the event.")
    start: DateTimeData = Field(..., description="The event start time.")
    end: DateTimeData = Field(..., description="The event end time.")
    description: Optional[str] = Field(default=None, description="A description of the event.")
    location: Optional[str] = Field(default=None, description="The location of the event.")


class CalendarTimeWindow(BaseModel):
    start: str = Field(..., description="The start of the calendar time window.")
    end: str = Field(..., description="The end of the calendar time window.")
