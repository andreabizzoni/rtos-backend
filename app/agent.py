from openai import OpenAI
from .config.settings import settings
from langfuse import observe, Langfuse
from datetime import datetime

from .calendar_client import CalendarClient
from .models.calendar_models import CalendarEvent, CalendarTimeWindow
from .tools.calendar_tools import create_event_tool, read_calendar_tool, update_event_tool
from .tools.web_search_tools import web_search_tool


class Agent:
    def __init__(self, model: str = "gpt-4.1"):
        self.model = model
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.langfuse = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            base_url=settings.langfuse_base_url,
        )
        self.context = [
            {
                "role": "system",
                "content": f"""You are a helpful AI assistant named Guido, 
                be ready to answer the user's questions or perform actions via the tools you have available. 
                Today's date and current time are: {datetime.now()}.""",
            }
        ]
        self.calendar_client = CalendarClient()
        self.tools = [create_event_tool(), read_calendar_tool(), update_event_tool(), web_search_tool()]
        self.max_turns = 5

    def call_function(self, name: str, args: str) -> str:
        try:
            if name == "read_calendar":
                validated_args = CalendarTimeWindow.model_validate_json(args)
                events = self.calendar_client.read_calendar(validated_args)
                return "\n".join([event.model_dump_json(indent=2) for event in events])

            if name == "create_calendar_event":
                validated_args = CalendarEvent.model_validate_json(args)
                return self.calendar_client.create_event(validated_args).model_dump_json(indent=2)

            if name == "update_calendar_event":
                validated_args = CalendarEvent.model_validate_json(args)
                return self.calendar_client.update_event(validated_args).model_dump_json(indent=2)

            return f"tool {name} does not exist."

        except Exception as e:
            print(f"Tool call to {name} failed: {e}")
            return f"Tool call to {name} failed. Either try a different tool or tell the user you are unable to complete their request right now."

    @observe(as_type="generation", capture_input=False, capture_output=False)
    def answer(self, query: str) -> str:
        self.context.append({"role": "user", "content": query})

        turns = 0
        while turns < self.max_turns:
            response = self.client.responses.create(
                model=self.model,
                input=self.context,  # type: ignore[arg-type]
                tools=self.tools,  # type: ignore[arg-type]
            )

            self.langfuse.update_current_generation(
                input=self.context,
                output=response.output,
                usage_details={
                    "input": getattr(response.usage, "input_tokens", 0),
                    "output": getattr(response.usage, "output_tokens", 0),
                },
            )

            if response.output_text:
                output_text = response.output_text
                self.context.append({"role": "assistant", "content": output_text})
                return output_text

            self.context += response.output
            for tool_call in response.output:
                if tool_call.type != "function_call":
                    continue

                name = tool_call.name
                args = tool_call.arguments
                result = self.call_function(name, args)
                self.context.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": result,
                    }
                )

            turns += 1

        return "Oops! Looks like I got stuck in an infinite loop, my head is starting to spin."
