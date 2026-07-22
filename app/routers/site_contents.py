from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import or_, String
from app.db.session import get_db
from app.services.jwt_bearer import get_payload, get_optional_payload
from app.middleware.exception_handler import response_handler
from app.models.site_content import SiteContent, SiteContentType, SiteContentSort
from app.schemas.site_content import CreateSiteContent, OutSiteContent, UpdateSiteContent
from app.utils.delete_file import delete_files
from app.utils.get_site_info import get_settings


router = APIRouter(prefix="/contents", tags=["Site Contents"])


@router.post("/{content_type}")
def create_contents(content_type: SiteContentType, data: CreateSiteContent, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        create_data = data.model_dump(
            mode="json",
            exclude_unset=True,
            exclude_none=True
        )

        new_content = SiteContent(type = content_type)

        for key, value in create_data.items():
            setattr(new_content, key, value)

        db.add(new_content)
        db.commit()
        db.refresh(new_content)

        return response_handler(
            status=True,
            message="Content created successfully",
            data=OutSiteContent.model_validate(new_content).model_dump(),
            status_code=201
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Site content create failed")


@router.patch("/{content_id}")
def update_content(content_id: str, data: UpdateSiteContent, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db_site_content = db.query(SiteContent).filter(SiteContent.id == content_id).first()
        if not db_site_content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        old_files = set()
        new_files = set()

        update_data = data.model_dump(
            mode="json",
            exclude_unset=True,
            exclude_none=True
        )

        for field in ("images", "icons"):
            if field in update_data:
                old_files.update(item["url"] for item in (getattr(db_site_content, field) or []) if item.get("url"))
                new_files.update(item["url"] for item in update_data[field] if item.get("url"))

        for key, value in update_data.items():
            setattr(db_site_content, key, value)

        for field in ("images", "icons", "buttons", "content"):
            if field in update_data:
                flag_modified(db_site_content, field)

        db.commit()
        db.refresh(db_site_content)

        delete_files_list = list(old_files - new_files)
        if delete_files_list:
            delete_files(delete_files_list)

        return response_handler(
            status=True,
            message="Content updated successfully",
            data=OutSiteContent.model_validate(db_site_content).model_dump(),
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Site content update failed")


@router.get("/")
def get_content(
    payload = Depends(get_optional_payload),
    db: Session = Depends(get_db),
    content_type: list[SiteContentType] | None = Query(None),
    q: str | None = Query(None),
    is_visible: bool | None = Query(None),
    sort: SiteContentSort | None = Query(None)
):
    try:
        is_admin = bool(payload) and payload.get("role") == "admin"

        db_site_content = []
        query = db.query(SiteContent)

        if not is_admin:
            db_settings = get_settings(db, [
                "show_statistics",
                "show_announcements",
                "show_banners",
                "show_gallery",
                "show_facilities",
                "show_services",
                "show_features",
                "show_faqs",
                "show_team_members",
            ])
            allowed_types = [
                content_type_item
                for content_type_item in SiteContentType
                if db_settings[f"show_{content_type_item.value}"]
            ]
            query = query.filter(
                SiteContent.type.in_(allowed_types),
                SiteContent.is_visible.is_(True),
            )

        if content_type:
            query =  query.filter(SiteContent.type.in_(content_type))

        if is_admin:
            if q:
                search = f"%{q}%"
                query = query.filter(or_(
                    SiteContent.title.ilike(search), 
                    SiteContent.subtitle.ilike(search), 
                    SiteContent.content.cast(String).ilike(search)
                ))
            if is_visible is not None:
                query = query.filter(SiteContent.is_visible == is_visible)

        if sort == SiteContentSort.created_at_desc:
            query = query.order_by(SiteContent.created_at.desc())
        elif sort == SiteContentSort.created_at_asc:
            query = query.order_by(SiteContent.created_at.asc())
        elif sort == SiteContentSort.updated_at_desc:
            query = query.order_by(SiteContent.updated_at.desc())
        elif sort == SiteContentSort.updated_at_asc:
            query = query.order_by(SiteContent.updated_at.asc())
        elif sort == SiteContentSort.order_desc:
            query = query.order_by(SiteContent.type.asc(), SiteContent.order.desc())
        elif sort == SiteContentSort.order_asc:
            query = query.order_by(SiteContent.type.asc(), SiteContent.order.asc())
        else:
            query = query.order_by(SiteContent.type.asc(), SiteContent.order.desc())

        db_contents_total = query.count()
        db_site_content = query.all()

        return response_handler(
            status=True,
            message="Content get successfully",
            data={
                "site_contents": [
                    OutSiteContent.model_validate(content).model_dump()
                    for content in db_site_content
                ],
                "total": db_contents_total
            },
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Site content get failed")


@router.delete("/{content_id}")
def delete_content(content_id: str, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db_site_content = db.query(SiteContent).filter(SiteContent.id == content_id).first()
        if not db_site_content:
            raise HTTPException(status_code=404, detail="Content not found")

        old_files = set()

        for field in ("images", "icons"):
            if hasattr(db_site_content, field):
                old_files.update(item["url"] for item in (getattr(db_site_content, field) or []) if item.get("url"))

        db.delete(db_site_content)
        db.commit()

        if old_files:
            delete_files(list(old_files))

        return response_handler(
            status=True,
            message="Content deleted successfully",
            data=None,
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Site content delete failed")

