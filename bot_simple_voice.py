import os
import io
import logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from gtts import gTTS

# Load environment variables
env_path = Path(__file__).resolve().parent / 'token.env'
load_dotenv(dotenv_path=env_path)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN in token.env!")

# Initialize Gemini Client with API key
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! ကျွန်တော် HH-Voice-Bot ပါ။\n"
        "စာသား သို့မဟုတ် ဝတ္ထုအခန်းများ ပို့ပေးပါ။ အသံဖိုင်အဖြစ် ပြောင်းပေးပါမည်။"
    )

async def handle_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text("အသံဖိုင် ဖန်တီးနေပါသည်...")

    try:
        # Use gemini-3.6-flash to clean up text if client is available
        clean_text = text
        if client:
            try:
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=f"Clean and format this Myanmar text into smooth, continuous sentences for reading out loud:\n\n{text}"
                )
                if response.text:
                    clean_text = response.text
            except Exception as ge:
                logging.warning(f"Gemini processing skipped: {ge}")

        # Convert clean text to speech via gTTS (Myanmar language)
        tts = gTTS(text=clean_text, lang='my')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        audio_bytes.name = "voice.ogg"

        await update.message.reply_voice(voice=audio_bytes)

    except Exception as e:
        await update.message.reply_text(f"Error generating audio: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tts))

    print("HH-Voice-Bot is running with gemini-3.6-flash + gTTS...")
    app.run_polling()