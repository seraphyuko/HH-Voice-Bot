import os
from datetime import date
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv("token.env")

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["hh_voice_bot"]

users_col = db["users"]
txs_col = db["processed_transactions"]

def get_user(user_id: str | int) -> dict:
    """Fetch user data, create default record if user does not exist."""
    uid = str(user_id)
    user = users_col.find_one({"_id": uid})
    if not user:
        user = {"_id": uid, "credits": 5, "last_claimed": None}
        users_col.insert_one(user)
    return user

def load_data() -> dict:
    """Compatibility helper for main.py state management."""
    users = {str(doc["_id"]): doc for doc in users_col.find()}
    processed = [str(doc["_id"]) for doc in txs_col.find()]
    users["processed_transactions"] = processed
    return users

def save_data(data: dict):
    """Saves/Updates user state and processed transactions."""
    for key, val in data.items():
        if key == "processed_transactions":
            for tx_id in val:
                txs_col.update_one({"_id": str(tx_id)}, {"$set": {"_id": str(tx_id)}}, upsert=True)
        elif isinstance(val, dict):
            users_col.update_one(
                {"_id": str(key)},
                {"$set": {"credits": val.get("credits", 5), "last_claimed": val.get("last_claimed")}},
                upsert=True
            )

def deduct_credit(user_id: str | int, cost: int = 1) -> tuple[bool, str, int]:
    """Atomically deducts credits from user balance."""
    uid = str(user_id)
    
    # Try atomic deduction directly in MongoDB to avoid race conditions
    result = users_col.find_one_and_update(
        {"_id": uid, "credits": {"$gte": cost}},
        {"$inc": {"credits": -cost}},
        return_document=True
    )

    if result is None:
        user = get_user(uid)
        current = user.get("credits", 0)
        return False, f"❌ Credit မလုံလောက်ပါ။ (လိုအပ်ချက်: {cost} Credits)", current

    return True, "", result["credits"]

def claim_daily_credit(user_id: str | int) -> tuple[bool, str, int]:
    """Claims daily bonus credits once per calendar day."""
    uid = str(user_id)
    user = get_user(uid)
    today_str = date.today().isoformat()

    if user.get("last_claimed") == today_str:
        return False, "⚠️ သင် ယနေ့အတွက် Daily Credit ရယူပြီးဖြစ်ပါသည်။", user.get("credits", 0)

    new_balance = user.get("credits", 0) + 1
    users_col.update_one(
        {"_id": uid},
        {"$set": {"credits": new_balance, "last_claimed": today_str}}
    )
    return True, f"🎉 **Daily Credit +1** ရရှိပါသည်။\n💳 လက်ရှိ လက်ကျန် Credit: **{new_balance}**", new_balance