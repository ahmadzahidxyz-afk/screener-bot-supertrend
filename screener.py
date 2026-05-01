import yfinance as yf
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")

# ===============================
# CLEAN SYMBOL
# ===============================
def clean_symbol(symbol):
    return symbol.replace(".JK","")

# ===============================
# STOCHASTIC
# ===============================
def stochastic(df, k_period=10, d_period=5, smooth_k=5):
    low_min = df["Low"].rolling(k_period).min()
    high_max = df["High"].rolling(k_period).max()

    k_fast = 100 * (df["Close"] - low_min) / (high_max - low_min)
    k_smooth = k_fast.rolling(smooth_k).mean()
    d_line = k_smooth.rolling(d_period).mean()

    return k_smooth, d_line

# ===============================
# SUPERTREND
# ===============================
def supertrend(df, period=2, multiplier=1):
    df = df.copy()

    high = df['High'].astype(float)
    low = df['Low'].astype(float)
    close = df['Close'].astype(float)

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1/period, adjust=False).mean()

    hl2 = (high + low) / 2
    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr

    final_upper = upper.copy()
    final_lower = lower.copy()

    for i in range(1, len(df)):
        if upper.iloc[i] < final_upper.iloc[i-1] or close.iloc[i-1] > final_upper.iloc[i-1]:
            final_upper.iloc[i] = upper.iloc[i]
        else:
            final_upper.iloc[i] = final_upper.iloc[i-1]

        if lower.iloc[i] > final_lower.iloc[i-1] or close.iloc[i-1] < final_lower.iloc[i-1]:
            final_lower.iloc[i] = lower.iloc[i]
        else:
            final_lower.iloc[i] = final_lower.iloc[i-1]

    trend = [1]

    for i in range(1, len(df)):
        if close.iloc[i] > final_upper.iloc[i-1]:
            trend.append(1)
        elif close.iloc[i] < final_lower.iloc[i-1]:
            trend.append(-1)
        else:
            trend.append(trend[i-1])

    df['trend'] = trend
    return df

# ===============================
# FORMAT OUTPUT
# ===============================
def format_output(data):
    value_fmt = f"{data['value']:,}".replace(",", ".")
    volume_fmt = f"{data['volume']:,}"

    return (
        f"╔══════════════════════╗\n"
        f"🎯 {data['symbol']}\n"
        f"╠══════════════════════╣\n"
        f"💰 Harga   : {data['close']}\n"
        f"📊 + Bumbu : {data['k']}\n"
        f"📊 + Bumbu : {data['d']}\n"
        f"📊 Volume  : {volume_fmt}\n"
        f"💵 Value   : Rp {value_fmt}\n"
        f"💰 Bandar  : {data['bandar']}\n"
        f"🎯 Score   : {data['score']}\n"
        f"🏷 Label   : {data['label']}\n"
        f"📈 Chart   : https://stockbit.com/symbol/{data['clean']}?chart=1\n"
        f"╚══════════════════════╝"
    )

# ===============================
# MAIN SIGNAL
# ===============================
def get_supertrend_signal(symbol, interval="1d", mode="normal"):
    try:
        df = yf.download(symbol, period="3mo", interval=interval, progress=False)

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[['High','Low','Close','Volume']].dropna()

        # FIX H4
        if interval == "1h":
            df = df.iloc[::4]

        df["K"], df["D"] = stochastic(df)
        df = supertrend(df)

        if len(df) < 10:
            return None

        close = float(df["Close"].iloc[-1])
        volume = int(df["Volume"].iloc[-1])
        value = int(close * volume)

        k = float(df["K"].iloc[-1]) if not np.isnan(df["K"].iloc[-1]) else 50
        d = float(df["D"].iloc[-1]) if not np.isnan(df["D"].iloc[-1]) else 50

        curr = df['trend'].iloc[-1]

        recent_flip = False
        for i in range(-5, -1):
            if df['trend'].iloc[i-1] == -1 and df['trend'].iloc[i] == 1:
                recent_flip = True

        avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
        bandar = "✅ MASUK" if volume > avg_vol * 1.5 else "❌"

        score = 0
        if recent_flip: score += 40
        if curr == 1: score += 30
        if bandar == "✅ MASUK": score += 30

        if mode == "fast":
            if not recent_flip: return None
            label = "⚡ FAST BUY"

        elif mode == "strong":
            if curr != 1: return None
            label = "🚀 UPTREND"

        else:
            if not (recent_flip and k < 25 and d < 25):
                return None
            label = "🔥 SMART MONEY"

        return {
            "symbol": symbol,
            "clean": clean_symbol(symbol),
            "close": round(close,2),
            "volume": volume,
            "value": value,
            "k": round(k,2),
            "d": round(d,2),
            "label": label,
            "bandar": bandar,
            "score": score,
            "text": format_output({
                "symbol": symbol,
                "clean": clean_symbol(symbol),
                "close": round(close,2),
                "volume": volume,
                "value": value,
                "k": round(k,2),
                "d": round(d,2),
                "label": label,
                "bandar": bandar,
                "score": score
            })
        }

    except Exception as e:
        print(symbol, "error:", e)
        return None

# ===============================
# SNIPER ENTRY (MULTI TF)
# ===============================
def get_sniper_signal(symbol):
    try:
        df_d = yf.download(symbol, period="3mo", interval="1d", progress=False)
        df_h4 = yf.download(symbol, period="1mo", interval="1h", progress=False)
        df_h1 = yf.download(symbol, period="7d", interval="1h", progress=False)

        if df_d.empty or df_h4.empty or df_h1.empty:
            return None

        for df in [df_d, df_h4, df_h1]:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

        df_d = df_d[['High','Low','Close','Volume']].dropna()
        df_h4 = df_h4[['High','Low','Close','Volume']].dropna().iloc[::4]
        df_h1 = df_h1[['High','Low','Close','Volume']].dropna()

        df_d = supertrend(df_d)
        df_h4 = supertrend(df_h4)
        df_h1 = supertrend(df_h1)

        if len(df_h1) < 10:
            return None

        if df_d['trend'].iloc[-1] != 1: return None
        if df_h4['trend'].iloc[-1] != 1: return None

        if not (df_h1['trend'].iloc[-2] == -1 and df_h1['trend'].iloc[-1] == 1):
            return None

        close = float(df_h1["Close"].iloc[-1])
        volume = int(df_h1["Volume"].iloc[-1])
        value = int(close * volume)

        avg_vol = df_h1["Volume"].rolling(20).mean().iloc[-1]
        bandar = "✅ MASUK" if volume > avg_vol * 1.5 else "❌"

        score = 70 + (30 if bandar == "✅ MASUK" else 0)

        text = (
            f"╔══════════════════════╗\n"
            f"🎯 {symbol}\n"
            f"╠══════════════════════╣\n"
            f"💰 Harga   : {round(close,2)}\n"
            f"📊 Volume  : {volume:,}\n"
            f"💵 Value   : Rp {value:,}".replace(",", ".") + "\n"
            f"💰 Bandar  : {bandar}\n"
            f"🎯 Score   : {score}\n"
            f"🏷 Label   : 🎯 SNIPER ENTRY\n"
            f"📈 Chart   : https://stockbit.com/symbol/{symbol.replace('.JK','')}?chart=1\n"
            f"╚══════════════════════╝"
        )

        return {"text": text, "score": score}

    except Exception as e:
        print(symbol, "sniper error:", e)
        return None
