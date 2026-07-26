from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_, and_, not_
from datetime import datetime, timezone
import math
import logging
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.models.message import Message
from app.models.user import User, UserRole
from app.middleware.exception_handler import response_handler
from app.utils.get_site_info import get_working_hours, get_settings
from app.routers.message_ws import manager

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/message", tags=["Message"])


@router.get("/chats")
async def get_message_users(
    payload = Depends(get_payload),
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        admin_ids = {
            admin_id
            for (admin_id,) in db.query(User.id).filter(User.role == UserRole.admin).all()
        }

        if not admin_ids:
            logger.warning("No admin users found while fetching chats list, admin_id=%s", payload["sub"])
            return response_handler(
                status=True,
                message="All chats fetched",
                data={
                    "users": [],
                    "count": 0,
                    "page": page,
                    "page_size": limit,
                },
                status_code=200,
            )

        users = {
            user_id
            for (user_id,) in db.query(
                case((
                        Message.sender_id.in_(admin_ids),
                        Message.receiver_id
                    ),
                    else_=Message.sender_id
                )
            )
            .filter(or_(
                and_(Message.sender_id.in_(admin_ids), not_(Message.receiver_id.in_(admin_ids))),
                and_(Message.receiver_id.in_(admin_ids), not_(Message.sender_id.in_(admin_ids))),
            ))
            .distinct()
            .all()
        }

        users = list(users)

        results = []
        users_map = {}
        last_messages = {}
        unread_counts = {}
        
        if users:

            users_map = {
                user.id: user
                for user in db.query(User).filter(User.id.in_(users)).all()
            }

            partner_expr = case((Message.sender_id.in_(admin_ids), Message.receiver_id), else_=Message.sender_id,)

            ranked_subq = (
                db.query(
                    Message.id.label("message_id"),
                    partner_expr.label("partner_id"),
                    func.row_number().over(
                        partition_by=partner_expr,
                        order_by=Message.created_at.desc(),
                    ).label("rn"),
                )
                .filter(
                    or_(
                        and_(Message.sender_id.in_(users), Message.receiver_id.in_(admin_ids)),
                        and_(Message.receiver_id.in_(users), Message.sender_id.in_(admin_ids)),
                    ),
                )
                .subquery()
            )

            ranked_rows = (
                db.query(ranked_subq.c.message_id, ranked_subq.c.partner_id)
                .filter(ranked_subq.c.rn == 1)
                .all()
            )

            if ranked_rows:
                message_id_to_partner = {row.message_id: row.partner_id for row in ranked_rows}
                messages_by_id = {
                    m.id: m
                    for m in db.query(Message).filter(Message.id.in_(message_id_to_partner.keys())).all()
                }
                for message_id, partner_id in message_id_to_partner.items():
                    msg = messages_by_id.get(message_id)
                    if msg:
                        last_messages[partner_id] = msg

                db_unread_counts = (
                    db.query(
                        Message.sender_id,
                        func.count(Message.id),
                    )
                    .filter(
                        Message.sender_id.in_(users),
                        Message.receiver_id.in_(admin_ids),
                        Message.is_read == False,
                    )
                    .group_by(Message.sender_id)
                    .all()
                )
                unread_counts = {
                    sender_id: count
                    for sender_id, count in db_unread_counts
                }


        for user_id in users:

            user = users_map.get(user_id)
            if not user: continue

            last_message = last_messages.get(user_id)

            unread_count = unread_counts.get(user_id, 0)

            is_online = manager.is_online(user_id)

            sort_time = None
            last_message_data = None

            if last_message:
                sort_time = last_message.created_at

                last_message_data = {
                    "id": last_message.id,
                    "content": last_message.content,
                    "sender_id": last_message.sender_id,
                    "created_at": last_message.created_at.isoformat(),
                }

            results.append({
                "user_id": user_id,
                "user_name": user.name,
                "user_phone": user.phone,
                "last_message": last_message_data,
                "unread_count": unread_count,
                "is_online": is_online,
                "_sort": sort_time,
            })

        results.sort(
            key=lambda x: x["_sort"] or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True
        )
        for item in results:
            item.pop("_sort")

        total_count = len(results)
        start = (page - 1) * limit
        end = start + limit
        paginated_results = results[start:end]

        return response_handler(
            status=True,
            message="All chats fetched",
            data={
                "users": paginated_results,
                "total": total_count,
                "page": page,
                "limit": limit,
                "pages": math.ceil(total_count / limit)
            },
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        logger.exception("Failed to get chats. Admin ID: %s", payload["sub"])
        raise HTTPException(status_code=500, detail="Get chats failed")


@router.get("/messages/{user_id}")
async def get_messages_for_admin(
    user_id: str,
    payload = Depends(get_payload),
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        admin_ids = {
            admin_id
            for (admin_id,) in db.query(User.id).filter(User.role == UserRole.admin).all()
        }
        if not admin_ids:
            raise HTTPException(status_code=404, detail="No admin found")

        partner = db.query(User).filter(User.id == user_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="User not found")

        query = db.query(Message).filter(
            or_(
                and_(Message.sender_id.in_(admin_ids), Message.receiver_id == user_id),
                and_(Message.receiver_id.in_(admin_ids), Message.sender_id == user_id),
            )
        )

        total = query.count()

        messages = query.order_by(Message.created_at.asc()).offset((page - 1) * limit).limit(limit).all()

        reply_ids = {
            message.reply_to_message_id
            for message in messages
            if message.reply_to_message_id
        }

        reply_map = {}

        if reply_ids:

            reply_map = {
                message.id: message
                for message in db.query(Message).filter(Message.id.in_(reply_ids)).all()
            }

        results = []

        for message in messages:

            reply = reply_map.get(message.reply_to_message_id)

            reply_data = None

            if reply:
                reply_data = {
                    "id": reply.id,
                    "content": reply.content,
                    "sender_id": reply.sender_id,
                    "receiver_id": reply.receiver_id,
                    "created_at": reply.created_at.isoformat(),
                }

            results.append({
                "id": message.id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "content": message.content,

                "reply": reply_data,

                "is_read": message.is_read,
                "is_delivered": message.is_delivered,

                "created_at": message.created_at.isoformat(),
            })

        return response_handler(
            status=True,
            message="Messages fetched successfully",
            data={
                "messages": results,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": math.ceil(total / limit),
            },
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        logger.exception("Failed to fetch messages. admin_id=%s user_id=%s", payload["sub"], user_id)
        raise HTTPException(status_code=500, detail="Get messages failed")


