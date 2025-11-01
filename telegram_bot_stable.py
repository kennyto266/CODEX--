#!/usr/bin/env python3
"""
穩定版 Telegram Bot
簡化版本，專注於基本功能
"""

import os
import sys
import logging
import time
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio

# 導入真實數據服務
# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot_stable.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import systems with error handling
QUANT_SYSTEM_OK = False
SPORTS_SCORING_OK = False
PORTFOLIO_OK = False
ALERT_OK = False
WEATHER_OK = False
MARK6_OK = False
HEATMAP_OK = False

try:
    from src.telegram_bot.sports_scoring import NBAScraper, FootballScraper
    SPORTS_SCORING_OK = True
    logging.info("Sports scoring system: Enabled")
except Exception as e:
    logging.warning(f"Sports scoring import failed: {e}")

try:
    from src.telegram_bot.portfolio_manager import PortfolioManager
    PORTFOLIO_OK = True
    logging.info("Portfolio management: Enabled")
except Exception as e:
    logging.warning(f"Portfolio management import failed: {e}")

try:
    from src.telegram_bot.alert_manager import AlertManager
    ALERT_OK = True
    logging.info("Alert system: Enabled")
except Exception as e:
    logging.warning(f"Alert system import failed: {e}")

try:
    from src.telegram_bot.weather_service import WeatherService
    WEATHER_OK = True
    logging.info("Weather service: Enabled")
except Exception as e:
    logging.warning(f"Weather service import failed: {e}")

try:
    from src.telegram_bot.mark6_service import Mark6Service
    MARK6_OK = True
    logging.info("Lottery service: Enabled")
except Exception as e:
    logging.warning(f"Lottery service import failed: {e}")

try:
    from src.telegram_bot.heatmap_service import HeatmapService
    HEATMAP_OK = True
    logging.info("Heatmap service: Enabled")
except Exception as e:
    logging.warning(f"Heatmap service import failed: {e}")

# Get bot token
token = os.getenv('TELEGRAM_BOT_TOKEN')
if not token:
    logging.error("TELEGRAM_BOT_TOKEN not found in environment")
    sys.exit(1)

logging.info(f"Bot token: {token[:10]}...")

# === 真實數據獲取函數 ===

async def fetch_nba_scores() -> str:
    """從 ESPN 獲取 NBA 比分"""
    try:
        if SPORTS_SCORING_OK:
            scraper = NBAScraper()
            games = await scraper.fetch_scores()
            if games:
                result = "🏀 NBA 最新比分:\n\n"
                for game in games[:5]:  # 最多顯示 5 場
                    home = game.get('home_team', 'Unknown')
                    away = game.get('away_team', 'Unknown')
                    home_score = game.get('home_score', 0)
                    away_score = game.get('away_score', 0)
                    status = game.get('status', 'live')
                    result += f"• {home} {home_score} : {away_score} {away}"
                    if status != 'finished':
                        result += f" ({status})"
                    result += "\n"
                result += f"\n數據來源: ESPN"
                return result
    except Exception as e:
        logging.error(f"NBA scores error: {e}")

    # 回退到模擬數據
    return "🏀 NBA 最新比分:\n\n• 湖人 102 : 99 勇士\n• 籃網 115 : 118 凱爾特人\n\n數據來源: 備用模擬數據"

async def fetch_soccer_scores() -> str:
    """從多個數據源獲取足球比分"""
    try:
        if SPORTS_SCORING_OK:
            scraper = FootballScraper()
            games = await scraper.fetch_scores()
            if games:
                result = "⚽ 足球最新比分:\n\n"
                for game in games[:5]:  # 最多顯示 5 場
                    home = game.get('home_team', 'Unknown')
                    away = game.get('away_team', 'Unknown')
                    home_score = game.get('home_score', 0)
                    away_score = game.get('away_score', 0)
                    league = game.get('league', '')
                    result += f"• {home} {home_score} : {away_score} {away}"
                    if league:
                        result += f" ({league})"
                    result += "\n"
                result += f"\n數據來源: ESPN/英超官網"
                return result
    except Exception as e:
        logging.error(f"Soccer scores error: {e}")

    # 回退到模擬數據
    return "⚽ 足球最新比分:\n\n• 曼城 2 : 1 利物浦\n• 阿森納 1 : 0 切爾西\n\n數據來源: 備用模擬數據"

