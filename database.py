import json
import os
from datetime import datetime, timedelta

DATA_FILE = "users.json"

def load_data():
    """Loads user data from JSON file."""
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def deduct_credit(user_id: str, cost: int = 1) -> tuple[bool, str, int]:
    """
    Deducts credits for service usage.
    Returns: (success_boolean, message, remaining_credits)
    """
    data = load_data()
    
    if user_id not in data or data[user_id].get("credits", 0) < cost:
        current = data.get(user_id, {}).get("credits", 0)
        msg = (
            "❌ **Credit မလုံလောက်ပါ!**\n\n"
            f"ဤဝန်ဆောင်မှုကို အသုံးပြုရန် **{cost} Credit** လိုအပ်ပါသည်။\n"
            f"သင့်လက်ကျန် Credit: **{current}**\n\n"
            "🎁 'နေ့စဉ်ဝင်မည်' မှ Credit အခမဲ့ ရယူပါ သို့မဟုတ် Credit ဖြည့်ပါ parameter။"
        )
        return False, msg, current

    data[user_id]["credits"] -= cost
    save_data(data)
    
    remaining = data[user_id]["credits"]
    return True, "Credit deducted", remaining

def save_data(data):
    """Saves user data to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def claim_daily_credit(user_id: str) -> tuple[bool, str, int]:
    """
    Checks if user can claim daily credit.
    Returns: (success_boolean, message, updated_balance)
    """
    data = load_data()
    now = datetime.now()

    # Initialize user if new
    if user_id not in data:
        data[user_id] = {
            "credits": 5,
            "last_claimed": None
        }

    user_info = data[user_id]
    last_claimed_str = user_info.get("last_claimed")

    # Check 24-hour limit
    if last_claimed_str:
        last_claimed = datetime.fromisoformat(last_claimed_str)
        time_passed = now - last_claimed
        
        if time_passed < timedelta(hours=24):
            remaining_time = timedelta(hours=24) - time_passed
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            msg = (
                "⚠️ **ယနေ့အတွက် Bonus ရယူပြီးပါပြီ!**\n\n"
                f"နောက်ထပ် ရယူနိုင်ရန် **{hours} နာရီ {minutes} မိနစ်** စောင့်ဆိုင်းပါ။\n"
                f"💳 လက်ရှိ လက်ကျန် Credit: **{user_info['credits']}**"
            )
            return False, msg, user_info["credits"]

    # Award +2 credits and record timestamp
    user_info["credits"] += 2
    user_info["last_claimed"] = now.isoformat()
    data[user_id] = user_info
    save_data(data)

    msg = (
        "🎉 **နေ့စဉ်ဝင်ရောက်မှု Bonus အောင်မြင်ပါသည်!**\n\n"
        f"🎁 သင် +2 Credit ရရှိပါသည်။\n"
        f"💳 လက်ရှိ လက်ကျန် Credit: **{user_info['credits']}**"
    )
    return True, msg, user_info["credits"]