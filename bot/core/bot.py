"""
Boter 2.0 - Bot Application Factory
Creates and configures the python-telegram-bot Application
"""
import logging

from telegram.ext import Application

from db.models import BotConfig

logger = logging.getLogger("boter.bot")


async def create_bot_application(config: BotConfig) -> Application:
    """Create and configure the Telegram bot application"""

    # Build application
    app = (
        Application.builder()
        .token(config.bot_token)
        .concurrent_updates(True)
        .build()
    )

    # Store config in bot_data for access in handlers
    app.bot_data["config"] = config

    # Register all handlers
    _register_handlers(app)

    logger.info("Bot application created successfully")
    return app


def _register_handlers(app: Application):
    """Register all handler modules"""
    from bot.handlers.start import register_start_handlers
    from bot.handlers.support.forward import register_forward_handlers
    from bot.handlers.support.reply import register_reply_handlers
    from bot.handlers.support.block import register_block_handlers
    from bot.handlers.admin.manage import register_admin_handlers
    from bot.handlers.admin.settings import register_settings_handlers
    from bot.handlers.antispam.media_filter import register_media_filter_handlers
    from bot.handlers.antispam.word_filter import register_word_filter_handlers
    from bot.handlers.antispam.lock import register_lock_handlers
    from bot.handlers.antispam.welcome import register_welcome_handlers
    from bot.handlers.antispam.rules import register_rules_handlers
    from bot.handlers.antispam.words import register_words_handlers

    register_start_handlers(app)
    register_forward_handlers(app)
    register_reply_handlers(app)
    register_block_handlers(app)
    register_admin_handlers(app)
    register_settings_handlers(app)
    register_media_filter_handlers(app)
    register_word_filter_handlers(app)
    register_lock_handlers(app)
    register_welcome_handlers(app)
    register_rules_handlers(app)
    register_words_handlers(app)

    logger.info("All handlers registered")
