import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import aiohttp

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Constants for Public Data Sources ---
COINGECKO_API = "https://api.coingecko.com/api/v3"
COINGECKO_PRICE = f"{COINGECKO_API}/simple/price"
COINGECKO_TRENDING = f"{COINGECKO_API}/search/trending"
BINANCE_API = "https://api.binance.com/api/v3"
BINANCE_24H_TICKER = f"{BINANCE_API}/ticker/24hr"

# --- Helper Functions ---

async def get_bitcoin_price():
    """Fetch current BTC price in USD from CoinGecko."""
    params = {"ids": "bitcoin", "vs_currencies": "usd"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(COINGECKO_PRICE, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("bitcoin", {}).get("usd", "N/A")
                return None
        except Exception as e:
            logger.error(f"Price request failed: {e}")
            return None

async def get_trending_coins():
    """Get top trending coins from CoinGecko."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(COINGECKO_TRENDING) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    coins = data.get("coins", [])[:5]
                    names = [coin["item"]["name"] for coin in coins]
                    return ", ".join(names) if names else "Bitcoin, Ethereum, Solana"
                return "Bitcoin, Ethereum, Solana"
        except Exception:
            return "Bitcoin, Ethereum, Solana"

async def get_market_update():
    """Get a market summary from Binance public API."""
    params = {"symbol": "BTCUSDT"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(BINANCE_24H_TICKER, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    price = float(data.get("lastPrice", 0))
                    change = float(data.get("priceChangePercent", 0))
                    return f"💰 *BTC/USDT*: ${price:,.2f} (24h: {change:+.2f}%)"
                return "💰 BTC/USDT: Market data currently unavailable."
        except Exception:
            return "💰 BTC/USDT: Market data currently unavailable."

async def get_top_news():
    """Get a daily news digest."""
    trending = await get_trending_coins()
    news_items = [
        f"📰 *Today's Crypto Highlights*",
        f"🚀 *Trending Coins*: {trending}",
        f"💡 *Did you know?* Bitcoin's whitepaper was published on October 31, 2008.",
        f"📅 *Today's Date*: {datetime.now().strftime('%B %d, %Y')}",
    ]
    return "\n".join(news_items)

# --- Bot Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
    user = update.effective_user
    welcome_text = (
        f"Hello {user.first_name}! 👋\n\n"
        "I am *CryptoDaily*, your daily crypto briefing bot.\n"
        "I provide a simple, non-financial summary of the crypto world.\n\n"
        "📋 *Available Commands:*\n"
        "/start - Show this welcome message\n"
        "/help - Show available commands\n"
        "/daily - Get today's crypto news and price digest\n"
        "/price - Get current BTC price\n"
        "/trending - See what's trending on CoinGecko\n\n"
        "⚠️ *Disclaimer*: I am an educational bot. I do not give financial advice."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message."""
    help_text = (
        "🤖 *CryptoDaily Bot Help*\n\n"
        "/start - Show the welcome message\n"
        "/help - Show this help menu\n"
        "/daily - Get a crypto news and price digest\n"
        "/price - Get current Bitcoin price in USD\n"
        "/trending - Show top 5 trending coins\n\n"
        "📊 *Data Sources*:\n"
        "CoinGecko & Binance Public APIs (No API keys required)\n\n"
        "📌 *Note*: All data is for educational purposes only."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a daily digest of crypto news and prices."""
    await update.message.reply_text("📊 *Generating your daily crypto digest...*", parse_mode="Markdown")
    
    btc_price = await get_bitcoin_price()
    market_update = await get_market_update()
    news = await get_top_news()
    
    digest = (
        f"📆 *Crypto Daily Digest* - {datetime.now().strftime('%B %d, %Y')}\n\n"
        f"🔹 {market_update}\n"
        f"🔹 Current BTC Price: ${btc_price:,.2f} (if available)\n\n"
        f"{news}\n\n"
        f"✅ *Daily digest complete!*"
    )
    await update.message.reply_text(digest, parse_mode="Markdown")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the current BTC price."""
    await update.message.reply_text("⏳ *Fetching current BTC price...*", parse_mode="Markdown")
    btc_price = await get_bitcoin_price()
    if btc_price and btc_price != "N/A":
        await update.message.reply_text(f"💰 *Bitcoin (BTC) Price*: ${btc_price:,.2f} USD", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Could not fetch BTC price at this time. Please try again later.")

async def trending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the top 5 trending coins."""
    await update.message.reply_text("⏳ *Fetching trending coins...*", parse_mode="Markdown")
    trending_coins = await get_trending_coins()
    if trending_coins:
        await update.message.reply_text(f"🚀 *Top Trending Coins*:\n{trending_coins}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Could not fetch trending coins at this time.")

# --- Main Application ---

def main():
    """Start the bot using a clean event loop."""
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("daily", daily))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("trending", trending))

    # Run the bot
    print("🤖 CryptoDaily Bot is starting...")
    try:
        application.run_polling()
    finally:
        loop.close()

if __name__ == "__main__":
    main()
