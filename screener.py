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
def supertrend(df, period=2, multiplier=1):
    high = df['High']
    low = df['Low']
    close = df['Close']

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1/period, adjust=False).mean()

    hl2 = (high + low) / 2
    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr

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
# FORMAT OUTPUT PRO
# ===============================
def format_output(symbol, close, volume, value, k, d, label, bandar, score):
    value_fmt = f"{value:,}".replace(",", ".")
    volume_fmt = f"{volume:,}"

    return (
        f"╔══════════════════════╗\n"
        f"🎯 {symbol}\n"
        f"╠══════════════════════╣\n"
        f"💰 Harga   : {round(close,2)}\n"
        f"📊 + Bumbu : {round(k,2)}\n"
        f"📊 + Bumbu : {round(d,2)}\n"
        f"📊 Volume  : {volume_fmt}\n"
        f"💵 Value   : Rp {value_fmt}\n"
        f"💰 Bandar  : {bandar}\n"
        f"🎯 Score   : {score}\n"
        f"🏷 Label   : {label}\n"
        f"📈 Chart   : https://stockbit.com/symbol/{symbol.replace('.JK','')}?chart=1\n"
        f"╚══════════════════════╝"
    )

# ===============================
# MAIN SIGNAL
# ===============================
def get_supertrend_signal(symbol, interval="1d", mode="strict"):
    try:
        df = yf.download(symbol, period="3mo", interval=interval, progress=False)

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[['High','Low','Close','Volume']].dropna()

        # 🔥 FIX: buang candle terakhir
        df = df.iloc[:-1]
        df = df.tail(100)

        if len(df) < 30:
            return None

        df["K"], df["D"] = stochastic(df)
        df = supertrend(df)

        prev = df['trend'].iloc[-2]
        curr = df['trend'].iloc[-1]
        flip = (prev == -1 and curr == 1)

        k = df["K"].iloc[-1]
        d = df["D"].iloc[-1]

        close = float(df["Close"].iloc[-1])
        volume = int(df["Volume"].iloc[-1])
        value = int(close * volume)

        # ===============================
        # BANDAR DETECTION
        # ===============================
        vol_avg = df["Volume"].rolling(20).mean()
        bandar_flag = volume > (vol_avg.iloc[-1] * 2)

        # ===============================
        # SCORING
        # ===============================
        score = 0
        if flip:
            score += 40
        if k < 30 and d < 30:
            score += 20
        if bandar_flag:
            score += 30
        if value > 1_000_000_000:
            score += 10

        # ===============================
        # MODE FILTER
        # ===============================
        if mode == "strict":
            if not (flip and k < 30 and d < 30):
                return None

        elif mode == "fast":
            if not flip:
                return None

        elif mode == "weekly":
            if curr != 1:
                return None

        # ===============================
        # LABEL
        # ===============================
        if score >= 80:
            label = "🔥 SMART MONEY"
        elif score >= 60:
            label = "🚀 STRONG BUY"
        elif score >= 40:
            label = "⚡ EARLY BUY"
        else:
            return None

        bandar_text = "✅ MASUK" if bandar_flag else "❌ TIDAK"

        return {
            "symbol": symbol,
            "text": format_output(symbol, close, volume, value, k, d, label, bandar_text, score)
        }

    except Exception as e:
        print(symbol, "error:", e)
        return None
