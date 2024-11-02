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
from get_member import check_subscription, subscription_required
from database_utils import delete_user_data
from reg_api_mpstat import register_api_key, save_api_key


# Константа для состояния
ENTER_API_KEY = range(1)

#Регистрация личного апи ключа мпстата
@subscription_required
async def register_api_key(update: Update, context: CallbackContext):
    await update.message.reply_text("Пожалуйста, введите ваш апи ключ мпстата:")
    return ENTER_API_KEY

# Обработка введенного API-ключа
async def save_api_key(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    api_key = update.message.text  # Получаем API-ключ из сообщения

    # Сохраняем API-ключ в базе данных
    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        await db.execute('''
            UPDATE users SET mpstats_api_key = ? WHERE user_id = ?
        ''', (api_key, user_id))
        await db.commit()

    await update.message.reply_text("Ваш API-ключ успешно сохранен.\n\nПри первичном формировании запроса, вы можете вписать любые данные.\n\nДалее при ежедневной отправке, бот будет отправлять те товары, у которых первый отзыв появился после даты, которая была две недели назад.\n\nБуду благодарен за обратную связь и предложения по улучшению работы.\n\nЧтобы начать введите /start_bot")
    return ConversationHandler.END  # Завершаем диалог


# Обработчик отменыs
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Регистрация API-ключа отменена.")
    return ConversationHandler.END
