"""
POST /api/render_video — Accept a finalized script and run the full pipeline.
"""
import re
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

from server.services.pipeline import run_pipeline
from server.services.jobs import create_job, update_job, get_job

router = APIRouter()

class SceneInput(BaseModel):
    id: int
    duration: int = 5
    character: str = "zundamon"
    narration: str = ""
    sound_effect: str = ""
    visual_query: str = ""
    image_prompt_en: str = ""
    overlay_text: str = ""


class RenderRequest(BaseModel):
    title: str
    bgm_keyword: str = "lofi"
    scenes: List[SceneInput]
    engine: str = "gtts"


class SourceInfo(BaseModel):
    scene_id: int
    query: str
    provider: str
    photographer: str
    source_url: str


class RenderResponse(BaseModel):
    job_id: str
    status: str
    message: str


def _render_task(job_id: str, script_data: dict, engine: str):
    """Background task to run the video pipeline."""
    try:
        update_job(job_id, status="processing", message="Starting pipeline...", progress=0)
        result = run_pipeline(script_data, engine=engine, job_id=job_id)
        update_job(job_id, status="completed", message="Video rendered successfully.", result=result, progress=100)
    except Exception as e:
        update_job(job_id, status="failed", message=str(e))
        print(f"Job {job_id} failed: {e}")


@router.post("/render_video", response_model=RenderResponse)
async def render_video(req: RenderRequest, background_tasks: BackgroundTasks):
    """確定済み台本を受け取り、非同期で素材収集→ナレーション→動画生成を実行（ジョブIDを即時返却）"""
    try:
        script_data = {
            "title": req.title,
            "bgm_keyword": req.bgm_keyword,
            "scenes": [s.model_dump() for s in req.scenes],
        }
        job_id = create_job()
        background_tasks.add_task(_render_task, job_id, script_data, req.engine)
        
        return RenderResponse(
            job_id=job_id,
            status="pending",
            message="Job started in background."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/render_status/{job_id}")
async def get_render_status(job_id: str):
    """ジョブの現在のステータスを返す（ポーリング用）"""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
