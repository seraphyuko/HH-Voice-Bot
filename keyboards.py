from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_tts_engine_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                "🎙️ Classic TTS (Standard - 1 Credit)", 
                callback_data="btn_tts_classic"
            )
        ],
        [
            InlineKeyboardButton(
                "TTS(Voice Clone) (Beta - Premium 3 Credits)", 
                callback_data="btn_tts_clone"
            )
        ],
        [
            InlineKeyboardButton(
                "◀️ ပင်မစာမျက်နှာသို့", 
                callback_data="btn_main_menu"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
    
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Returns the main menu inline keyboard structure."""
    keyboard = [
        [InlineKeyboardButton("🚀 Web App ဖွင့်မည်", web_app={"url": "https://example.com"})],
        [InlineKeyboardButton("🎙 စာသားမှအသံ", callback_data="btn_tts")],
        [
            InlineKeyboardButton("🎬 အလိုအလျောက် Recap", callback_data="btn_recap"),
            InlineKeyboardButton("🌐 အလိုအလျောက် ဘာသာပြန်", callback_data="btn_translate")
        ],
        [InlineKeyboardButton("🎬 ReadyMade Videos", callback_data="btn_readymade")],
        [InlineKeyboardButton("🧰 Recap ကိရိယာများ", callback_data="btn_tools")],
        [InlineKeyboardButton("📕 RedNote Downloader - 1 Credit", callback_data="btn_rednote")],
        [
            InlineKeyboardButton("🎁 နေ့စဉ်ဝင်မည် - +2 Credit", callback_data="btn_daily_credit"),
            InlineKeyboardButton("💳 Credit ဖြည့်မည်", callback_data="btn_topup")
        ],
        [
            InlineKeyboardButton("🌐 English", callback_data="btn_lang_en"),
            InlineKeyboardButton("💬 Admin ထံ စာပို့မည်", url="https://t.me/your_admin_username")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)