import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

history = [
    types.Content(role="user", parts=[types.Part.from_text(text="こんにちは！")]),
    types.Content(role="model", parts=[types.Part.from_text(text="こんにちは、お手伝いします！")])
]

chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction="You are a helpful assistant.",
    ),
    history=history
)

response = chat.send_message("私はさっきなんて言った？")
print(response.text)
