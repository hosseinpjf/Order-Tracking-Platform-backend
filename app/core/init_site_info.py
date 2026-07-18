from sqlalchemy.orm import Session
import uuid
from app.models.site_info import SiteInfo, SiteInfoSettings
from sqlalchemy.orm.attributes import flag_modified

def init_site_info(db: Session):
    try:
        site_info = db.query(SiteInfo).first()

        if not site_info:
            site_info = SiteInfo(settings=[])
            db.add(site_info)
            db.flush()

        current_settings = list(site_info.settings or []) # database
        valid_capabilities = {setting.value for setting in SiteInfoSettings} # base list
        existing_capabilities = {s["capability"] for s in current_settings}

        changed = False

        for setting in SiteInfoSettings:
            if setting.value not in existing_capabilities:
                current_settings.append({
                    "id": uuid.uuid4().hex,
                    "capability": setting.value,
                    "enabled": True
                })
                changed = True

        filtered_settings = [
            s for s in current_settings if s["capability"] in valid_capabilities
        ]
        if len(filtered_settings) != len(current_settings):
            current_settings = filtered_settings
            changed = True

        if changed:
            site_info.settings = current_settings
            flag_modified(site_info, "settings")

        db.commit()

    except Exception:
        db.rollback()
        raise