from typing import Any


def create_event_tool() -> dict[str, Any]:
    return {
        "type": "function",
        "name": "create_calendar_event",
        "description": "Create an event in the user's calendar. Use this when you need to schedule something in the user's calendar.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "The title of the event.",
                },
                "start": {
                    "type": "object",
                    "properties": {
                        "dateTime": {
                            "type": "string",
                            "description": "The event start time in RFC3339 format: YYYY-MM-DDTHH:MM:SSZ. If not provided by the user, estimate based on the type of activity being scheduled.",
                        },
                    },
                    "required": ["dateTime"],
                    "additionalProperties": False,
                },
                "end": {
                    "type": "object",
                    "properties": {
                        "dateTime": {
                            "type": "string",
                            "description": "The event end time in RFC3339 format: YYYY-MM-DDTHH:MM:SSZ. If not provided by the user, estimate based on the type of activity being scheduled.",
                        },
                    },
                    "required": ["dateTime"],
                    "additionalProperties": False,
                },
                "description": {
                    "type": ["string", "null"],
                    "description": "A brief description of the event.",
                },
                "location": {
                    "type": ["string", "null"],
                    "description": "The location of the event. If it is not explicitly provided by the user or you are unable to confidently guess it from the conversation, leave blank.",
                },
            },
            "required": ["summary", "start", "end", "description", "location"],
            "additionalProperties": False,
        },
    }


def read_calendar_tool() -> dict[str, Any]:
    return {
        "type": "function",
        "name": "read_calendar",
        "description": "Read the user's calendar to see what events are scheduled within a time window [start, end]. Use this when you need visibility over the user's calendar.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "start": {
                    "type": "string",
                    "description": "The start of the time window you want to view in RFC3339 format: YYYY-MM-DDTHH:MM:SSZ.",
                },
                "end": {
                    "type": "string",
                    "description": "The end of the time window you want to view in RFC3339 format: YYYY-MM-DDTHH:MM:SSZ.",
                },
            },
            "required": ["start", "end"],
            "additionalProperties": False,
        },
    }


def update_event_tool() -> dict[str, Any]:
    return {
        "type": "function",
        "name": "update_calendar_event",
        "description": "Update an event in the user's calendar. Use this when you need to update one or more fields of an event. Keep the unedited fields the same as the original event.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "The id of the event that needs to be updated.",
                },
                "summary": {
                    "type": "string",
                    "description": "The title of the event.",
                },
                "start": {
                    "type": "object",
                    "properties": {
                        "dateTime": {
                            "type": "string",
                            "description": "The event start time in RFC3339 format: YYYY-MM-DDTHH:MM:SSZ. If not provided by the user, estimate based on the type of activity being scheduled.",
                        },
                    },
                    "required": ["dateTime"],
                    "additionalProperties": False,
                },
                "end": {
                    "type": "object",
                    "properties": {
                        "dateTime": {
                            "type": "string",
                            "description": "The event end time in RFC3339 format: YYYY-MM-DDTHH:MM:SSZ. If not provided by the user, estimate based on the type of activity being scheduled.",
                        },
                    },
                    "required": ["dateTime"],
                    "additionalProperties": False,
                },
                "description": {
                    "type": ["string", "null"],
                    "description": "A brief description of the event.",
                },
                "location": {
                    "type": ["string", "null"],
                    "description": "The location of the event. If it is not explicitly provided by the user or you are unable to confidently guess it from the conversation, leave blank.",
                },
            },
            "required": ["id", "summary", "start", "end", "description", "location"],
            "additionalProperties": False,
        },
    }
