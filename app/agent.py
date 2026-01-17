import logging
from datetime import datetime
from typing import AsyncIterator

from langfuse import observe, Langfuse
from openai import OpenAI, AsyncOpenAI

from .calendar_client import CalendarClient
from .config.settings import settings
from .models.calendar_models import CalendarEvent, CalendarTimeWindow
from .models.stream_models import TextChunk, ToolCallEvent, StreamEvent
from .tools.calendar_tools import create_event_tool, read_calendar_tool, update_event_tool
from .tools.web_search_tools import web_search_tool

logger = logging.getLogger(__name__)

SPEECH = "speech"
TEXT = "text"


class Agent:
    def __init__(self, model: str = "gpt-4.1"):
        self.model = model
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.async_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.langfuse = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            base_url=settings.langfuse_base_url,
        )
        self.context = [
            {
                "role": "system",
                "content": f"""You are an AI assistant named Rtos (pronounced art-ohs), 
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

            logger.warning(f"Unknown tool requested: {name}")
            return f"tool {name} does not exist."

        except Exception as e:
            logger.error(f"Tool call to {name} failed: {e}", exc_info=True)
            return f"Tool call to {name} failed. Either try a different tool or tell the user you are unable to complete their request right now."

    @observe(as_type="generation", capture_input=False, capture_output=False)
    def chat(self, query: str) -> str:
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

    async def stream(self, query: str, mode: str) -> AsyncIterator[StreamEvent]:
        logger.info(f"Answering in {mode} mode the query: {query[:20]}...")
        if mode == SPEECH:
            self.context[0] = {
                "role": "system",
                "content": f"""You are an AI assistant named Rtos (pronounced art-ohs), 
                be ready to answer the user's questions or perform actions via the tools you have available. 
                Today's date and current time are: {datetime.now()}. You are responding via speech mode. This means that your
                answers will be spoken out loud. Because of this, make sure that your answer emulates spoken language.
                Avoid using written elements that you would not find in spoken language (like emojis or urls), and that all acroyms are written out 
                in plain language instead.
                """,
            }

        self.context.append({"role": "user", "content": query})

        turns = 0

        while turns < self.max_turns:
            stream = await self.async_client.responses.create(
                model=self.model,
                input=self.context,  # type: ignore[arg-type]
                tools=self.tools,  # type: ignore[arg-type]
                stream=True,
            )

            response = None
            async for event in stream:
                if event.type == "response.output_text.delta":
                    if mode == TEXT:
                        yield TextChunk(text=event.delta)
                elif event.type == "response.completed":
                    response = event.response

            if response and response.output_text:
                if mode == SPEECH:
                    yield TextChunk(text=response.output_text)

                logger.info(f"chat_stream completed with text response (turn {turns + 1})")
                self.context.append({"role": "assistant", "content": response.output_text})
                return

            if response:
                self.context += response.output
                for tool_call in response.output:
                    if tool_call.type == "function_call":
                        logger.info(f"Calling tool: {tool_call.name}")
                        yield ToolCallEvent(name=tool_call.name)
                        result = self.call_function(tool_call.name, tool_call.arguments)
                        self.context.append(
                            {
                                "type": "function_call_output",
                                "call_id": tool_call.call_id,
                                "output": result,
                            }
                        )

            turns += 1

        logger.warning(f"chat_stream reached max turns ({self.max_turns})")
        raise Exception("Agent reached maximum turns without completing")
