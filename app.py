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
    values = data.get('values', [])
    if len(values) < 21: return None
    
    closes = [float(x['close']) for x in values][::-1]
    opens = [float(x['open']) for x in values][::-1]

    # 1. CALCUL RSI (Période 14)
    period = 14
    changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [x if x > 0 else 0 for x in changes]
    losses = [-x if x < 0 else 0 for x in changes]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    rsi = 100 - (100 / (1 + (avg_gain / (avg_loss if avg_loss != 0 else 1))))

    # 2. MÉCANIQUE DE CONFIRMATION (Couleur de la dernière bougie)
    is_green = closes[-1] > opens[-1]
    is_red = closes[-1] < opens[-1]

    return {
        "rsi": round(rsi, 2),
        "is_green": is_green,
        "is_red": is_red
    }

async def signal_scanner():
    try:
        bot.send_message(MY_CHAT_ID, "✅ **SCANNER OPTIMISÉ (25/75)**\n\nRecherche de signaux avec confirmation de bougie en cours...")
    except: pass

    while True:
        for pair in PAIRS:
            try:
                url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=30&apikey={API_KEY}"
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if "values" in data:
                    res = analyze_pro_logic(data)
                    if not res: continue

                    # LOGIQUE D'ENTRÉE AMÉLIORÉE
                    if res["rsi"] <= 25 and res["is_green"]:
                        bot.send_message(MY_CHAT_ID, f"🟢 **ACHAT (BUY)**\n📊 Paire: {pair}\n🔥 RSI: {res['rsi']}\n🕯 Bougie: Confirmation Verte ✅")

                    elif res["rsi"] >= 75 and res["is_red"]:
                        bot.send_message(MY_CHAT_ID, f"🔴 **VENTE (SELL)**\n📊 Paire: {pair}\n🔥 RSI: {res['rsi']}\n🕯 Bougie: Confirmation Rouge ✅")
                    
                    print(f"Scan {pair}: RSI {res['rsi']} | Bougie OK") # Log de contrôle
                
                await asyncio.sleep(15) # Protection API
            except Exception as e:
                print(f"Erreur sur {pair}: {e}")
                await asyncio.sleep(10)
        
        await asyncio.sleep(20)

# Serveur Flask pour Render
server = Flask('')
@server.route('/')
def home(): return "Scanner Pro 25/75 Online"

def run_flask():
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    asyncio.run(signal_scanner())
    
