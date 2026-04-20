import os
import asyncio
import telebot
import requests
from flask import Flask
from threading import Thread

# ==========================================
# CONFIGURATION PRO - AUTO_SCANNER_X
# ==========================================
TOKEN = "8770729734:AAGlXZov9BewOgPBh77jqumPtUSi_yW9bfI"
MY_CHAT_ID = 7259801083
API_KEY = "ecea24f4e4f8487a8d141a10966856e5" 

bot = telebot.TeleBot(TOKEN)

# Liste des paires pour un scan efficace
PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "AUD/USD"]

def calculate_rsi(prices, period=14):
    if len(prices) <= period: return 50
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [x if x > 0 else 0 for x in changes]
    losses = [-x if x < 0 else 0 for x in changes]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ==========================================
# SCANNER STRATÉGIE PRO (25/75)
# ==========================================
async def signal_scanner():
    try:
        bot.send_message(MY_CHAT_ID, "🚀 **AUTO SCANNER X : SYSTÈME PRO ACTIVÉ**\n\nScanner opérationnel. Analyse des marchés en cours...")
    except: pass

    while True:
        for pair in PAIRS:
            try:
                url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=30&apikey={API_KEY}"
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if "values" in data:
                    closes = [float(x['close']) for x in data['values']][::-1]
                    rsi = calculate_rsi(closes)
                    
                    if rsi <= 25: 
                        bot.send_message(MY_CHAT_ID, f"💎 **SIGNAL ACHAT**\n📊 {pair}\n⚡ RSI: {round(rsi, 2)}")
                    elif rsi >= 75: 
                        bot.send_message(MY_CHAT_ID, f"🔴 **SIGNAL VENTE**\n📊 {pair}\n⚡ RSI: {round(rsi, 2)}")
                
                # PAUSE DE SÉCURITÉ (15s) pour respecter ton plan TwelveData
                await asyncio.sleep(15)
                    
            except:
                await asyncio.sleep(10)
        
        await asyncio.sleep(30)

# ==========================================
# MAINTIEN DU SERVEUR RENDER
# ==========================================
server = Flask('')
@server.route('/')
def home(): return "Scanner Pro Online"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    server.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    asyncio.run(signal_scanner())
      
