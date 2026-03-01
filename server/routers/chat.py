"""
POST /api/chat — Free-form conversation with Gemini for brainstorming ideas.
"""
import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# ── Gemini setup ──
_api_key = os.getenv("GEMINI_API_KEY", "")
if _api_key:
    genai.configure(api_key=_api_key)
_model = genai.GenerativeModel("gemini-flash-latest")


class ChatMessage(BaseModel):
    role: str            # "user" or "model"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    system_prompt: str = (
        "あなたはYouTubeショート動画の企画アシスタントです。"
        "ユーザーと一緒に「名著×ネットミーム」で面白い動画企画を考えます。"
        "日本語で回答してください。"
    )


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Gemini との自由対話（壁打ち）"""
    try:
        chat_session = _model.start_chat(history=[
            {"role": m.role, "parts": [m.content]}
            for m in req.messages[:-1]
        ])
        last_msg = req.messages[-1].content if req.messages else ""
        response = chat_session.send_message(last_msg)
        return ChatResponse(reply=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
