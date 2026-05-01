import telebot
import time
from screener import get_supertrend_signal
from issi_symbols import ISSI_SYMBOLS

TOKEN = "8540062679:AAFfnJF5M2eCYjzPY6hFWX56jHrxDRCNnNw"
bot = telebot.TeleBot(TOKEN)

# ===============================
# START
# ===============================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
"""Halo👋🏼 aku asisten ALPHA🤖

Silahkan scan😁 pilih command:

/buy_strong   → Daily (Supertrend + Stoch)
/buy_high     → H4
/strong_buy   → Weekly
/fastswing_1D → Fast Daily ⚡
/fastswing_4H → Fast H4 ⚡
/sniper_entry → ENTRY PALING AKURAT 🎯🔥
""")

# ===============================
# SCAN CORE
# ===============================
def scan(symbols, interval, mode):
    results = []
    sent = set()

    for sym in symbols:
        data = get_supertrend_signal(sym, interval, mode)

        if data and sym not in sent:
            results.append(data["text"])
            sent.add(sym)

    return results

# ===============================
# SEND PER SAHAM
# ===============================
def kirim(chat_id, hasil, title):
    if not hasil:
        bot.send_message(chat_id, "❌ Tidak ada signal")
        return

    bot.send_message(chat_id, title)

    for h in hasil:
        try:
            bot.send_message(chat_id, h)
            time.sleep(1)
        except Exception as e:
            print("Error kirim:", e)

# ===============================
# COMMANDS
# ===============================
@bot.message_handler(commands=['buy_strong'])
def daily(message):
    bot.reply_to(message, "🔍 Scanning Daily...")
    hasil = scan(ISSI_SYMBOLS, "1d", "strict")
    kirim(message.chat.id, hasil, "🔥 BUY STRONG DAILY")

@bot.message_handler(commands=['buy_high'])
def h4(message):
    bot.reply_to(message, "🔍 Scanning H4...")
    hasil = scan(ISSI_SYMBOLS, "1h", "strict")
    kirim(message.chat.id, hasil, "⚡ BUY HIGH H4")

@bot.message_handler(commands=['strong_buy'])
def weekly(message):
    bot.reply_to(message, "🔍 Scanning Weekly...")
    hasil = scan(ISSI_SYMBOLS, "1wk", "weekly")
    kirim(message.chat.id, hasil, "🚀 WEEKLY TREND")

@bot.message_handler(commands=['fastswing_1D'])
def fast_d(message):
    bot.reply_to(message, "🔍 Fast Scan Daily...")
    hasil = scan(ISSI_SYMBOLS, "1d", "fast")
    kirim(message.chat.id, hasil, "⚡ FAST DAILY")

@bot.message_handler(commands=['fastswing_4H'])
def fast_h(message):
    bot.reply_to(message, "🔍 Fast Scan H4...")
    hasil = scan(ISSI_SYMBOLS, "1h", "fast")
    kirim(message.chat.id, hasil, "⚡ FAST H4")

@bot.message_handler(commands=['sniper_entry'])
def sniper(message):
    bot.reply_to(message, "🎯 Sniper Entry Scan...")

    results = []
    sent = set()

    for sym in ISSI_SYMBOLS:
        d = get_supertrend_signal(sym, "1d", "strict")
        h4 = get_supertrend_signal(sym, "1h", "strict")

        if d and h4 and sym not in sent:
            results.append(d["text"])
            sent.add(sym)

    kirim(message.chat.id, results, "🎯 SNIPER ENTRY")

# ===============================
# RUN BOT
# ===============================
while True:
    try:
        print("🤖 Bot jalan...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print("Error:", e)
        time.sleep(5)
