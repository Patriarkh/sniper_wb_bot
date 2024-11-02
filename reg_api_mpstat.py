import logging
import asyncio

import pytz
import datetime

from telegram import Update
import settings
import aiosqlite
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from formirovanie_zaprosa import zapros_start, get_quantity_goods, get_otzyv, get_diapazon_revenue, cancel, init_db
from helpers import log_message
from every_day import check_for_new_items
from database_utils import init_db
from get_member import subscription_required

# Настройка логирования
logger = logging.getLogger(__name__)


# Константа для состояния
ENTER_API_KEY = 4

#Регистрация личного апи ключа мпстата
@subscription_required
async def register_api_key(update: Update, context: CallbackContext):
    await update.message.reply_text("Пожалуйста, введите ваш апи ключ мпстата:")
    return ENTER_API_KEY

# Обработка введенного API-ключа
async def save_api_key(update: Update, context: CallbackContext):
    logger.info("save_api_key вызван.")
    user_id = update.effective_user.id
    api_key = update.message.text  # Получаем API-ключ из сообщения

    # Сохраняем API-ключ в базе данных
    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        await db.execute('''
            INSERT INTO users (user_id, mpstats_api_key)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET mpstats_api_key = excluded.mpstats_api_key
        ''', (user_id, api_key))
        await db.commit()

    logger.info(f"API-ключ для пользователя {user_id} сохранен.")
    await update.message.reply_text("Ваш API-ключ успешно сохранен.\n\nДля формирования вашей базы данных введите /start_bot")
    return ConversationHandler.END




# Обработчик отменыs
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Регистрация API-ключа отменена.")
    return ConversationHandler.END