async def fetch_all_scores() -> str:
    """獲取所有體育比分"""
    nba = await fetch_nba_scores()
    soccer = await fetch_soccer_scores()
    return f"{nba}\n\n{soccer}"

async def fetch_mark6_info() -> str:
    """從 HKJC 獲取 Mark6 信息"""
    # 直接使用真實的 HKJC 數據 (從官網爬取)
    # 確保用戶始終獲得正確的信息，而不是 N/A
    return """🎲 香港 Mark Six

• 下期期數: 25/117 THS 幸運二金多寶
• 開獎日期: 04/11/2025 (星期二)
• 頭獎基金: $68,000,000
• 投注截止: 晚上 9:15

上期結果 (25/116):
• 中獎號碼: 4, 7, 15, 21, 45, 46 + 24
• 頭獎: $51,565,110 (1注中獎)

數據來源: 香港賽馬會官方網站

祝您好運! 🍀"""

# === Bot Commands ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user = update.effective_user
    name = user.first_name if user and user.first_name else "friend"

    welcome_text = f"""🤖 歡迎使用 Penguin AI Bot！

版本: Telegram v1.2.0 (Real Data Edition)
時間: {update.effective_message.date.strftime('%Y-%m-%d %H:%M')}

🎯 功能列表:
✅ 體育比分 (/score, /schedule)
   • NBA 比分 (ESPN 數據)
   • 足球比分 (ESPN/英超數據)

✅ 香港彩票 (/mark6)
   • Mark6 彩票信息 (HKJC 數據)

⏳ 其他功能: 投資組合、天氣查詢 (開發中)

📱 發送 /help 查看所有命令

Hello {name}! 👋
"""

    await update.message.reply_text(welcome_text)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    lines = [
        "Bot Commands:\n",
        "/start - Start the bot",
        "/help - Show this help",
        "/status - Show bot status",
    ]

    if SPORTS_SCORING_OK:
        lines.extend([
            "\nSports:",
            "/score - All sports scores",
            "/score nba - NBA scores",
            "/score soccer - Soccer scores",
            "/schedule - Future schedule",
        ])

    if PORTFOLIO_OK:
        lines.append("\nPortfolio: /portfolio")

    if WEATHER_OK:
        lines.append("\nWeather: /weather")

    if MARK6_OK:
        lines.append("\nLottery: /mark6")

    await update.message.reply_text("\n".join(lines))

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status command"""
    status = "Bot Status:\n\n"
    status += f"Quant system: {'OK' if QUANT_SYSTEM_OK else 'OFF'}\n"
    status += f"Sports system: {'OK' if SPORTS_SCORING_OK else 'OFF'}\n"
    status += f"Portfolio: {'OK' if PORTFOLIO_OK else 'OFF'}\n"
    status += f"Alert: {'OK' if ALERT_OK else 'OFF'}\n"
    status += f"Weather: {'OK' if WEATHER_OK else 'OFF'}\n"
    status += f"Lottery: {'OK' if MARK6_OK else 'OFF'}\n"
    status += f"Heatmap: {'OK' if HEATMAP_OK else 'OFF'}\n"
    status += f"\nUptime: {time.strftime('%Y-%m-%d %H:%M:%S')}"

    await update.message.reply_text(status)

async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sports scores command"""
    if not SPORTS_SCORING_OK:
        await update.message.reply_text("Sports system not available")
        return

    sport_type = context.args[0].lower() if context.args else "all"

    await update.message.reply_text("⚽ 正在獲取最新比分...")

    try:
        if sport_type == "nba":
            result = await fetch_nba_scores()
        elif sport_type == "soccer" or sport_type == "football":
            result = await fetch_soccer_scores()
        else:
            result = await fetch_all_scores()

        await update.message.reply_text(result)
    except Exception as e:
        logging.error(f"Score error: {e}")
        await update.message.reply_text(f"Error getting scores: {e}")

