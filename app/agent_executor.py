from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from .agent import Agent


class Executor(AgentExecutor):
    def __init__(self):
        self.agent = Agent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        result = self.agent.chat(context.get_user_input())
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")
