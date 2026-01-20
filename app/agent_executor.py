import logging

from uuid import uuid4
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Role, TaskState, Message, Part, TextPart, DataPart, FilePart, FileWithBytes
from a2a.utils import new_task

from .agent import Agent
from .models.stream_models import AudioChunk, TextChunk, ToolCallEvent
from .utils.enums import Mode

logger = logging.getLogger(__name__)


class Executor(AgentExecutor):
    def __init__(self):
        self.agent = Agent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        mode = context.metadata.get("mode", Mode.TEXT.value)
        task = context.current_task

        if not context.message:
            raise Exception("No message provided")

        if not task:
            task = new_task(context.message)
            logger.info(f"Created new task: {task.id}")
            await event_queue.enqueue_event(task)
        else:
            logger.info(f"Continuing existing task: {task.id}")

        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            stream = self.agent.stream_speech(query) if mode == Mode.SPEECH.value else self.agent.stream_text(query)

            async for event in stream:
                if isinstance(event, ToolCallEvent):
                    logger.info(f"Streaming tool call event: {event.name}")
                    await updater.update_status(
                        TaskState.working,
                        Message(
                            message_id=uuid4().hex,
                            context_id=task.context_id,
                            task_id=task.id,
                            role=Role.agent,
                            parts=[Part(root=DataPart(data={"type": "tool_call", "name": event.name}))],
                        ),
                    )
                elif isinstance(event, TextChunk):
                    logger.info(f"Streaming text chunk: {len(event.text)} chars")
                    await updater.update_status(
                        TaskState.working,
                        Message(
                            message_id=uuid4().hex,
                            context_id=task.context_id,
                            task_id=task.id,
                            role=Role.agent,
                            parts=[Part(root=TextPart(text=event.text))],
                        ),
                    )
                elif isinstance(event, AudioChunk):
                    logger.info(f"Streaming audio chunk: {len(event.data)} base64 chars")
                    await updater.update_status(
                        TaskState.working,
                        Message(
                            message_id=uuid4().hex,
                            context_id=task.context_id,
                            task_id=task.id,
                            role=Role.agent,
                            parts=[
                                Part(
                                    root=FilePart(
                                        file=FileWithBytes(
                                            bytes=event.data,
                                            mime_type=event.mime_type,
                                        )
                                    )
                                )
                            ],
                        ),
                    )

            logger.info(f"Task {task.id} completed successfully")
            await updater.complete()

        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}", exc_info=True)
            await updater.update_status(
                TaskState.failed,
                Message(
                    message_id=uuid4().hex,
                    context_id=task.context_id,
                    task_id=task.id,
                    role=Role.agent,
                    parts=[Part(root=TextPart(text=f"Error: {e}"))],
                ),
                final=True,
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Cancel not supported")
