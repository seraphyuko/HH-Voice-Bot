import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

import config
import keyboards
import tts_engine
import database  # Import the new database module

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name

    # Load credits from database
    data = database.load_data()
    user_credits = data.get(user_id, {}).get("credits", 5)

    caption_text = (
        f"👋 မင်္ဂလာပါ, {user_name}\n"
        f"💳 လက်ကျန် Credit - {user_credits}\n"
    )
    reply_markup = keyboards.get_main_menu_keyboard()
    await update.message.reply_text(caption_text, reply_markup=reply_markup)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    # Handle daily credit button click
    if query.data == "btn_daily_credit":
        success, message, current_balance = database.claim_daily_credit(user_id)
        await query.message.reply_text(message, parse_mode="Markdown")

    elif query.data == "btn_tts":
        await query.message.reply_text("ကျေးဇူးပြု၍ အသံပြောင်းလိုသော စာသားကို ပို့ပေးပါ။")
    else:
        await query.message.reply_text(f"You selected option: {query.data}")

async def text_to_speech_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    # Check and deduct 1 credit
    success, error_msg, remaining = database.deduct_credit(user_id, cost=1)
    if not success:
        await update.message.reply_text(error_msg, parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text("အသံဖိုင် ဖန်တီးနေပါသည်...")

    try:
        audio_stream = tts_engine.generate_myanmar_speech(text)
        
        # Send voice note with remaining credit info
        await update.message.reply_voice(
            voice=audio_stream,
            caption=f"✅ အသံဖိုင် ဖန်တီးပြီးပါပြီ။\n💳 သင့်လက်ကျန် Credit: **{remaining}**",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Error generating audio: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech_handler))

    print("HH-Voice-Bot is running...")
    app.run_polling()