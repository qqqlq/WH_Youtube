import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

# Define Output Schema
class Scene(BaseModel):
    id: int = Field(..., description="Sequential ID of the scene")
    duration: int = Field(..., description="Duration of the scene in seconds (usually 3-5s)")
    narration: str = Field(..., description="Voiceover narration text for this scene (Japanese)")
    visual_query: str = Field(..., description="Specific English search query to find a stock photo/video for this scene")
    overlay_text: str = Field(..., description="Short, punchy text to display on screen (Japanese)")

class VideoScript(BaseModel):
    title: str = Field(..., description="Title of the YouTube Short")
    scenes: List[Scene]

class PlannerAgent:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables.")
        
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

    def generate_script(self, topic: str) -> dict:
        """
        Generates a 60-second video script for the given topic.
        """
        print(f"Planning video for topic: {topic}...")
        
        prompt = f"""
        You are a professional video planner for YouTube Shorts.
        Create a compelling, educational, and high-retention 60-second video script about: "{topic}".
        
        Requirements:
        1. **Total Duration:** Must be approx 60 seconds.
        2. **Structure:** Divide into scenes (approx 3-5 seconds each, total ~10-15 scenes).
        3. **Visuals:** 'visual_query' must be a specific English search term for stock photos (e.g., "glacier calving close up 4k wallpaper").
        4. **Narration:** Engaging, informative, and coherent (Japanese).
        5. **Overlay:** Short, impactful keywords (Japanese).
        
        Output must be valid JSON matching the schema:
        {{
            "title": "str",
            "scenes": [
                {{
                    "id": int,
                    "duration": int,
                    "narration": "str",
                    "visual_query": "str",
                    "overlay_text": "str"
                }}
            ]
        }}
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=VideoScript,
                ),
            )
            # Parse JSON
            script_data = json.loads(response.text)
            return script_data
        except Exception as e:
            print(f"Error generating script: {e}")
            raise

if __name__ == "__main__":
    # Test execution
    try:
        planner = PlannerAgent()
        script = planner.generate_script("Los Glaciares National Park (Patagonia)")
        print(json.dumps(script, indent=2, ensure_ascii=False))
        
        # Save validation file
        with open("workspace/inputs/test_script.json", "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Test failed: {e}")
