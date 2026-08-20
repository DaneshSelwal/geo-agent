import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEE_PROJECT_ID = os.getenv("GEE_PROJECT_ID")