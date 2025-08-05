import requests
import time
import tweepy
from textblob import TextBlob

# === CONFIGURATION ===
DEX_API_URL = "https://api.dexscreener.com/latest/dex/pairs/solana/"
PUMP_FUN_URL = "https://pump.fun/api/trending"  # hypothetical endpoint

LOW_MARKET_CAP_THRESHOLD = 5_000_000
LIQUIDITY_THRESHOLD = 100_000
VOLUME_THRESHOLD = 50_000

TELEGRAM_BOT_TOKEN = "7879579850:AAFULo4ke7-moFK2-lf-49QZPAu2ueBZfm4"
TELEGRAM_CHAT_ID = "6855585968"

API_KEY = 'your_twitter_api_key'
API_SECRET_KEY = 'your_twitter_api_secret_key'
ACCESS_TOKEN = 'your_twitter_access_token'
ACCESS_SECRET = 'your_twitter_access_secret_key'

auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload)

def track_twitter_mentions(keyword, count=100):
    tweets = tweepy.Cursor(api.search_tweets, q=keyword, lang="en", result_type="recent").items(count)
    positive, negative, neutral = 0, 0, 0
    for tweet in tweets:
        analysis = TextBlob(tweet.text)
        if analysis.sentiment.polarity > 0:
            positive += 1
        elif analysis.sentiment.polarity < 0:
            negative += 1
        else:
            neutral += 1
    if positive > negative:
        send_telegram(f"🚨 Positive sentiment detected for '{keyword}' on Twitter!")

def get_token_data_from_dex():
    response = requests.get(DEX_API_URL)
    if response.status_code != 200:
        return []
    try:
        return response.json().get("pairs", [])
    except:
        return []

def is_rugproof(pair):
    try:
        lp_locked = pair.get("liquidity", {}).get("lockStatus", "").lower() in ["locked", "true"]
        renounced = pair.get("info", {}).get("ownerRenounced", False)
        return lp_locked and renounced
    except:
        return False

def extract_telegram(pair):
    try:
        tg = pair.get("info", {}).get("telegram", "")
        return tg if tg else "N/A"
    except:
        return "N/A"

def track_solana_memecoins():
    pairs = get_token_data_from_dex()
    for pair in pairs:
        try:
            symbol = pair.get("baseToken", {}).get("symbol", "")
            name = pair.get("baseToken", {}).get("name", "")
            address = pair.get("pairAddress", "")
            liquidity = float(pair.get("liquidity", {}).get("usd", 0))
            volume = float(pair.get("volume", {}).get("h24", 0))
            price = float(pair.get("priceUsd", 0))
            market_cap = liquidity * price
            telegram_link = extract_telegram(pair)

            if (market_cap < LOW_MARKET_CAP_THRESHOLD and
                liquidity > LIQUIDITY_THRESHOLD and
                volume > VOLUME_THRESHOLD and
                is_rugproof(pair)):

                message = (
                    f"🧿 Solana Meme Alert\n"
                    f"Name: {name} ({symbol})\n"
                    f"Price: ${price:.6f}\n"
                    f"Liquidity: ${liquidity:,.0f}\n"
                    f"Volume 24h: ${volume:,.0f}\n"
                    f"Market Cap: ${market_cap:,.0f}\n"
                    f"Pair: https://dexscreener.com/solana/{address}\n"
                    f"Telegram: {telegram_link}"
                )
                send_telegram(message)
        except:
            continue

def check_pump_fun_trending():
    try:
        res = requests.get(PUMP_FUN_URL)
        trending = res.json().get("trending", [])
        for coin in trending[:5]:
            name = coin.get("name", "Unknown")
            symbol = coin.get("symbol", "")
            address = coin.get("address", "")
            msg = f"🚀 Pump.fun Trending: {name} ({symbol})\nhttps://pump.fun/{address}"
            send_telegram(msg)
    except:
        pass

if __name__ == "__main__":
    while True:
        track_solana_memecoins()
        check_pump_fun_trending()
        track_twitter_mentions("solana meme")
        time.sleep(300)