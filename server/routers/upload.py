from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pathlib import Path
import shutil
from server.services.pipeline import slugify

router = APIRouter()

WORKSPACE = Path("workspace/projects")

@router.post("/upload_image")
async def upload_image(
    title: str = Form(...),
    scene_id: int = Form(...),
    file: UploadFile = File(...)
):
    """
    手動アップロードされた画像を受け取り、対応するプロジェクトのassetsフォルダに保存する。
    """
    try:
        slug = slugify(title)
        project_dir = WORKSPACE / slug
        assets_dir = project_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        ext = Path(file.filename).suffix if file.filename else ".jpg"
        # frontend will expect this specific pattern later, or can just use the returned URL
        filename = f"scene_{scene_id:02d}_manual{ext}"
        filepath = assets_dir / filename
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "status": "success",
            "url": f"/outputs/{slug}/assets/{filename}",
            "scene_id": scene_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")
