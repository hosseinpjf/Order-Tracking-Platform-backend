from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.db.session import get_db
from app.services.jwt_bearer import get_payload, get_optional_payload
from app.middleware.exception_handler import response_handler
from app.models.site_content import SiteContent, SiteContentType
from app.schemas.site_content import CreateSiteContent, OutSiteContent
from app.utils.delete_file import delete_file, delete_files
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
