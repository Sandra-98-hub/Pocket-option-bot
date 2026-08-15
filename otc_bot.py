import os
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

print("BOT STARTING")
print("TOKEN PRESENT:", bool(TOKEN))
print("CHAT ID PRESENT:", bool(CHAT_ID))

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": "✅ TEST FROM RENDER BOT"
    },
    timeout=10
)

print("TELEGRAM STATUS:", response.status_code)
print("TELEGRAM RESPONSE:", response.text)