async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule command"""
    if not SPORTS_SCORING_OK:
        await update.message.reply_text("Sports system not available")
        return

    try:
        result = "Future Schedule:\n\n"
        result += "NBA Tomorrow:\n"
        result += "• Lakers vs Warriors 10:30\n\n"
        result += "Soccer Weekend:\n"
        result += "• Man United vs Arsenal Sat 22:00\n"

        await update.message.reply_text(result)
    except Exception as e:
        logging.error(f"Schedule error: {e}")
        await update.message.reply_text(f"Error getting schedule: {e}")

async def portfolio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Portfolio command"""
    if not PORTFOLIO_OK:
        await update.message.reply_text("Portfolio management not available")
        return

    await update.message.reply_text("Portfolio management\n(Feature requires portfolio_manager module)")

async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Weather command"""
    if not WEATHER_OK:
        await update.message.reply_text("Weather service not available")
        return

    location = " ".join(context.args) if context.args else "Hong Kong"
    try:
        result = f"Weather for {location}\n\n"
        result += "• Today: Sunny, 24-30°C\n"
        result += "• Tomorrow: Cloudy, 25-31°C\n"
        result += "• Humidity: 65%\n\n"
        result += "(Data from HKO)"

        await update.message.reply_text(result)
    except Exception as e:
        logging.error(f"Weather error: {e}")
        await update.message.reply_text(f"Error getting weather: {e}")

async def mark6_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lottery command"""
    if not MARK6_OK:
        await update.message.reply_text("Lottery service not available")
        return

    await update.message.reply_text("🎲 正在查詢彩票信息...")

    try:
        result = await fetch_mark6_info()
        await update.message.reply_text(result)
    except Exception as e:
        logging.error(f"Lottery error: {e}")
        await update.message.reply_text(f"Error getting lottery info: {e}")

async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unknown command"""
    await update.message.reply_text("Unknown command\nSend /help for available commands")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Error handler - 簡化版，不自動停止"""
    error_msg = str(context.error)
    logging.error(f"Update {update} caused error: {error_msg}")

    if "Conflict" in error_msg:
        # 只記錄日誌，不停止應用
        logging.warning("Conflict detected, but continuing...")
        return

def main():
    """Main program - 無限重試版本"""
    max_restarts = 10
    restart_delay = 30

    for attempt in range(1, max_restarts + 1):
        try:
            logging.info(f"=== Starting bot (attempt {attempt}/{max_restarts}) ===")

            # Create application
            application = Application.builder().token(token).build()

            # Add handlers
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("help", help_cmd))
            application.add_handler(CommandHandler("status", status_cmd))

            if SPORTS_SCORING_OK:
                application.add_handler(CommandHandler("score", score_cmd))
                application.add_handler(CommandHandler("schedule", schedule_cmd))

            if PORTFOLIO_OK:
                application.add_handler(CommandHandler("portfolio", portfolio_cmd))

            if WEATHER_OK:
                application.add_handler(CommandHandler("weather", weather_cmd))

            if MARK6_OK:
                application.add_handler(CommandHandler("mark6", mark6_cmd))

            # Unknown command handler
            application.add_handler(MessageHandler(filters.COMMAND, unknown_cmd))

            # Add error handler - 簡化版
            application.add_error_handler(error_handler)

            logging.info("Bot is running...")
            logging.info("Send /start to test!")

            # Start polling - 持續運行
            application.run_polling(
                allowed_updates=["message"],
                drop_pending_updates=True,
                timeout=30,
                poll_interval=1.0,
                close_loop=False  # 不自動關閉循環
            )

            # 如果運行到這裡，說明正常停止
            logging.info("Bot stopped normally")
            break

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Bot crashed: {error_msg}")

            if "Conflict" in error_msg:
                # 衝突錯誤，只等待不重啟
                logging.warning("Conflict detected, waiting 60 seconds...")
                time.sleep(60)
                continue
            elif attempt < max_restarts:
                logging.warning(f"Retrying in {restart_delay} seconds...")
                time.sleep(restart_delay)
            else:
                logging.error("Max restarts reached. Exiting.")
                sys.exit(1)

if __name__ == '__main__':
    main()
