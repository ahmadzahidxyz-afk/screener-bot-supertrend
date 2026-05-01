import telebot
import time
from screener import get_supertrend_signal, get_sniper_signal
from issi_symbols import ISSI_SYMBOLS

TOKEN = "8540062679:AAFfnJF5M2eCYjzPY6hFWX56jHrxDRCNnNw"
bot = telebot.TeleBot(TOKEN)

ISSI_SYMBOLS = list(set(ISSI_SYMBOLS))

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
"""Halo👋🏼 aku ALPHA🤖

/buy_strong  → Daily
/buy_high    → H4
/strong_buy  → Weekly
/fastswing_1D → Fast Daily
/fastswing_4H → Fast H4
/sniper_entry → ENTRY PALING AKURAT 🎯🔥
""")

def scan_and_send(message, interval, mode):
    sent = set()
    for sym in ISSI_SYMBOLS:
        data = get_supertrend_signal(sym, interval, mode)
        if data and sym not in sent:
            bot.send_message(message.chat.id, data["text"])
            sent.add(sym)
            time.sleep(1)

@bot.message_handler(commands=['buy_strong'])
def buy_daily(message):
    scan_and_send(message, "1d", "normal")

@bot.message_handler(commands=['buy_high'])
def buy_h4(message):
    scan_and_send(message, "1h", "normal")

@bot.message_handler(commands=['strong_buy'])
def strong(message):
    scan_and_send(message, "1wk", "strong")

@bot.message_handler(commands=['fastswing_1D'])
def fast_1d(message):
    scan_and_send(message, "1d", "fast")

@bot.message_handler(commands=['fastswing_4H'])
def fast_4h(message):
    scan_and_send(message, "1h", "fast")

@bot.message_handler(commands=['sniper_entry'])
def sniper(message):
    bot.reply_to(message, "🎯 SNIPER SCAN...")

    results = []
    for sym in ISSI_SYMBOLS:
        data = get_sniper_signal(sym)
        if data:
            results.append((sym, data["score"], data["text"]))

    results.sort(key=lambda x: x[1], reverse=True)

    for r in results[:10]:
        bot.send_message(message.chat.id, r[2])
        time.sleep(1)

while True:
    try:
        print("🤖 Bot jalan...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print("Error:", e)
        time.sleep(5)
