import os
import sys
import json
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from google import genai
from google.genai import types

class Scene(BaseModel):
    id: int = Field(..., description="Sequential ID of the scene")
    duration: int = Field(..., description="Duration of the scene in seconds (usually 3-5s)")
    narration: str = Field(..., description="Voiceover narration text for this scene (Japanese)")
    visual_query: str = Field(..., description="Specific English search query to find a stock photo/video for this scene")
    overlay_text: str = Field(..., description="Short, punchy text to display on screen (Japanese)")

class VideoScript(BaseModel):
    title: str = Field(..., description="Title of the YouTube Short")
    scenes: List[Scene]

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

prompt = "Create a 10s video script about Mt. Fuji. Just 2 scenes."

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=VideoScript,
    ),
)
print("Raw text:")
print(response.text)
script_data = json.loads(response.text)
print("Parsed JSON:")
print(json.dumps(script_data, indent=2, ensure_ascii=False))
