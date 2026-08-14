from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.api.v1.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import PropertyStatus
from app.models.messaging import Conversation, Message
from app.models.property import Property
from app.models.user import User
from app.schemas.messaging import (
    ConversationCreate,
    ConversationRead,
    MessageCreate,
    MessageRead,
    UnreadCountsRead,
)

router = APIRouter(prefix="/conversations", tags=["messaging"])


def _conv_options():
    return (
        joinedload(Conversation.buyer),
        joinedload(Conversation.seller),
        joinedload(Conversation.property).joinedload(Property.media),
        selectinload(Conversation.messages),
    )


async def _get_conversation(db: AsyncSession, conversation_id: uuid.UUID):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(*_conv_options())
    )
    return result.unique().scalar_one_or_none()


def _is_participant(conversation: Conversation, user: User) -> bool:
    return conversation.buyer_id == user.id or conversation.seller_id == user.id


def _conversation_read(
    conversation: Conversation, current_user_id: uuid.UUID
) -> ConversationRead:
    unread = sum(
        1
        for m in conversation.messages
        if not m.is_read and m.sender_id != current_user_id
    )
    last = conversation.messages[-1] if conversation.messages else None
    return ConversationRead(
        id=conversation.id,
        property_id=conversation.property_id,
        buyer_id=conversation.buyer_id,
        seller_id=conversation.seller_id,
        last_message_at=conversation.last_message_at,
        buyer_archived=conversation.buyer_archived,
        seller_archived=conversation.seller_archived,
        buyer_blocked=conversation.buyer_blocked,
        seller_blocked=conversation.seller_blocked,
        created_at=conversation.created_at,
        buyer=conversation.buyer,
        seller=conversation.seller,
        property_title=(conversation.property.title if conversation.property else None),
        property_cover=(
            conversation.property.media[0].url
            if conversation.property and conversation.property.media
            else None
        ),
        unread_count=unread,
        last_message=last.content if last else None,
    )


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ConversationRead]:
    me_id = current_user.id
    result = await db.execute(
        select(Conversation)
        .options(*_conv_options())
        .where(
            or_(
                (Conversation.buyer_id == me_id)
                & (Conversation.buyer_archived.is_(False)),
                (Conversation.seller_id == me_id)
                & (Conversation.seller_archived.is_(False)),
            )
        )
        .order_by(Conversation.last_message_at.desc().nullslast())
        .offset(offset)
        .limit(limit)
    )
    conversations = result.scalars().unique().all()
    return [
        _conversation_read(c, me_id)
        for c in conversations
        if _is_participant(c, current_user)
    ]


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def start_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationRead:
    property = await db.get(Property, payload.property_id)
    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    if property.status not in (
        PropertyStatus.ACTIVE.value,
        PropertyStatus.SOLD.value,
        PropertyStatus.RENTED.value,
    ):
        raise HTTPException(status_code=400, detail="Property is not contactable")
    if property.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message your own listing")

    # Reuse an existing conversation between the same buyer/seller/property
    existing = await db.execute(
        select(Conversation)
        .options(*_conv_options())
        .where(
            Conversation.property_id == property.id,
            Conversation.buyer_id == current_user.id,
            Conversation.seller_id == property.owner_id,
        )
    )
    conversation = existing.scalar_one_or_none()
    if conversation is None:
        conversation = Conversation(
            property_id=property.id,
            buyer_id=current_user.id,
            seller_id=property.owner_id,
        )
    db.add(conversation)
    await db.flush()

    # Mark the message as read for the sender, unread for the recipient
    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=payload.message.strip(),
        is_read=False,  # Default to unread for all users; will be updated per-user on fetch
    )

    db.add(message)
    await db.flush()
    conversation.last_message_at = message.created_at
    await db.commit()

    conversation = await _get_conversation(db, conversation.id)
    return _conversation_read(conversation, current_user.id)


@router.get("/unread-count", response_model=UnreadCountsRead)
async def unread_counts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UnreadCountsRead:
    me_id = current_user.id

    # Count unread messages for the current user
    total = (
        await db.execute(
            select(func.count(Message.id))
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(
                Message.is_read.is_(False),
                or_(
                    (Conversation.buyer_id == me_id)
                    & (Conversation.buyer_archived.is_(False)),
                    (Conversation.seller_id == me_id)
                    & (Conversation.seller_archived.is_(False)),
                ),
            )
        )
    ).scalar() or 0

    # Count conversations with unread messages
    conversations = (
        await db.execute(
            select(func.count(func.distinct(Message.conversation_id)))
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(
                Message.is_read.is_(False),
                or_(
                    (Conversation.buyer_id == me_id)
                    & (Conversation.buyer_archived.is_(False)),
                    (Conversation.seller_id == me_id)
                    & (Conversation.seller_archived.is_(False)),
                ),
            )
        )
    ).scalar() or 0

    return UnreadCountsRead(total=total, conversations=conversations)


@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationRead:
    conversation = await _get_conversation(db, conversation_id)
    if conversation is None or not _is_participant(conversation, current_user):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _conversation_read(conversation, current_user.id)


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[MessageRead]:
    conversation = await _get_conversation(db, conversation_id)
    if conversation is None or not _is_participant(conversation, current_user):
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Mark all unread messages in the conversation as read for the current user
    result = await db.execute(
        select(Message).where(
            Message.conversation_id == conversation_id,
            Message.is_read.is_(False),
        )
    )
    for message in result.scalars().all():
        message.is_read = True
    await db.commit()

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    messages = result.scalars().all()
    return list(reversed(messages))


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: uuid.UUID,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageRead:
    conversation = await _get_conversation(db, conversation_id)
    if conversation is None or not _is_participant(conversation, current_user):
        raise HTTPException(status_code=404, detail="Conversation not found")

    other_id = (
        conversation.seller_id
        if conversation.buyer_id == current_user.id
        else conversation.buyer_id
    )
    blocked = (
        conversation.buyer_blocked
        if conversation.seller_id == other_id
        else conversation.seller_blocked
    )
    if blocked:
        raise HTTPException(
            status_code=403, detail="You are blocked in this conversation"
        )

    message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        content=payload.content.strip(),
        is_read=False,  # Ensure the message is marked as unread for the recipient
    )

    db.add(message)
    await db.flush()
    conversation.last_message_at = message.created_at
    conversation.buyer_archived = False
    conversation.seller_archived = False
    await db.commit()
    await db.refresh(message)
    return message


@router.patch(
    "/{conversation_id}/archive",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def archive_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    conversation = await _get_conversation(db, conversation_id)
    if conversation is None or not _is_participant(conversation, current_user):
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.buyer_id == current_user.id:
        conversation.buyer_archived = True
    else:
        conversation.seller_archived = True
    await db.commit()


@router.patch(
    "/{conversation_id}/block",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def block_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    conversation = await _get_conversation(db, conversation_id)
    if conversation is None or not _is_participant(conversation, current_user):
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.buyer_id == current_user.id:
        conversation.buyer_blocked = True
    else:
        conversation.seller_blocked = True
    await db.commit()


@router.delete(
    "/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    conversation = await _get_conversation(db, conversation_id)
    if conversation is None or not _is_participant(conversation, current_user):
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.messages:
        raise HTTPException(
            status_code=400,
            detail="Use archive to hide a conversation with messages",
        )
    await db.delete(conversation)
    await db.commit()
