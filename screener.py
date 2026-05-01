import yfinance as yf
import pandas as pd

# ===============================
# STOCHASTIC
# ===============================
def stochastic(df):
    low_min = df["Low"].rolling(10).min()
    high_max = df["High"].rolling(10).max()
    k = 100 * (df["Close"] - low_min) / (high_max - low_min)
    k = k.rolling(5).mean()
    d = k.rolling(5).mean()
    return k, d

# ===============================
# SUPERTREND
# ===============================
def supertrend(df):
    high, low, close = df['High'], df['Low'], df['Close']

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1/2, adjust=False).mean()

    hl2 = (high + low) / 2
    upper = hl2 + atr
    lower = hl2 - atr

    trend = [1]

    for i in range(1, len(df)):
        if close.iloc[i] > upper.iloc[i-1]:
            trend.append(1)
        elif close.iloc[i] < lower.iloc[i-1]:
            trend.append(-1)
        else:
            trend.append(trend[i-1])

    df["trend"] = trend
    return df

# ===============================
# GET DATA
# ===============================
def get_data(symbol, interval):
    try:
        df = yf.download(symbol, period="3mo", interval=interval, progress=False)

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[['High','Low','Close','Volume']].dropna()

        if len(df) < 20:
            return None

        df["K"], df["D"] = stochastic(df)
        df = supertrend(df)

        return df
    except:
        return None

# ===============================
# BANDAR DETECTION
# ===============================
def bandar_detect(df):
    avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
    vol_now = df["Volume"].iloc[-1]

    if vol_now > avg_vol * 1.5:
        return True
    return False

# ===============================
# SCORE SYSTEM
# ===============================
def calculate_score(df, new_trend):
    score = 0

    k = df["K"].iloc[-1]
    d = df["D"].iloc[-1]

    if new_trend:
        score += 40

    if k < 30 and d < 30:
        score += 30

    if bandar_detect(df):
        score += 20

    if df["trend"].iloc[-1] == 1:
        score += 10

    return score

# ===============================
# TREND
# ===============================
def is_new_uptrend(df):
    return df["trend"].iloc[-2] == -1 and df["trend"].iloc[-1] == 1

def is_uptrend(df):
    return df["trend"].iloc[-1] == 1

# ===============================
# FORMAT
# ===============================
def format_output(symbol, df, label, score, bandar):
    close = round(float(df["Close"].iloc[-1]),2)
    volume = int(df["Volume"].iloc[-1])
    value = int(close * volume)

    k = df["K"].iloc[-1]
    d = df["D"].iloc[-1]

    bandar_txt = "✅ MASUK" if bandar else "❌ SEPI"

    return (
        f"╔══════════════════════╗\n"
        f"🎯 {symbol}\n"
        f"╠══════════════════════╣\n"
        f"💰 Harga   : {close}\n"
        f"📊 + Bumbu : {round(k,2)}\n"
        f"📊 + Bumbu : {round(d,2)}\n"
        f"📊 Volume  : {volume:,}\n"
        f"💵 Value   : Rp {value:,}\n"
        f"💰 Bandar  : {bandar_txt}\n"
        f"🎯 Score   : {score}\n"
        f"🏷 Label   : {label}\n"
        f"📈 Chart   : https://stockbit.com/symbol/{symbol.replace('.JK','')}?chart=1\n"
        f"╚══════════════════════╝"
    )

# ===============================
# MAIN SIGNAL
# ===============================
def get_signal(symbol, mode):
    df = get_data(symbol, "1d")
    if df is None:
        return None

    new_trend = is_new_uptrend(df)
    bandar = bandar_detect(df)
    score = calculate_score(df, new_trend)

    # BUY STRONG
    if mode == "buy_d":
        if new_trend and df["K"].iloc[-1] < 30:
            return format_output(symbol, df, "🔥 SMART MONEY", score, bandar)

    # FAST
    if mode == "fast_1d":
        if new_trend:
            return format_output(symbol, df, "⚡ FAST BUY", score, bandar)

    # WEEKLY
    if mode == "weekly":
        if is_uptrend(df):
            return format_output(symbol, df, "🚀 TREND", score, bandar)

    return None
