from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.orm.attributes import flag_modified
import uuid
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.middleware.exception_handler import response_handler
from app.models.site_info import SiteInfo
from app.schemas.site_info import CreateSiteInfo


router = APIRouter(prefix="/info", tags=["Site Info"])

FIELDS_WITH_ID = ["slogans", "phones", "links", "working_hours", "settings"]
FIELDS_WITH_ID_CHILDREN = ["hero", "footer", "about_us", "contact_us"]
@router.post("/")
def create_info(data: CreateSiteInfo, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db_site_info = db.query(SiteInfo).first()
        if not db_site_info:
            db_site_info = SiteInfo()
            db.add(db_site_info)
            db.flush()

        create_data = data.model_dump(
            mode="json",
            exclude_unset=True,
            exclude_none=True
        )

        for key, value in create_data.items():

            if key in FIELDS_WITH_ID:
                prev_data = list(getattr(db_site_info, key) or [])
                
                for item in value:
                    item["id"] = uuid.uuid4().hex

                    if key in ("slogans", "phones", "links"):
                        item.setdefault("is_visible", True)

                    if key == "working_hours":
                        item.setdefault("is_closed", False)
                
                    prev_data.append(item)

                value = prev_data

            if key in FIELDS_WITH_ID_CHILDREN:
                prev_data = dict(getattr(db_site_info, key) or {})

                for key_item, value_item in value.items():

                    if key_item in ("images", "buttons"):
                        prev_item = prev_data.get(key_item, [])

                        for item in value_item:
                            item["id"] = uuid.uuid4().hex
                            prev_item.append(item)

                        prev_data[key_item] = prev_item

                    else:
                        prev_data[key_item] = value_item

                value = prev_data
                
            setattr(db_site_info, key, value)
            flag_modified(db_site_info, key)

        db.commit()
        db.refresh(db_site_info)

        return response_handler(
            status=True,
            message="Data created successfully",
            data={},
            status_code=200
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Site info create failed")

