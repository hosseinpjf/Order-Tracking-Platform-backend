from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List
import uuid
import os
import aiofiles
from PIL import Image
from io import BytesIO
from app.middleware.exception_handler import response_handler
from app.services.jwt_bearer import get_payload
from app.config.settings import settings
from app.utils.delete_file import cleanup, delete_file


router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/images/{folder_name}")
async def upload_images(folder_name: str, files: List[UploadFile] = File(...), positions: List[str] = Form(...), payload = Depends(get_payload)):
    saved_paths = []
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        if folder_name not in settings.ALLOWED_FOLDERS:
            raise HTTPException(400, "Invalid folder")
        IMAGE_REPOSITORY: str = os.path.join("media", "uploads", folder_name)

        if not files:
            raise HTTPException(status_code=400, detail="At least one file is required")
        
        if len(files) != len(positions):
            raise HTTPException(status_code=400, detail="Files and positions length mismatch")

        os.makedirs(IMAGE_REPOSITORY, exist_ok=True)

        results = []
        for file, position in zip(files, positions):

            if file.content_type not in settings.ALLOWED_CONTENT_TYPES:
                raise HTTPException(status_code=400, detail="Only image files are allowed")
            
            file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if file_ext not in settings.ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=400, detail="Invalid file extension")
            
            content = await file.read()

            if len(content) > settings.MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="File too large (max 5MB)")
            
            try: 
                with Image.open(BytesIO(content)) as img: img.verify()
            except Exception: raise HTTPException(status_code=400, detail="Invalid image file")

            file_name = f"{uuid.uuid4().hex}.{file_ext}"
            file_path = os.path.join(IMAGE_REPOSITORY, file_name)
            
            async with aiofiles.open(file_path, "wb") as buffer:
                await buffer.write(content)

            saved_paths.append(file_path)

            results.append({
                "url": f"/{IMAGE_REPOSITORY}/{file_name}",
                "position": position
            })

        return response_handler(
            status = True,
            message="Images uploaded successfully",
            data=results,
            status_code=201
        )
    except HTTPException:
        cleanup(saved_paths)
        raise
    except Exception:
        cleanup(saved_paths)
        raise HTTPException(status_code=500, detail="Images upload failed")


