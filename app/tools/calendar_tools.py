def create_event_tool() -> dict:
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
                    "type": "string",
                    "description": "The event start time in RFC3339 format: YYYY-MM-DDTHH:MM:SSZ. If not provided by the user, estimate based on the type of activity being scheduled.",
                },
                "end": {
                    "type": "string",
                    "description": "The event end time in RFC3339 format: YYYY-MM-DDTHH:MM:SSZ. If not provided by the user, estimate based on the type of activity being scheduled.",
                },
                "description": {
                    "type": "string",
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
