"""MAMA CHOL VPN Telegram Bot."""
import logging
import asyncio
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import httpx
from backend.config.settings import settings

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

API_BASE = settings.app_url + "/api/v1"

MESSAGES = {
    "en": {
        "welcome": "👋 Welcome to *MAMA CHOL VPN* bot!\n\nI can help you manage your VPN subscription.\n\nUse /help to see available commands.",
        "help": """📋 *Available Commands*

/start — Welcome message
/status — Check your subscription status
/config — Get your VPN configuration
/usage — View data usage
/support — Contact support
/language — Change language

💬 You can also ask me anything about MAMA CHOL VPN!""",
        "not_linked": "⚠️ Your Telegram account is not linked to any MAMA CHOL VPN account.\n\nVisit mamachol.online → Dashboard → Settings to link your Telegram.",
        "status_active": "✅ *Subscription Active*\n\nPlan: {plan}\nExpires: {expiry}\nData used: {data_used} / {data_limit}",
        "status_expired": "❌ *Subscription Expired*\n\nRenew your plan at mamachol.online/dashboard/payments",
        "config_header": "🔗 *Your VPN Configuration*\n\nUse the buttons below to get your config links:",
        "language_select": "🌐 Select your language:",
        "support_msg": "📞 *Contact Support*\n\n• Email: support@mamachol.online\n• Telegram: @mamacholsupport\n• Dashboard: mamachol.online/dashboard/support\n\nOr describe your issue here and I'll try to help!",
        "ai_error": "Sorry, I couldn't get a response from AI. Please try again or contact support.",
    },
    "bn": {
        "welcome": "👋 *MAMA CHOL VPN* বটে স্বাগতম!\n\nআমি আপনার VPN সাবস্ক্রিপশন পরিচালনায় সাহায্য করতে পারি।\n\n/help দিয়ে কমান্ড দেখুন।",
        "help": """📋 *কমান্ড সমূহ*

/start — স্বাগত বার্তা
/status — সাবস্ক্রিপশন স্ট্যাটাস
/config — VPN কনফিগারেশন
/usage — ডেটা ব্যবহার
/support — সাপোর্ট
/language — ভাষা পরিবর্তন""",
        "not_linked": "⚠️ আপনার টেলিগ্রাম MAMA CHOL VPN অ্যাকাউন্টের সাথে যুক্ত নয়।\n\nmamachol.online → Dashboard → Settings এ যান।",
        "status_active": "✅ *সাবস্ক্রিপশন সক্রিয়*\n\nপ্ল্যান: {plan}\nমেয়াদ: {expiry}\nডেটা: {data_used} / {data_limit}",
        "support_msg": "📞 *সাপোর্ট*\n\n• ইমেইল: support@mamachol.online\n• টেলিগ্রাম: @mamacholsupport",
    },
    "zh": {
        "welcome": "👋 欢迎使用 *MAMA CHOL VPN* 机器人！\n\n我可以帮您管理VPN订阅。\n\n使用 /help 查看可用命令。",
        "help": """📋 *可用命令*

/start — 欢迎消息
/status — 查看订阅状态
/config — 获取VPN配置
/usage — 查看流量使用
/support — 联系支持
/language — 切换语言""",
        "not_linked": "⚠️ 您的Telegram账户尚未与MAMA CHOL VPN账户关联。\n\n请访问 mamachol.online → 控制台 → 设置 进行关联。",
        "status_active": "✅ *订阅有效*\n\n套餐: {plan}\n到期时间: {expiry}\n已用流量: {data_used} / {data_limit}",
        "support_msg": "📞 *联系支持*\n\n• 邮箱: support@mamachol.online\n• Telegram: @mamacholsupport",
    },
}


def get_message(lang: str, key: str, **kwargs) -> str:
    msg = MESSAGES.get(lang, MESSAGES["en"]).get(key) or MESSAGES["en"].get(key, "")
    return msg.format(**kwargs) if kwargs else msg


def get_user_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", "en")


async def fetch_api(endpoint: str, token: str) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{API_BASE}{endpoint}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.error(f"API request failed: {e}")
    return None


