import os
import asyncio
import telebot
import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask
from threading import Thread
from datetime import datetime

# ==========================================
# CONFIGURATION ELITE V13 - FINAL SNIPER
# ==========================================
TOKEN = "8770729734:AAGlXZov9BewOgPBh77jqumPtUSi_yW9bfI"
MY_CHAT_ID = 7259801083
TWELVE_DATA_API = "5f9db9ff50e4417da0416ee8c1b0bc2c"
MARKETAUX_API = "R3SLBCzBtMXumR33sMlndbqXe1CavD9RC2MsCl9v"

bot = telebot.TeleBot(TOKEN)

# 10 Actifs de Haute Qualité (Marché Réel)
PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "AUD/USD", 
    "GBP/JPY", "USD/CAD", "AUD/JPY", "EUR/GBP", "NZD/USD"
]

last_signal_min = {}

# ==========================================
# FONCTIONS TECHNIQUES & FILTRES
# ==========================================

def get_market_sentiment(pair):
    """Analyse du sentiment MarketAux pour filtrer les faux signaux"""
    symbol = pair.replace("/", "")
    url = f"https://api.marketaux.com/v1/news/all?symbols={symbol}&filter_entities=true&api_token={MARKETAUX_API}"
    try:
        res = requests.get(url, timeout=5).json()
        if "data" not in res or not res["data"]:
            return "NEUTRAL"
        
        pos, neg = 0, 0
        for item in res["data"]:
            s = item.get("sentiment")
            if s == "positive": pos += 1
            elif s == "negative": neg += 1
        
        if pos > neg: return "POSITIVE"
        if neg > pos: return "NEGATIVE"
        return "NEUTRAL"
    except:
        return "NEUTRAL"

def analyze_price_action(df):
    """Détection de Rejet (Mèche) et RSI Wilder"""
    # Calcul RSI Wilder (Période 14) - Identique Quotex
    df['rsi'] = ta.rsi(df['close'], length=14)
    
    last = df.iloc[-1]
    
    # Calcul du corps et des mèches
    body = abs(last['close'] - last['open'])
    if body == 0: body = 0.00001
    upper_wick = last['high'] - max(last['close'], last['open'])
    lower_wick = min(last['close'], last['open']) - last['low']
    
    # Détection de rejet (1.5x le corps minimum)
    bullish_rej = lower_wick > (body * 1.5)
    bearish_rej = upper_wick > (body * 1.5)
    
    return {
        "rsi": round(last['rsi'], 2),
        "price": last['close'],
        "bullish_rej": bullish_rej,
        "bearish_rej": bearish_rej,
        "is_green": last['close'] > last['open'],
        "is_red": last['close'] < last['open']
    }

async def scanner_engine():
    bot.send_message(MY_CHAT_ID, "✅ **ELITE V13 SNIPER OPÉRATIONNEL**\n\n- Filtre : Rejet Mèche + Sentiment News\n- RSI : 30/70 (Wilder)\n- Sync : UTC+0")

    while True:
        now = datetime.utcnow()
        
        # --- PHASE D'ANALYSE PRÉCISE ---
        if 25 <= now.second <= 52:
            for pair in PAIRS:
                try:
                    # Récupération des données 1min
                    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=30&apikey={TWELVE_DATA_API}"
                    response = requests.get(url, timeout=5).json()
                    
                    if "values" not in response: continue
                    
                    df = pd.DataFrame(response['values'])
                    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].apply(pd.to_numeric)
                    df = df.iloc[::-1] # Remettre dans l'ordre chronologique
                    
                    res = analyze_price_action(df)
                    
                    # 1. PRÉPARATION (:25 - :35)
                    if 25 <= now.second <= 35:
                        if (res["rsi"] <= 33 or res["rsi"] >= 67) and last_signal_min.get(pair) != now.minute:
                            bot.send_message(MY_CHAT_ID, 
                                f"⚠️ **PRÉPARATION**\n📊 Actif: {pair}\n💵 Prix: {res['price']}\n🔥 RSI: {res['rsi']}")
                            last_signal_min[pair] = now.minute

                    # 2. SIGNAL SNIPER FINAL (:45 - :52)
                    if 45 <= now.second <= 52:
                        sentiment = get_market_sentiment(pair)
                        
                        # --- LOGIQUE ACHAT (CALL) ---
                        if res["rsi"] <= 30 and (res["bullish_rej"] or res["is_green"]):
                            if sentiment != "NEGATIVE":
                                bot.send_message(MY_CHAT_ID, 
                                    f"🟢 **ENTREZ MAINTENANT (ACHAT)**\n\n"
                                    f"📊 Paire: {pair}\n"
                                    f"💵 Prix: {res['price']}\n"
                                    f"🔥 RSI: {res['rsi']}\n"
                                    f"📰 News: {sentiment} ✅\n"
                                    f"⏰ Entrée: {now.hour:02}:{now.minute + 1 if now.minute < 59 else 0:02}:00 UTC+0\n"
                                    f"🎯 M1 Sniper")
                                await asyncio.sleep(8) # Évite les doublons

                        # --- LOGIQUE VENTE (PUT) ---
                        elif res["rsi"] >= 70 and (res["bearish_rej"] or res["is_red"]):
                            if sentiment != "POSITIVE":
                                bot.send_message(MY_CHAT_ID, 
                                    f"🔴 **ENTREZ MAINTENANT (VENTE)**\n\n"
                                    f"📊 Paire: {pair}\n"
                                    f"💵 Prix: {res['price']}\n"
                                    f"🔥 RSI: {res['rsi']}\n"
                                    f"📰 News: {sentiment} ✅\n"
                                    f"⏰ Entrée: {now.hour:02}:{now.minute + 1 if now.minute < 59 else 0:02}:00 UTC+0\n"
                                    f"🎯 M1 Sniper")
                                await asyncio.sleep(8)

                except Exception:
                    continue
        
        await asyncio.sleep(1)

# ==========================================
# DÉPLOYEMENT
# ==========================================
server = Flask('')
@server.route('/')
def home(): return "Bot Sniper V13 Online"

def run_flask():
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    asyncio.run(scanner_engine())
    
