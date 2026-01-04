from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# from datetime import datetime, timedelta
import os.path
import pickle
from .models.calendar_models import (
    CalendarEventToolCall,
    CalendarEvent,
    CalendarEventResponse,
    DateTimeData,
)
from .config.settings import settings


class CalendarClient:
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        token_file = os.path.join(module_dir, "token.pickle")

        if os.path.exists(token_file):
            with open(token_file, "rb") as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    settings.get_google_credentials_dict(),
                    ["https://www.googleapis.com/auth/calendar"],
                )
                self.creds = flow.run_local_server(port=0)

            with open(token_file, "wb") as token:
                pickle.dump(self.creds, token)

        self.service = build("calendar", "v3", credentials=self.creds)

    def create_event(self, event: CalendarEventToolCall) -> CalendarEventResponse:
        if self.service is None:
            raise Exception(
                "Failed to create calendar event: Google Calendar service not initialized."
            )
        try:
            request_body = CalendarEvent(
                summary=event.summary,
                start=DateTimeData(
                    dateTime=event.start,
                ),
                end=DateTimeData(
                    dateTime=event.end,
                ),
                description=event.description,
                location=event.location,
            )
            response = (
                self.service.events()
                .insert(
                    calendarId=settings.email_address,
                    body=request_body.model_dump(),
                )
                .execute()
            )
            return CalendarEventResponse.model_validate(obj=response, extra="ignore")

        except Exception as e:
            raise Exception(f"Failed to create calendar event: {e}") from e
