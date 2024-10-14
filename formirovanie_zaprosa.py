import logging
import requests
import json
import settings
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import datetime
import aiosqlite
from helpers import send_long_message, log_message


# Настройка логирования
logger = logging.getLogger(__name__)


# Константы этапов диалога
SET_ITEMS, SET_DATE, SET_REVENUE = range(3)

# Функция инициализации базы данных
async def init_db():
    async with aiosqlite.connect('products.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                revenue REAL,
                first_comment_date TEXT,
                product_id INTEGER,
                product_url TEXT
            )
        ''')
        await db.commit()




# Запрашиваем количество товаров
async def zapros_start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Введите количество товаров (например, 10):")
    return SET_ITEMS

# Получаем дату
async def get_quantity_goods(update: Update, context: CallbackContext) -> int:
    context.user_data['count'] = int(update.message.text)
    await update.message.reply_text("Введите дату в формате YYYY-MM-DD:")
    return SET_DATE

# Получаем диапазон выручки
async def get_otzyv(update: Update, context: CallbackContext) -> int:
    context.user_data['date'] = update.message.text
    await update.message.reply_text("Укажите диапазон выручки в формате: минимальная выручка максимальная выручка")
    return SET_REVENUE

# Получаем выручку и отправляем запрос
async def get_diapazon_revenue(update: Update, context: CallbackContext) -> int:
    revenue_range = update.message.text.split()
    context.user_data['revenue_min'] = int(revenue_range[0])
    context.user_data['revenue_max'] = int(revenue_range[1])





        # Вычисляем вчерашнюю дату и дату за последние 30 дней от вчерашнего дня
    yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    last_30_days_from_today = (datetime.datetime.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')



    
    # Формирование данных для запроса
    json_data = {
        'startRow': 0,
        'endRow': context.user_data['count'],
        'filterModel': {
            'firstcommentdate': {
                'filterType': 'date',
                'type': 'greaterThan',
                'dateFrom': context.user_data['date'],
            },
            'revenue': {
                'filterType': 'number',
                'type': 'inRange',
                'filter': context.user_data['revenue_min'],
                'filterTo': context.user_data['revenue_max'],
            }
        }
    }

    url = f'https://mpstats.io/api/wb/get/category?path=Женщинам&d1={last_30_days_from_today}&d2={yesterday}'
    headers = {
        'X-Mpstats-TOKEN': settings.MPSTATS_API_KEY,
        'Content-Type': 'application/json'
    }

    # Выполняем запрос к API
    response = requests.post(url, headers=headers, data=json.dumps(json_data))
    
    if response.status_code == 200:
        data = response.json().get('data', [])
        if data:
            message = "Вот список товаров:\n\n"
            # **Открываем соединение с базой данных**
            async with aiosqlite.connect('products.db') as db:
                for item in data:
                    name = item.get('name', 'Нет названия')
                    revenue = item.get('revenue', 'Нет данных о выручке')
                    first_comment_date = item.get('firstcommentdate', 'Нет данных о дате первого отзыва')
                    product_id = item.get('id', 'Нет артикула')
                    product_url = item.get('url', 'Нет ссылки')
                    message += f"Название товара: {name}\n, Выручка: {revenue}\n, Дата первого отзыва: {first_comment_date}\n, Артиукл: {product_id}\n, Ссылка на вб: {product_url}\n\n"
                    await db.execute('''
                            INSERT INTO products (name, revenue, first_comment_date, product_id, product_url)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (name, revenue, first_comment_date, product_id, product_url))
                # **Фиксируем изменения в базе данных**
                await db.commit()
            # Разделение и отправка длинного сообщения
            await send_long_message(update.effective_chat.id, message, context)
        else:
            await update.message.reply_text("Товары не найдены.")
    else:
        await update.message.reply_text(f"Ошибка: {response.status_code}\n{response.text}")

    return ConversationHandler.END

       

    


# Выход из диалога
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END