async def get_user_token_by_telegram_id(telegram_id: str) -> Optional[str]:
    """Get API token for a Telegram user. In production, store in DB."""
    return None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(context)
    keyboard = [
        [InlineKeyboardButton("🌐 English", callback_data="lang_en"),
         InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn")],
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh"),
         InlineKeyboardButton("🇮🇳 हिंदी", callback_data="lang_hi")],
        [InlineKeyboardButton("📊 Dashboard", url="https://mamachol.online/dashboard"),
         InlineKeyboardButton("💰 Pricing", url="https://mamachol.online/#pricing")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        get_message(lang, "welcome"),
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(context)
    await update.message.reply_text(get_message(lang, "help"), parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(context)
    telegram_id = str(update.effective_user.id)
    token = await get_user_token_by_telegram_id(telegram_id)

    if not token:
        await update.message.reply_text(get_message(lang, "not_linked"), parse_mode="Markdown")
        return

    data = await fetch_api("/user/dashboard", token)
    if data and data.get("plan_active"):
        msg = get_message(
            lang, "status_active",
            plan=data.get("plan", "").title(),
            expiry=data.get("expires_at", "N/A")[:10],
            data_used=f"{data.get('data_used_gb', 0):.1f} GB",
            data_limit=f"{data.get('data_limit_gb') or '∞'} GB"
        )
    else:
        msg = get_message(lang, "status_expired")

    keyboard = [[InlineKeyboardButton("💳 Renew Plan", url="https://mamachol.online/dashboard/payments")]]
    await update.message.reply_text(
        msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(context)
    telegram_id = str(update.effective_user.id)
    token = await get_user_token_by_telegram_id(telegram_id)

    if not token:
        await update.message.reply_text(get_message(lang, "not_linked"), parse_mode="Markdown")
        return

    keyboard = [
        [InlineKeyboardButton("📱 Get QR Code", url="https://mamachol.online/dashboard/config"),
         InlineKeyboardButton("📋 Copy Link", url="https://mamachol.online/dashboard/config")],
    ]
    await update.message.reply_text(
        get_message(lang, "config_header"),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📊 View Full Dashboard", url="https://mamachol.online/dashboard")]]
    await update.message.reply_text(
        "📊 View your detailed usage at the dashboard:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(context)
    await update.message.reply_text(get_message(lang, "support_msg"), parse_mode="Markdown")


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
         InlineKeyboardButton("🇧🇩 বাংলা", callback_data="lang_bn")],
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh"),
         InlineKeyboardButton("🇮🇳 हिंदी", callback_data="lang_hi")],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar")],
    ]
    await update.message.reply_text(
        get_message("en", "language_select"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("lang_"):
        lang = query.data.replace("lang_", "")
        if lang in ["en", "bn", "zh", "hi", "ar"]:
            context.user_data["lang"] = lang
            lang_names = {"en": "English", "bn": "বাংলা", "zh": "中文", "hi": "हिंदी", "ar": "العربية"}
            await query.edit_message_text(f"✅ Language set to {lang_names.get(lang, lang)}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages with AI."""
    lang = get_user_lang(context)
    user_message = update.message.text

    await update.message.chat.send_action("typing")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{API_BASE}/chat",
                json={"message": user_message, "lang": lang}
            )
            if resp.status_code == 200:
                data = resp.json()
                await update.message.reply_text(data.get("reply", get_message(lang, "ai_error")))
                return
    except Exception as e:
        logger.error(f"AI chat failed: {e}")

    await update.message.reply_text(get_message(lang, "ai_error"))


async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to get stats."""
    if str(update.effective_user.id) != settings.telegram_admin_chat_id:
        await update.message.reply_text("⛔ Admin only command")
        return
    await update.message.reply_text(
        "📊 Admin stats available at: https://mamachol.online/admin"
    )


def create_bot() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("config", config_command))
    app.add_handler(CommandHandler("usage", usage_command))
    app.add_handler(CommandHandler("support", support_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("stats", admin_stats_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app


if __name__ == "__main__":
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment")
        exit(1)
    bot = create_bot()
    logger.info("Starting MAMA CHOL VPN Telegram Bot...")
    bot.run_polling(allowed_updates=Update.ALL_TYPES)
