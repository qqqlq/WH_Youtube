"""
POST /api/generate_script — Generate a video script JSON from topic + context.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from agents.planner import PlannerAgent

router = APIRouter()


class ScriptRequest(BaseModel):
    topic: str
    context: Optional[str] = ""  # Chat history summary for extra context


class ScriptResponse(BaseModel):
    title: str
    scenes: list


@router.post("/generate_script", response_model=ScriptResponse)
async def generate_script(req: ScriptRequest):
    """チャットコンテキストを元に台本 JSON を生成"""
    try:
        planner = PlannerAgent()

        # If context is provided, prepend it to the topic for richer generation
        effective_topic = req.topic
        if req.context:
            effective_topic = f"{req.topic}\n\n補足コンテキスト:\n{req.context}"

        script = planner.generate_script(effective_topic)
        return ScriptResponse(
            title=script.get("title", req.topic),
            scenes=script.get("scenes", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
