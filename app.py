import os
import asyncio
import telebot
import requests
from flask import Flask
from threading import Thread

# ==========================================
# CONFIGURATION PRO - AUTO_SCANNER_X_ELITE
# ==========================================
TOKEN = "8770729734:AAGlXZov9BewOgPBh77jqumPtUSi_yW9bfI"
MY_CHAT_ID = 7259801083
API_KEY = "5f9db9ff50e4417da0416ee8c1b0bc2c" 

bot = telebot.TeleBot(TOKEN)

# Liste complète basée sur tes captures Quotex
PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "EUR/GBP", 
    "AUD/USD", "AUD/CAD", "CAD/JPY", "AUD/CHF", "GBP/AUD", 
    "AUD/JPY", "EUR/CHF", "CHF/JPY", "GBP/CHF", "GBP/JPY",
    "EUR/AUD", "EUR/CAD", "USD/CAD", "GBP/CAD", "USD/CHF"
]

def analyze_pro_logic(data):
    values = data.get('values', [])
    if len(values) < 21: return None
    
    closes = [float(x['close']) for x in values][::-1]
    opens = [float(x['open']) for x in values][::-1]

    period = 14
    changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [x if x > 0 else 0 for x in changes]
    losses = [-x if x < 0 else 0 for x in changes]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0: return {"rsi": 100, "is_green": False, "is_red": False, "price": closes[-1]}
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    is_green = closes[-1] > opens[-1]
    is_red = closes[-1] < opens[-1]

    return {
        "rsi": round(rsi, 2),
        "is_green": is_green,
        "is_red": is_red,
        "price": closes[-1]
    }

async def signal_scanner():
    try:
        bot.send_message(MY_CHAT_ID, f"🛡️ **SCANNER MULTI-ACTIFS ACTIVÉ**\n\nSurveillance de {len(PAIRS)} paires en cours.\nStratégie: Anticipation (30/70) + Sniper (25/75)")
    except: pass

    while True:
        for pair in PAIRS:
            try:
                url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=30&apikey={API_KEY}"
                response = requests.get(url, timeout=15)
                data = response.json()
                
                if data.get("status") == "error":
                    # Si limite atteinte, on attend plus longtemps
                    await asyncio.sleep(30) 
                    continue

                if "values" in data:
                    res = analyze_pro_logic(data)
                    if not res: continue

                    # --- 1. PRÉPARATION (Pour avoir le temps d'ouvrir Quotex) ---
                    if 25 < res["rsi"] <= 30:
                        bot.send_message(MY_CHAT_ID, f"⚠️ **PRÉPARATION ACHAT**\n📊 {pair}\n📉 RSI: {res['rsi']}\n👀 Ouvrez l'actif sur Quotex...")
                    
                    elif 70 <= res["rsi"] < 75:
                        bot.send_message(MY_CHAT_ID, f"⚠️ **PRÉPARATION VENTE**\n📊 {pair}\n📈 RSI: {res['rsi']}\n👀 Ouvrez l'actif sur Quotex...")

                    # --- 2. SIGNAL D'ENTRÉE (Confirmation M1) ---
                    if res["rsi"] <= 25 and res["is_green"]:
                        bot.send_message(MY_CHAT_ID, f"🟢 **ENTREZ MAINTENANT (ACHAT)**\n📊 Paire: {pair}\n💵 Prix: {res['price']}\n🔥 RSI: {res['rsi']}\n🎯 Expiration: 1 min (UTC+0)")

                    elif res["rsi"] >= 75 and res["is_red"]:
                        bot.send_message(MY_CHAT_ID, f"🔴 **ENTREZ MAINTENANT (VENTE)**\n📊 Paire: {pair}\n💵 Prix: {res['price']}\n🔥 RSI: {res['rsi']}\n🎯 Expiration: 1 min (UTC+0)")
                
                # Pause courte pour scanner toute la liste rapidement sans bloquer l'API
                await asyncio.sleep(8) 
            except Exception as e:
                await asyncio.sleep(5)
        
        await asyncio.sleep(10)

server = Flask('')
@server.route('/')
def home(): return "Scanner Multi-Actifs Online"

def run_flask():
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    asyncio.run(signal_scanner())
                
