from openai import OpenAI
from .config.settings import settings
from langfuse import observe, Langfuse

from .calendar_client import CalendarClient
from .models.calendar_models import CalendarEventToolCall
from .tools.calendar_tools import create_event_tool


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
                "content": "You are a helpful assistant, ready to answer the user or perform actions via the tools you have available",
            }
        ]
        self.calendar_client = CalendarClient()
        self.tools = [create_event_tool()]
        self.max_turns = 5

    def call_function(self, name: str, args: str) -> str:
        if name == "create_calendar_event":
            try:
                validated_tool_call = CalendarEventToolCall.model_validate_json(args)
                return self.calendar_client.create_event(
                    validated_tool_call
                ).model_dump_json(indent=2)
            except Exception as e:
                print(f"Tool call to {name} failed: {e}")
                return f"Tool call to {name} failed. Either try a different tool or tell the user you are unable to complete their request right now."
        return f"tool {name} does not exist. Either try a different tool or tell the user you are unable to complete their request right now."

    @observe(as_type="generation", capture_input=False, capture_output=False)
    def answer(self, query: str) -> str:
        self.context.append({"role": "user", "content": query})

        turns = 0
        while turns < self.max_turns:
            response = self.client.responses.create(
                model=self.model,
                input=self.context,
                tools=self.tools,
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
