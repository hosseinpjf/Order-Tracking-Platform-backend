from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.middleware.exception_handler import response_handler
from app.models.site_content import SiteContent, SiteContentType


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/site-content/kpi")
def get_site_content_summary(payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        summary = (
            db.query(
                func.count(SiteContent.id).label("total_contents"),
                func.sum(
                    case(
                        (SiteContent.is_visible == True, 1),
                        else_=0,
                    )
                ).label("visible_contents"),
                func.sum(
                    case(
                        (SiteContent.is_visible == False, 1),
                        else_=0,
                    )
                ).label("hidden_contents"),
            )
            .first()
        )

        content_types = (
            db.query(
                SiteContent.type,
                func.count(SiteContent.id).label("count"),
            )
            .group_by(SiteContent.type)
            .all()
        )

        type_counts = {
            content_type.value: 0
            for content_type in SiteContentType
        }

        for item in content_types:
            type_counts[item.type.value] = item.count

        return response_handler(
            status=True,
            message="Get site content KPI report successful",
            data={
                "total_contents": summary.total_contents or 0,
                "visible_contents": summary.visible_contents or 0,
                "hidden_contents": summary.hidden_contents or 0,
                "content_types": type_counts,
            },
            status_code=200,
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Get site content KPI report failed")

