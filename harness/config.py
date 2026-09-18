import os
from dotenv import load_dotenv
load_dotenv()
BASE_URL = os.environ.get("QWEN_BASE_URL", "http://localhost:8000/v1")
API_KEY = os.environ.get("QWEN_API_KEY", "none")
MODEL = os.environ.get("QWEN_MODEL", "qwen3.8-27b")
SANDBOX_IMAGE = os.environ.get("SANDBOX_IMAGE", "qwen-sandbox:latest")
