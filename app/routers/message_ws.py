from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import logging
from app.db.session import SessionLocal
from app.services.tokens import verify_token
from app.models.message import Message
from app.models.device_tracking import DeviceTracking
from app.models.user import User
from app.websockets.message_manager import MessageConnectionManager


router = APIRouter()
manager = MessageConnectionManager()
logger = logging.getLogger("websockets.messages")

@router.websocket("/ws/messages")
async def websocket_messages(websocket: WebSocket):

    # ----------------------------<< Verification Authorization >>----------------------------
    # 1) Get Token
    token = websocket.cookies.get("access_token")

    if not token:
        await websocket.close(code=4401)  # Unauthorized
        return

    # 2) Verify Token
    payload = verify_token(token)
    if payload is None:
        await websocket.close(code=4401)
        return

    user_id: str = payload.get("sub")
    device_id: str = payload.get("device_id")
    access_version: int = payload.get("access_version")

    if not user_id or not device_id or access_version is None:
        await websocket.close(code=4401)
        return

    # 3) Device validation
    def _get_device():
        db = SessionLocal()

        try:
            return db.query(DeviceTracking).filter(
                DeviceTracking.device_id == device_id,
                DeviceTracking.access_version == access_version,
            ).first()
        finally:
            db.close()

    db_device = await asyncio.to_thread(_get_device)

    # ----------------------------<< Create a channel >>----------------------------
    # 1) Connection in ConnectionManager
    await manager.connect(user_id, db_device.id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("event", "send_message")

            # ----------------------------<< Message sending operation >>----------------------------
            if event_type == "send_message":

                receiver_id = data.get("receiver_id")
                content = data.get("content")
                reply_to_message_id = data.get("reply_to_message_id")

                content = content.strip()

                # 1) Validating input data
                if not receiver_id or not content or not content:
                    await websocket.send_json({"event": "error", "message": "receiver_id and non-empty content are required"})
                    continue

                if receiver_id == user_id:
                    await websocket.send_json({"event": "error", "message": "you cannot send message to yourself"})
                    continue

                if not isinstance(content, str):
                    await websocket.send_json({"event": "error", "message": "content must be a string"})
                    continue
    
                if len(content) > 5000:
                    await websocket.send_json({"event": "error", "message": "content exceeds maximum length of 5000 characters"})
                    continue

                if reply_to_message_id is not None and not isinstance(reply_to_message_id, str):
                    await websocket.send_json({"event": "error", "message": "reply_to_message_id must be a string"})
                    continue

                if not isinstance(receiver_id, str):
                    await websocket.send_json({"event": "error", "message": "receiver_id must be a string"})
                    continue

                # 2) Checking for the existence of the receiver and reply_to_message_id.
                def _validate():
                    db = SessionLocal()
                    try:
                        if not db.query(User.id).filter(User.id == receiver_id).first():
                            return "receiver not found"

                        if reply_to_message_id:
                            reply_message = db.query(Message).filter(Message.id == reply_to_message_id).first()

                            if not reply_message:
                                return "reply_to_message_id not found"

                            if not (
                                (reply_message.sender_id == user_id and reply_message.receiver_id == receiver_id)
                                or
                                (reply_message.sender_id == receiver_id and reply_message.receiver_id == user_id)
                            ):
                                return "reply_to_message_id does not belong to this conversation"

                            return None
                    finally:
                        db.close()

                validation_error = await asyncio.to_thread(_validate)
                if validation_error:
                    await websocket.send_json({"event": "error", "message": validation_error})
                    continue

                # 3) Marking as "delivered" (If at least one receiver device was online)
                receiver_online = manager.is_online(receiver_id)

                # 4) Save to database
                def _save():
                    db = SessionLocal()
                    try:
                        db_message = Message(
                            sender_id = user_id,
                            receiver_id = receiver_id,
                            content = content,
                            reply_to_message_id = reply_to_message_id,
                            is_delivered = receiver_online,
                            is_read = False,
                        )
                        db.add(db_message)
                        db.commit()
                        db.refresh(db_message)
                        return db_message

                    finally:
                        db.close()

                db_message = await asyncio.to_thread(_save)

                # ---
                message_payload = {
                    "id": db_message.id,
                    "sender_id": user_id,
                    "receiver_id": receiver_id,
                    "content": db_message.content,
                    "reply_to_message_id": db_message.reply_to_message_id,
                    "created_at": db_message.created_at.isoformat(),
                    "is_delivered": db_message.is_delivered,
                }

                # 5) Send message to receiver
                await manager.send_to_user(receiver_id, {
                    "event": "new_message",
                    "message": message_payload
                })

                # 6) Send message to sender
                await manager.send_to_user(user_id, {
                    "event": "sent",
                    "message": message_payload
                })

            # ----------------------------<< Message reading operation >>----------------------------
            elif event_type == "mark_read":
                message_id = data.get("message_id")

                def _mark_read():
                    db = SessionLocal()
                    try:
                        msg = db.query(Message).filter(
                            Message.id == message_id,
                            Message.receiver_id == user_id,
                        ).first()
                        if msg and not msg.is_read:
                            msg.is_read = True
                            db.commit()
                        return msg
                    finally:
                        db.close()

                msg = await asyncio.to_thread(_mark_read)
                if msg:
                    await manager.send_to_user(msg.sender_id, {
                        "event": "read_receipt",
                        "message_id": msg.id,
                    })

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("unexpected error in websocket connection for user %s", user_id)
    finally:
        await manager.disconnect(user_id, db_device.id)