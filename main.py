import telebot
import time
from screener import get_supertrend_signal
from issi_symbols import ISSI_SYMBOLS

TOKEN = "ISI_TOKEN_KAMU_DISINI"
bot = telebot.TeleBot(TOKEN)

# ===============================
# START MESSAGE
# ===============================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
"""Halo👋🏼 aku asisten ALPHA🤖
aku akan membantumu scan saham yang bagus🚀⚡

Silahkan scan😁
Pilih salah satu command dibawah yaa😁

/buy_strong   → Daily (akurasi tinggi)
/buy_high     → H4 (swing)
/strong_buy   → Weekly 🚀
/fastswing_1D → Fast Daily ⚡
/fastswing_4H → Fast H4 ⚡
/sniper_entry → ENTRY PALING AKURAT 🎯🔥
""")

# ===============================
# CORE SCAN FUNCTION (ANTI DOUBLE)
# ===============================
def scan(symbols, interval, mode="normal"):
    results = []
    sent = set()

    for sym in symbols:
        data = get_supertrend_signal(sym, interval, mode)

        if data and data["symbol"] not in sent:
            results.append(data["text"])
            sent.add(data["symbol"])

    return results

# ===============================
# SEND MESSAGE PER 1 SAHAM
# ===============================
def kirim_satu_satu(chat_id, results, title):
    if not results:
        bot.send_message(chat_id, "❌ Tidak ada signal")
        return

    bot.send_message(chat_id, title)

    for res in results:
        try:
            bot.send_message(chat_id, res)
            time.sleep(1)
        except Exception as e:
            print("Send error:", e)

# ===============================
# DAILY (FILTER KETAT)
# ===============================
@bot.message_handler(commands=['buy_strong'])
def buy_daily(message):
    bot.reply_to(message, "🔍 Scanning Daily... tunggu ±3 menit 🤗")

    hasil = scan(ISSI_SYMBOLS, "1d", mode="strict")

    kirim_satu_satu(message.chat.id, hasil, "🔥 BUY STRONG (DAILY)")

# ===============================
# H4 (FILTER)
# ===============================
@bot.message_handler(commands=['buy_high'])
def buy_h4(message):
    bot.reply_to(message, "🔍 Scanning H4... tunggu ±3 menit 🤗")

    hasil = scan(ISSI_SYMBOLS, "1h", mode="strict")

    kirim_satu_satu(message.chat.id, hasil, "⚡ BUY HIGH (H4)")

# ===============================
# WEEKLY (NO FILTER)
# ===============================
@bot.message_handler(commands=['strong_buy'])
def buy_weekly(message):
    bot.reply_to(message, "🔍 Scanning Weekly... 🤗")

    hasil = scan(ISSI_SYMBOLS, "1wk", mode="fast")

    kirim_satu_satu(message.chat.id, hasil, "🚀 STRONG BUY WEEKLY")

# ===============================
# FAST DAILY
# ===============================
@bot.message_handler(commands=['fastswing_1D'])
def fast_daily(message):
    bot.reply_to(message, "🔍 Fast Scan Daily... ⚡")

    hasil = scan(ISSI_SYMBOLS, "1d", mode="fast")

    kirim_satu_satu(message.chat.id, hasil, "⚡ FAST SWING DAILY")

# ===============================
# FAST H4
# ===============================
@bot.message_handler(commands=['fastswing_4H'])
def fast_h4(message):
    bot.reply_to(message, "🔍 Fast Scan H4... ⚡")

    hasil = scan(ISSI_SYMBOLS, "1h", mode="fast")

    kirim_satu_satu(message.chat.id, hasil, "⚡ FAST SWING H4")

# ===============================
# SNIPER ENTRY (MULTI TF)
# ===============================
@bot.message_handler(commands=['sniper_entry'])
def sniper_entry(message):
    bot.reply_to(message, "🎯 Sniper Entry Scan... (1H + H4 + Daily) 🔥")

    results = []
    sent = set()

    for sym in ISSI_SYMBOLS:
        d1 = get_supertrend_signal(sym, "1d", "strict")
        h4 = get_supertrend_signal(sym, "1h", "strict")
        h1 = get_supertrend_signal(sym, "1h", "strict")

        if d1 and h4 and h1:
            if sym not in sent:
                results.append(d1["text"])
                sent.add(sym)

    kirim_satu_satu(message.chat.id, results, "🎯 SNIPER ENTRY 🔥")

# ===============================
# RUN BOT (ANTI ERROR 409)
# ===============================
while True:
    try:
        print("🤖 Bot jalan...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print("Error:", e)
        time.sleep(5)
