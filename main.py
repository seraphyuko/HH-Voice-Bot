import logging
import io
import asyncio
from PIL import Image
import easyocr

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
import engine
import database
import re

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Replace with your actual numeric ID from @userinfobot (e.g., "584920182")
ADMIN_ID = "6373962597"

# Initialize OCR reader (supports English & numbers)
reader = easyocr.Reader(['en'], gpu=False)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name

    # Fetch user credit balance from database
    data = database.load_data()
    user_credits = data.get(user_id, {}).get("credits", 5)

    caption_text = (
        f"👋 မင်္ဂလာပါ, {user_name}\n"
        f"💳 လက်ကျန် Credit - {user_credits}\n"
    )
    reply_markup = keyboards.get_main_menu_keyboard()
    await update.message.reply_text(caption_text, reply_markup=reply_markup)

async def check_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /balance and /credit commands."""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name

    data = database.load_data()
    user_credits = data.get(user_id, {}).get("credits", 5)

    balance_msg = (
        f"👤 <b>{user_name}</b> ၏ အကောင့်အချက်အလက်\n\n"
        f"🆔 User ID: <code>{user_id}</code>\n"
        f"💳 လက်ကျန် Credit: <b>{user_credits}</b> Credits"
    )
    await update.message.reply_text(balance_msg, parse_mode="HTML")

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline menu button selections."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data == "btn_daily_credit":
        success, message, current_balance = database.claim_daily_credit(user_id)
        await query.message.reply_text(message, parse_mode="Markdown")

    elif query.data == "btn_topup":
        # Fetch live user balance
        data = database.load_data()
        user_credits = data.get(user_id, {}).get("credits", 5)

        topup_msg = (
            f"💳 <b>သင့် လက်ရှိ လက်ကျန် Credit:</b> {user_credits}\n"
            f"🆔 <b>သင့် User ID:</b> <code>{user_id}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "<b>၁။ ငွေပေးချေနိုင်သော ဘဏ်အကောင့်များ:</b>\n"
            "• <b>K PLUS / KBANK:</b> 123-4-56789-0\n"
            "• <b>KPay / Wave:</b> 09123456789\n\n"
            "<b>၂။ ဈေးနှုန်းများ:</b>\n"
            "• 10 Credits - 1,000 MMK / 15 THB\n"
            "• 50 Credits - 4,500 MMK / 70 THB\n\n"
            "<b>၃။ Credit ရယူရန်:</b>\n"
            "ငွေလွှဲပြီးပါက ပြေစာ (Screenshot) နှင့် သင့် User ID ကို Admin ထံ ပေးပို့ပေးပါရန်။\n\n"
            "📩 Admin Direct Contact: @hnin_nns"
        )
        await query.message.reply_text(topup_msg, parse_mode="HTML")

    elif query.data == "btn_lang_en":
        msg = "🌐 **Language set to English!**\n\nAll future responses and voice synthesis will default to English."
        await query.message.reply_text(msg, parse_mode="Markdown")

    elif query.data == "btn_tts":
        # Send the inline keyboard menu to choose between Classic or Voice Clone
        await query.message.reply_text(
            "🎙️ <b>စာသားမှအသံ Engine အမျိုးအစား ရွေးချယ်ပါ:</b>",
            reply_markup=keyboards.get_engine_keyboard(),
            parse_mode="HTML"
        )

    elif query.data == "btn_tts_classic":
        context.user_data["selected_engine"] = "classic"
        await query.message.reply_text(
            "🎙️ <b>Classic TTS (Standard) ကို ရွေးချယ်ထားပါသည်။</b>\n\n"
            "ကျေးဇူးပြု၍ အသံပြောင်းလိုသော စာသားကို ပို့ပေးပါ (ကျသင့်ငွေ: 1 Credit)။",
            parse_mode="HTML"
        )

    elif query.data == "btn_tts_clone":
        context.user_data["selected_engine"] = "clone"
        await query.message.reply_text(
            "✨ <b>TTS (Voice Clone) Beta ကို ရွေးချယ်ထားပါသည်။</b>\n\n"
            "ကျေးဇူးပြု၍ အသံပြောင်းလိုသော စာသားကို ပို့ပေးပါ (ကျသင့်ငွေ: 3 Credits)။",
            parse_mode="HTML"
        )

    elif query.data == "btn_main_menu":
        user_name = query.from_user.first_name
        data = database.load_data()
        user_credits = data.get(user_id, {}).get("credits", 5)

        caption_text = (
            f"👋 မင်္ဂလာပါ, {user_name}\n"
            f"💳 လက်ကျန် Credit - {user_credits}\n"
        )
        await query.message.reply_text(
            caption_text,
            reply_markup=keyboards.get_main_menu_keyboard()
        )

    else:
        await query.message.reply_text(f"You selected option: {query.data}")


async def photo_receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles payment receipt photos using regex parsing and duplicate prevention."""
    user_id = str(update.effective_user.id)
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    status_msg = await update.message.reply_text(
        "⏳ <b>ငွေလွှဲပြေစာကို လက်ခံရရှိပါသည်။</b>\n\n"
        "စနစ်မှ ဘဏ်စာရင်းဝင်ရောက်မှုကို စစ်ဆေးနေပါသဖြင့် ခဏစောင့်ဆိုင်းပေးပါရန်...",
        parse_mode="HTML"
    )

    try:
        # Run EasyOCR in a separate thread to prevent blocking the async event loop
        results = await asyncio.to_thread(reader.readtext, bytes(photo_bytes), detail=0)
        extracted_text = " ".join(results).upper()
        
        logging.info(f"OCR Raw Output [{user_id}]: {extracted_text}")

        # Extract transaction ID (if present) to prevent double claiming
        tx_match = re.search(r'\b\d{10,20}\b', extracted_text)
        transaction_id = tx_match.group(0) if tx_match else None

        data = database.load_data()
        processed_txs = data.get("processed_transactions", [])

        if transaction_id and transaction_id in processed_txs:
            await status_msg.edit_text(
                "⚠️ <b>ဤပြေစာကို အသုံးပြုပြီးဖြစ်ပါသည်။</b>\n\n"
                "ငွေလွှဲပြေစာ အသစ်ကိုသာ ပေးပို့ပေးပါရန်။",
                parse_mode="HTML"
            )
            return

        # Extract decimal numbers or currency values
        amounts = re.findall(r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b', extracted_text)
        
        # Clean amount strings into float values
        parsed_values = []
        for amt in amounts:
            try:
                parsed_values.append(float(amt.replace(',', '')))
            except ValueError:
                continue

        added_credits = 0
        
        # Match detected amounts against pricing tiers
        if any(val in [1000.0, 1000, 100.0, 100] for val in parsed_values):
            added_credits = 10
        elif any(val in [4500.0, 4500, 450.0, 450] for val in parsed_values):
            added_credits = 30
        elif any(val in [7000.0, 7000, 700.0, 700] for val in parsed_values):
            added_credits = 100

        if added_credits > 0:
            if user_id not in data:
                data[user_id] = {"credits": 5, "last_claimed": None}

            # Update credit balance
            data[user_id]["credits"] += added_credits
            
            # Record transaction ID to block reuse
            if transaction_id:
                if "processed_transactions" not in data:
                    data["processed_transactions"] = []
                data["processed_transactions"].append(transaction_id)

            database.save_data(data)

            new_balance = data[user_id]["credits"]
            
            await status_msg.edit_text(
                f"🎉 <b>ငွေလွှဲပြေစာ စစ်ဆေးမှု အောင်မြင်ပါသည်။</b>\n\n"
                f"🎁 သင့်အကောင့်သို့ <b>+{added_credits} Credit</b> ထည့်သွင်းပေးလိုက်ပါပြီ။\n"
                f"💳 လက်ရှိ လက်ကျန် Credit: <b>{new_balance}</b>",
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(
                "❌ <b>ငွေလွှဲပြေစာ စစ်ဆေးမှု မအောင်မြင်ပါ။</b>\n\n"
                "ပြေစာမှ ငွေပမာဏကို အတည်ပြု၍ မရရှိပါသဖြင့် သင်၏ ငွေလွှဲပြေစာ (Screenshot) နှင့် User ID ကို Admin (@hnin_nns) ထံ တိုက်ရိုက် ပေးပို့၍ အကူအညီရယူပါ။",
                parse_mode="HTML"
            )

    except Exception as e:
        logging.error(f"OCR Error for user {user_id}: {e}")
        await status_msg.edit_text(f"⚠️ Error verifying receipt: {e}")

async def text_to_speech_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Converts user text messages to speech and deducts credits."""
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    # Fetch live user balance
    data = database.load_data()
    user_credits = data.get(user_id, {}).get("credits", 5)

    # Get engine selection (default to classic)
    engine = context.user_data.get("selected_engine", "classic")

    # Set required credits based on engine choice
    cost = 3 if engine == "clone" else 1

    if user_credits < cost:
        await update.message.reply_text(f"❌ Credit မလုံလောက်ပါ။ (လိုအပ်ချက်: {cost} Credits)")
        return

    # Verify balance and deduct credits via database module
    success, error_msg, remaining = database.deduct_credit(user_id, cost=cost)
    if not success:
        await update.message.reply_text(error_msg, parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text("အသံဖိုင် ဖန်တီးနေပါသည်...")

    try:
        # Generate Myanmar speech based on chosen engine (returns BytesIO stream)
        audio_stream = await engine.generate_myanmar_speech(text, engine_type=engine)
        
        await update.message.reply_voice(
            voice=audio_stream,
            caption=f"✅ အသံဖိုင် ဖန်တီးပြီးပါပြီ။\n💳 သင့်လက်ကျန် Credit: **{remaining}**",
            parse_mode="Markdown"
        )
        await status_msg.delete()
    except Exception as e:
        logging.error(f"TTS Error for user {user_id}: {e}")
        await status_msg.edit_text(f"⚠️ Error generating audio: {e}")

async def add_credit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command: /addcredit <user_id> <amount>"""
    sender_id = str(update.effective_user.id)
    
    if sender_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized: Admin access only.")
        return

    try:
        target_user_id = context.args[0]
        amount = int(context.args[1])

        data = database.load_data()
        if target_user_id not in data:
            data[target_user_id] = {"credits": 5, "last_claimed": None}

        data[target_user_id]["credits"] += amount
        database.save_data(data)

        new_bal = data[target_user_id]["credits"]
        
        # Confirm action to Admin
        await update.message.reply_text(
            f"✅ <b>Credit Added Successfully!</b>\n\n"
            f"👤 <b>User ID:</b> <code>{target_user_id}</code>\n"
            f"➕ <b>Added:</b> +{amount} Credits\n"
            f"💳 <b>New Balance:</b> {new_bal} Credits",
            parse_mode="HTML"
        )

        # Notify the targeted user directly
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=(
                    f"🎉 <b>Credit ဖြည့်သွင်းမှု အောင်မြင်ပါသည်။</b>\n\n"
                    f"🎁 သင်၏ အကောင့်သို့ <b>+{amount} Credit</b> ထည့်သွင်းပေးပြီးပါပြီ။\n"
                    f"💳 လက်ရှိ လက်ကျန် Credit: <b>{new_bal}</b>"
                ),
                parse_mode="HTML"
            )
        except Exception:
            await update.message.reply_text("⚠️ Updated database, but could not deliver notification to user.")

    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage: <code>/addcredit &lt;user_id&gt; &lt;amount&gt;</code>", parse_mode="HTML")

if __name__ == '__main__':
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Command and Handler Registrations
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("addcredit", add_credit_command))
    app.add_handler(CommandHandler("balance", check_balance_command))
    app.add_handler(CommandHandler("credit", check_balance_command))
    
    app.add_handler(CallbackQueryHandler(button_callback_handler))
    
    app.add_handler(MessageHandler(filters.PHOTO, photo_receipt_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech_handler))

    print("HH-Voice-Bot is running with full features...")
    app.run_polling()