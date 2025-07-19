
import os
import json
import asyncio
import datetime
import requests
import nest_asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# 🔐 Твій Telegram токен і тимчасове chat_id (заміниш після /start)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = "815490600"  # Замінити після отримання chat_id від бота

COINS = ["ethereum", "solana", "arbitrum", "lido-dao"]
SYMBOLS = {
    "ethereum": "ETH",
    "solana": "SOL",
    "arbitrum": "ARB",
    "lido-dao": "LDO"
}

API_URL = "https://api.coingecko.com/api/v3/simple/price"

async def get_coin_data():
    params = {
        "ids": ",".join(COINS),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_1hr_change": "true"
    }
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def analyze(data):
    changes_1h = {k: v.get("usd_1h_change", 0) for k, v in data.items()}
    sorted_coins = sorted(changes_1h.items(), key=lambda x: x[1], reverse=True)
    top = sorted_coins[0]
    worst = sorted_coins[-1]
    diff = top[1] - worst[1]
    return top, worst, diff

async def send_signal(bot, top, worst, diff):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    msg = (
        f"⚡ [{now}] Перелив з {SYMBOLS[top[0]]} у {SYMBOLS[worst[0]]}\n"
        f"▸ {SYMBOLS[top[0]]}: {top[1]:.2f}% за 1 год\n"
        f"▸ {SYMBOLS[worst[0]]}: {worst[1]:.2f}% за 1 год\n"
        f"📊 Δ = {diff:.2f}% (поріг ≥ 3%)"
    )
    await bot.send_message(chat_id=CHAT_ID, text=msg)

async def send_status(bot, text):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    await bot.send_message(chat_id=CHAT_ID, text=f"✅ [{now}] {text}")

async def periodic_check(application):
    bot = application.bot
    while True:
        try:
            data = await get_coin_data()
            if data:
                top, worst, diff = analyze(data)
                if diff >= 3:
                    await send_signal(bot, top, worst, diff)
                else:
                    await send_status(bot, "Активний. Сигналів нема. Ринок спокійний.")
            else:
                await send_status(bot, "Помилка при отриманні даних.")
        except Exception as e:
            await send_status(bot, f"⚠️ Помилка: {str(e)}")
        await asyncio.sleep(300)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    await update.message.reply_text(f"👋 Бот працює. Твій chat_id: {user_id}")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    asyncio.create_task(periodic_check(app))
    print("✅ Бот запущено. Очікує сигнали...")
    await app.run_polling()

# ✅ Windows-фікс: asyncio loop із nest_asyncio
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())

    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
