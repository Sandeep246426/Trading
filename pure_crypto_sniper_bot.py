import requests
import time

# ================= CREDENTIALS =================
TELEGRAM_TOKEN = "8924870114:AAFyjQ9VQXeYql8W7uTIZpc0IOoo1wY1vVw"
CHAT_ID = "1110749441"
# ===============================================

BLACKLIST = [
    'USDCUSDT', 'FDUSDUSDT', 'TUSDUSDT', 'BUSDUSDT', 'EURUSDT', 
    'USDPUSDT', 'DAIUSDT', 'USDEUSDT', 'USD1USDT', 'EURIUSDT'
]

def send_msg(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}", flush=True)

# 1. INSTITUTIONAL EXPANSION / MARUBOZU LOGIC
def is_institutional_candle(o, h, l, c):
    total_range = h - l
    if total_range <= 0: return False, "NONE"
    body = abs(c - o)
    body_ratio = body / total_range
    
    # 65%+ ठोस बॉडी और छोटी विक = बिग प्लेयर कैंडल
    if body_ratio >= 0.65:
        if c > o and (h - c) <= 0.18 * total_range:
            return True, "BULLISH_EXPANSION"
        elif c < o and (c - l) <= 0.18 * total_range:
            return True, "BEARISH_EXPANSION"
    return False, "NONE"

# 2. 15M TECHNICAL ENTRY SNIPER
def check_crypto_15m_entry(symbol, flow_type):
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=15m&limit=30"
        data = requests.get(url, timeout=5).json()
        if not data or len(data) < 20: return None

        o, h, l, c = float(data[-1][1]), float(data[-1][2]), float(data[-1][3]), float(data[-1][4])
        vols = [float(k[5]) for k in data]
        avg_vol = sum(vols[-10:]) / 10
        vol_surge = vols[-1] > (avg_vol * 1.1)

        is_big_candle, candle_type = is_institutional_candle(o, h, l, c)

        signal = None
        if "INFLOW" in flow_type and candle_type == "BULLISH_EXPANSION" and vol_surge:
            signal = "BUY / LONG 🟢 (Smart Money Breakout)"
            sl = round(l * 0.995, 6)
            risk = c - sl
            if risk <= 0: return None
            tp1 = round(c + (risk * 2.0), 6)
            tp2 = round(c + (risk * 4.0), 6)
        elif "OUTFLOW" in flow_type and candle_type == "BEARISH_EXPANSION" and vol_surge:
            signal = "SELL / SHORT 🔴 (Smart Money Dump)"
            sl = round(h * 1.005, 6)
            risk = sl - c
            if risk <= 0: return None
            tp1 = round(c - (risk * 2.0), 6)
            tp2 = round(c - (risk * 4.0), 6)

        if signal:
            return {
                "symbol": symbol,
                "action": signal,
                "entry": c,
                "sl": sl,
                "tp1": tp1,
                "tp2": tp2,
                "pattern": "Solid Institutional Marubozu"
            }
    except:
        return None

# 3. AUTO-DISCOVERY & CONTINUOUS SCANNER
def run_crypto_scanner():
    print("Auto-Scanning High-Movement Binance Futures Coins...", flush=True)
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        tickers = requests.get(url, timeout=10).json()
        
        valid_coins = []
        for t in tickers:
            sym = t['symbol']
            if sym.endswith('USDT') and sym not in BLACKLIST and not any(k in sym for k in ['UP', 'DOWN', 'BEAR', 'BULL']):
                vol = float(t['quoteVolume'])
                # $25M+ वॉल्यूम वाले सभी एक्टिव कॉइन्स
                if vol > 25000000:
                    valid_coins.append({
                        'symbol': sym, 
                        'change': float(t['priceChangePercent']), 
                        'volume': vol
                    })

        # टॉप 15 इनफ्लो (गेनर्स) और टॉप 15 आउटफ्लो (लूजर्स)
        top_crypto_inflow = sorted(valid_coins, key=lambda x: x['change'], reverse=True)[:15]
        top_crypto_outflow = sorted(valid_coins, key=lambda x: x['change'])[:15]

        crypto_trades = []
        for c in top_crypto_inflow:
            res = check_crypto_15m_entry(c['symbol'], "INFLOW")
            if res: crypto_trades.append(res)
            time.sleep(0.04)

        for c in top_crypto_outflow:
            res = check_crypto_15m_entry(c['symbol'], "OUTFLOW")
            if res: crypto_trades.append(res)
            time.sleep(0.04)

        if crypto_trades:
            msg = f"🔥 *CRYPTO BIG PLAYER 15M SNIPER ALERTS* 🔥\n━━━━━━━━━━━━━━━━━━━━━\n"
            for t in crypto_trades:
                msg += (f"🪙 *COIN:* `#{t['symbol']}`\n"
                        f"📊 *ACTION:* {t['action']}\n"
                        f"🕯 *PATTERN:* `{t['pattern']}`\n"
                        f"-----------------------------------\n"
                        f"📌 *EXACT ENTRY:* `{t['entry']}`\n"
                        f"⛔ *STOP-LOSS:* `{t['sl']}`\n"
                        f"-----------------------------------\n"
                        f"🎯 *TARGETS:*\n"
                        f"├ 🎯 *TP1 (1:2 RR):* `{t['tp1']}`\n"
                        f"└ 🎯 *TP2 (1:4 RR):* `{t['tp2']}`\n"
                        f"-----------------------------------\n"
                        f"🔗 [Open Binance](https://www.binance.com/en/futures/{t['symbol']})\n\n")
            send_msg(msg)
            print("✅ Crypto Signals Sent to Telegram!", flush=True)
        else:
            print("Scan finished: Awaiting fresh 15M institutional candle confirmation.", flush=True)

    except Exception as e:
        print(f"Error in scan: {e}", flush=True)

# 1. Startup Notification
send_msg("🚀 *Pure Crypto Flow Sniper Live!*\nScanning Top 30 High-Movement Coins 24/7 on 15M Institutional Setups.")

# 2. Continuous 15-Minute Loop
while True:
    run_crypto_scanner()
    time.sleep(900)
