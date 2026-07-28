from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sgc_db.models.agent_meta import Conversation, Message, ToolInvocation


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_conversation(
        self, session_id: str, customer_id: str | None, context: dict
    ) -> Conversation:
        conv = Conversation(
            session_id=session_id,
            customer_id=customer_id,
            context_snapshot=context,
        )
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

    async def get_conversation(self, session_id: str) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def add_message(
        self, session_id: str, role: str, content: str, source_refs: list | None = None
    ) -> Message:
        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            source_refs=source_refs or [],
        )
        self.session.add(msg)
        await self.session.commit()
        return msg

    async def get_messages(self, session_id: str, limit: int = 50) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def log_tool_invocation(
        self,
        session_id: str,
        tool_name: str,
        input_payload: dict,
        output_payload: dict,
        success: bool,
    ) -> ToolInvocation:
        inv = ToolInvocation(
            session_id=session_id,
            tool_name=tool_name,
            input_payload=input_payload,
            output_payload=output_payload,
            success=success,
        )
        self.session.add(inv)
        await self.session.commit()
        return inv
