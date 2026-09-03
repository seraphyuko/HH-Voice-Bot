import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve path to token.env
env_path = Path(__file__).resolve().parent / 'token.env'
load_dotenv(dotenv_path=env_path)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing in token.env!")