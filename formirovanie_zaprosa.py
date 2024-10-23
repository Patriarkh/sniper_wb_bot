import logging
import asyncio
import requests
import aiosqlite
import json
import settings
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import datetime
from common import register_user, make_mpstats_request
from database_utils import init_db  # Импортируем из нового файла

# Настройка логирования
logger = logging.getLogger(__name__)

# Константы этапов диалога
SET_ITEMS, SET_DATE, SET_REVENUE = range(3)

# Запрашиваем количество товаров
async def zapros_start(update: Update, context: CallbackContext) -> int:
    await register_user(update, context)
    await update.message.reply_text("Введите количество товаров (например, 10):")
    return SET_ITEMS

# Получаем количество товаров
async def get_quantity_goods(update: Update, context: CallbackContext) -> int:
    context.user_data['count'] = int(update.message.text)
    await update.message.reply_text("Введите дату в формате YYYY-MM-DD:")
    return SET_DATE

# Получаем дату
async def get_otzyv(update: Update, context: CallbackContext) -> int:
    context.user_data['date'] = update.message.text
    await update.message.reply_text("Укажите диапазон выручки в формате: минимальная выручка максимальная выручка")
    return SET_REVENUE

# Получаем диапазон выручки и сохраняем его в базу данных
async def get_diapazon_revenue(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    revenue_range = update.message.text.split()
    revenue_min = int(revenue_range[0])
    revenue_max = int(revenue_range[1])

    # Сохраняем данные в базу данных
    async with aiosqlite.connect('products.db') as db:
        await db.execute('''
            UPDATE users
            SET revenue_min = ?, revenue_max = ?
            WHERE user_id = ?
        ''', (revenue_min, revenue_max, user_id))
        await db.commit()

    # Теперь формируем и отправляем запрос к MPStats с использованием введенных данных
    await make_mpstats_request(update, context, user_id)
    return ConversationHandler.END

# Выход из диалога
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END
