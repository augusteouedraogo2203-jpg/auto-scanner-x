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
API_KEY = "ecea24f4e4f8487a8d141a10966856e5" 

bot = telebot.TeleBot(TOKEN)
PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "AUD/USD"]

def analyze_pro_logic(data):
    closes = [float(x['close']) for x in data['values']][::-1]
    opens = [float(x['open']) for x in data['values']][::-1]

    # 1. CALCUL RSI (Période 14)
    period = 14
    if len(closes) < period + 1: return None
    changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [x if x > 0 else 0 for x in changes]
    losses = [-x if x < 0 else 0 for x in changes]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    rsi = 100 - (100 / (1 + (avg_gain / (avg_loss if avg_loss != 0 else 1))))

    # 2. MÉCANIQUE "GET_COLOR" (Confirmation par la bougie actuelle)
    # On vérifie si la bougie en cours est en train de se retourner
    last_close = closes[-1]
    last_open = opens[-1]
    is_green = last_close > last_open  # Confirmation pour ACHAT
    is_red = last_close < last_open    # Confirmation pour VENTE

    # 3. FILTRE DE TENDANCE (Moyenne Mobile simple 20 pour le flux)
    sma_20 = sum(closes[-20:]) / 20

    return {
        "rsi": round(rsi, 2),
        "is_green": is_green,
        "is_red": is_red,
        "price": last_close,
        "sma_20": sma_20
    }

async def signal_scanner():
    try:
        bot.send_message(MY_CHAT_ID, "🎯 **MODE SNIPER ACTIVÉ (RSI 20/80)**\n\nAttente de zones extrêmes avec confirmation de bougie...")
    except: pass

    while True:
        for pair in PAIRS:
            try:
                # On demande un peu plus de données (40) pour calculer la SMA 20 correctement
                url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=40&apikey={API_KEY}"
                data = requests.get(url, timeout=10).json()
                
                if "values" in data:
                    res = analyze_pro_logic(data)
                    if not res: continue

                    # --- LOGIQUE D'ACHAT (BUY) ---
                    # RSI < 20 + Bougie Verte + Prix commence à repasser au-dessus ou proche SMA
                    if res["rsi"] <= 20 and res["is_green"]:
                        bot.send_message(MY_CHAT_ID, f"🟢 **SIGNAL ACHAT SNIPER**\n📊 Asset: {pair}\n🔥 RSI: {res['rsi']}\n🕯 Bougie: Confirmée Verte\n⚖️ Statut: Zone de rebond")

                    # --- LOGIQUE DE VENTE (SELL) ---
                    # RSI > 80 + Bougie Rouge
                    elif res["rsi"] >= 80 and res["is_red"]:
                        bot.send_message(MY_CHAT_ID, f"🔴 **SIGNAL VENTE SNIPER**\n📊 Asset: {pair}\n🔥 RSI: {res['rsi']}\n🕯 Bougie: Confirmée Rouge\n⚖️ Statut: Zone de rejet")
                
                await asyncio.sleep(15) # Respect du quota TwelveData
            except:
                await asyncio.sleep(10)
        await asyncio.sleep(20)

# Serveur pour Render
server = Flask('')
@server.route('/')
def home(): return "Scanner Elite 20/80 Online"

def run_flask():
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(signal_scanner())
    
