import os

from dotenv import load_dotenv


load_dotenv()

PLAYWRIGHT_WS_ENDPOINT = f"ws://localhost:{os.getenv('PLAYWRIGHT_WS_PORT', '3000')}"
