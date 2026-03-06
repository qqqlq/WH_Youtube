"""
POST /api/render_video — Accept a finalized script and run the full pipeline.
"""
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from server.services.pipeline import run_pipeline

router = APIRouter()


class SceneInput(BaseModel):
    id: int
    duration: int = 5
    narration: str = ""
    visual_query: str = ""
    overlay_text: str = ""


class RenderRequest(BaseModel):
    title: str
    scenes: List[SceneInput]
    engine: str = "gtts"


class SourceInfo(BaseModel):
    scene_id: int
    query: str
    provider: str
    photographer: str
    source_url: str


class RenderResponse(BaseModel):
    status: str
    video_url: str
    project_slug: str
    sources: List[SourceInfo]


@router.post("/render_video", response_model=RenderResponse)
async def render_video(req: RenderRequest):
    """確定済み台本を受け取り、素材収集→ナレーション→動画生成を一括実行"""
    try:
        script_data = {
            "title": req.title,
            "scenes": [s.model_dump() for s in req.scenes],
        }
        result = run_pipeline(script_data, engine=req.engine)
        return RenderResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
