from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle
from .models.calendar_models import CalendarEvent, CalendarTimeWindow
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

    def create_event(self, event: CalendarEvent) -> CalendarEvent:
        if self.service is None:
            raise Exception("Failed to create calendar event: Google Calendar service not initialized.")
        try:
            response = (
                self.service.events()
                .insert(
                    calendarId=settings.email_address,
                    body=event.model_dump(exclude={"status"}),
                )
                .execute()
            )
            return CalendarEvent.model_validate(obj=response, extra="ignore")

        except Exception as e:
            raise Exception(f"Failed to create calendar event: {e}") from e

    def update_event(self, event: CalendarEvent) -> CalendarEvent:
        if self.service is None:
            raise Exception("Failed to update calendar event: Google Calendar service not initialized.")
        try:
            response = (
                self.service.events()
                .update(
                    calendarId=settings.email_address,
                    eventId=event.id,
                    body=event.model_dump(exclude={"status", "id"}),
                )
                .execute()
            )
            return CalendarEvent.model_validate(obj=response, extra="ignore")

        except Exception as e:
            raise Exception(f"Failed to update calendar event: {e}") from e

    def read_calendar(self, time_window: CalendarTimeWindow) -> list[CalendarEvent]:
        if self.service is None:
            raise Exception("Failed to read calendar: Google Calendar service not initialized.")
        try:
            events = (
                self.service.events()
                .list(
                    calendarId=settings.email_address,
                    timeMin=time_window.start,
                    timeMax=time_window.end,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return [CalendarEvent.model_validate(obj=event, extra="ignore") for event in events["items"]]
        except Exception as e:
            raise Exception(f"Failed to read calendar: {e}") from e
