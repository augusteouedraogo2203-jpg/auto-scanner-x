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
API_KEY = "5f9db9ff50e4417da0416ee8c1b0bc2c" # Ta nouvelle clé API TwelveData

bot = telebot.TeleBot(TOKEN)
PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "AUD/USD"]

def analyze_pro_logic(data):
    values = data.get('values', [])
    if len(values) < 21: return None
    
    # Inversion pour avoir les données chronologiques (plus récent à la fin)
    closes = [float(x['close']) for x in values][::-1]
    opens = [float(x['open']) for x in values][::-1]

    # 1. CALCUL RSI (Période 14)
    period = 14
    changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [x if x > 0 else 0 for x in changes]
    losses = [-x if x < 0 else 0 for x in changes]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0: return {"rsi": 100, "is_green": False, "is_red": False}
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # 2. MÉCANIQUE DE CONFIRMATION (Couleur de la dernière bougie clôturée)
    # C'est la mécanique qui donne de vrais résultats
    is_green = closes[-1] > opens[-1]
    is_red = closes[-1] < opens[-1]

    return {
        "rsi": round(rsi, 2),
        "is_green": is_green,
        "is_red": is_red
    }

async def signal_scanner():
    try:
        bot.send_message(MY_CHAT_ID, "🛡️ **SYSTÈME ÉLITE OPÉRATIONNEL**\n\nClé API mise à jour. Analyse RSI 25/75 + Confirmation active.")
    except: pass

    while True:
        for pair in PAIRS:
            try:
                # Appel avec ta nouvelle API KEY
                url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=30&apikey={API_KEY}"
                response = requests.get(url, timeout=15)
                data = response.json()
                
                # Gestion des limites TwelveData
                if data.get("status") == "error":
                    print(f"Alerte API: {data.get('message')}")
                    await asyncio.sleep(60) 
                    continue

                if "values" in data:
                    res = analyze_pro_logic(data)
                    if not res: continue

                    # --- STRATÉGIE DE CONFLUENCE ---
                    # Signal d'achat : RSI bas ET bougie de retournement verte
                    if res["rsi"] <= 25 and res["is_green"]:
                        bot.send_message(MY_CHAT_ID, f"🟢 **SIGNAL ACHAT**\n📊 Paire: {pair}\n🔥 RSI: {res['rsi']}\n🕯 Bougie: Confirmée Verte ✅\n🎯 Expiration conseillée: 1-2 min")

                    # Signal de vente : RSI haut ET bougie de retournement rouge
                    elif res["rsi"] >= 75 and res["is_red"]:
                        bot.send_message(MY_CHAT_ID, f"🔴 **SIGNAL VENTE**\n📊 Paire: {pair}\n🔥 RSI: {res['rsi']}\n🕯 Bougie: Confirmée Rouge ✅\n🎯 Expiration conseillée: 1-2 min")
                    
                    print(f"Scan {pair}: RSI {res['rsi']}") 
                
                # Pause de sécurité pour le plan gratuit
                await asyncio.sleep(15) 
            except Exception as e:
                print(f"Erreur: {e}")
                await asyncio.sleep(10)
        
        await asyncio.sleep(20)

# Serveur Flask pour maintenir Render éveillé
server = Flask('')
@server.route('/')
def home(): return "Scanner Pro V3 Online"

def run_flask():
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    asyncio.run(signal_scanner())
    
