from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.orm.attributes import flag_modified
import uuid
from app.db.session import get_db
from app.services.jwt_bearer import get_payload, get_optional_payload
from app.middleware.exception_handler import response_handler
from app.models.site_info import SiteInfo, SiteInfoPart
from app.schemas.site_info import CreateSiteInfo, UpdateSiteInfo
from app.utils.site_info_update import update_list, update_section
from app.utils.delete_file import delete_file, delete_files


router = APIRouter(prefix="/info", tags=["Site Info"])

FIELDS_WITH_LIST_DATA = ["slogans", "phones", "links", "working_hours", "settings", "today_suggestions"]
FIELDS_WITH_DICT_DATA = ["hero", "footer", "about_us", "contact_us"]
FIELDS_WITH_SIMPLE_DATA = ["name", "logo", "address", "table_reservation_time", "location"]

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

        old_image = None

        for key, value in create_data.items():

            if key in FIELDS_WITH_SIMPLE_DATA:
                if key == "logo" and value and db_site_info.logo and value != db_site_info.logo:
                    old_image = db_site_info.logo
                    
                setattr(db_site_info, key, value)
                continue

            if key in FIELDS_WITH_LIST_DATA:
                current_value = list(getattr(db_site_info, key) or [])

                for item in value:
                    item["id"] = uuid.uuid4().hex
                    if key in ("slogans", "phones", "links", "today_suggestions"):
                        item.setdefault("is_visible", True)
                    current_value.append(item)

                setattr(db_site_info, key, current_value)
                flag_modified(db_site_info, key)
                continue

            if key in FIELDS_WITH_DICT_DATA:
                current_section = dict(getattr(db_site_info, key) or {})

                for section_key, section_value in value.items():
                    if section_key in ("images", "buttons"):
                        current_items = current_section.get(section_key, [])

                        for item in section_value:
                            item["id"] = uuid.uuid4().hex
                            current_items.append(item)

                        current_section[section_key] = current_items
                    else:
                        current_section[section_key] = section_value

                setattr(db_site_info, key, current_section)
                flag_modified(db_site_info, key)
                continue

        db.commit()
        db.refresh(db_site_info)

        if old_image:
            delete_file(old_image)

        return response_handler(
            status=True,
            message="Data created successfully",
            data=None,
            status_code=201
        )
    except HTTPException as http_error:
        db.rollback()
        raise http_error
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Site info create failed")


@router.patch("/")
def update_info(data: UpdateSiteInfo, payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        db_site_info = db.query(SiteInfo).first()
        if not db_site_info:
            raise HTTPException(status_code=404, detail="Site info not found")

        update_data = data.model_dump(
            mode="json",
            exclude_unset=True,
            exclude_none=True,
        )

        old_images = set()

        for key, value in update_data.items():

            if key in FIELDS_WITH_SIMPLE_DATA:
                if key == "logo" and value and db_site_info.logo and value != db_site_info.logo:
                    old_images.add(db_site_info.logo)

                setattr(db_site_info, key, value)
                continue

            if key in FIELDS_WITH_LIST_DATA:
                current_value = getattr(db_site_info, key) or []

                is_image = False
                if key == "links": is_image = True

                setattr(db_site_info, key, update_list(is_image, current_value, value, old_images))
                flag_modified(db_site_info, key)
                continue

            if key in FIELDS_WITH_DICT_DATA:
                current_section = getattr(db_site_info, key) or {}
                setattr(db_site_info, key, update_section(current_section, value, old_images))
                flag_modified(db_site_info, key)
                continue

        db.commit()
        db.refresh(db_site_info)

        if old_images:
            delete_files(list(old_images))

        return response_handler(
            status=True,
            message="Data updated successfully",
            data=None,
            status_code=200
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Site info update failed")


@router.get("/")
def get_info(
    db: Session = Depends(get_db),
    payload = Depends(get_optional_payload),
    parts: list[SiteInfoPart] = Query(default=[SiteInfoPart.all])
):
    try:
        is_admin = bool(payload) and payload.get("role") == "admin"

        db_site_info = db.query(SiteInfo).first()
        if not db_site_info:
            raise HTTPException(status_code=404, detail="Site info not found")
        
        if SiteInfoPart.all in parts:
            parts = [
                *(SiteInfoPart(field) for field in FIELDS_WITH_SIMPLE_DATA),
                *(SiteInfoPart(field) for field in FIELDS_WITH_LIST_DATA),
                *(SiteInfoPart(field) for field in FIELDS_WITH_DICT_DATA),
            ]

        data_output = {}
        for part in parts:

            if part.value in FIELDS_WITH_SIMPLE_DATA:
                data_output[part.value] = getattr(db_site_info, part.value)

            elif part.value in FIELDS_WITH_LIST_DATA:
                items = getattr(db_site_info, part.value) or []
                if not is_admin:
                    items = [item for item in items if item.get("is_visible", True)]
                data_output[part.value] = items

            elif part.value in FIELDS_WITH_DICT_DATA:
                section = (getattr(db_site_info, part.value) or {}).copy()
                if not is_admin:
                    if "buttons" in section:
                        section["buttons"] = [button for button in section["buttons"] if button.get("is_visible", True)]
                data_output[part.value] = section

        return response_handler(
            status=True,
            message="Site info get successfully",
            data=data_output,
            status_code=200
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Site info get failed")

