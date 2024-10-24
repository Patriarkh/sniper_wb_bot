# common.py
import aiosqlite
import datetime
import logging
import asyncio
import requests
import json
import settings
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import datetime
import aiosqlite
from database_utils import save_product_for_user, init_db



logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sniper_bot.log"),  # Логи будут сохраняться в файл
        logging.StreamHandler()  # Логи также будут выводиться в консоль
    ]
)
logger = logging.getLogger(__name__)

async def make_mpstats_request(update: Update, context: CallbackContext, user_id):
    # Извлекаем данные из базы данных для пользователя
    async with aiosqlite.connect('products.db') as db:
        cursor = await db.execute('SELECT revenue_min, revenue_max FROM users WHERE user_id = ?', (user_id,))
        user_data = await cursor.fetchone()

        if not user_data:
            await update.message.reply_text("Данные пользователя не найдены.")
            return

        revenue_min, revenue_max = user_data
        count = context.user_data.get('count', 100)
        date_from = context.user_data.get('date')

        yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        last_30_days_from_today = (datetime.datetime.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')

        # Формируем данные для запроса
        json_data = {
            'startRow': 0,
            'endRow': count, 
            'filterModel': {
                'firstcommentdate': {
                    'filterType': 'date',
                    'type': 'greaterThan',
                    'dateFrom': date_from,
                },
                'revenue': {
                    'filterType': 'number',
                    'type': 'inRange',
                    'filter': revenue_min,
                    'filterTo': revenue_max,
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
                for item in data:
                    # Сохраняем товар и отправляем пользователю информацию
                    await save_product_for_user(item, user_id)
                    message = (
                        f"Название товара: {item.get('name', 'Нет названия')}\n"
                        f"Выручка: {item.get('revenue', 'Нет данных')}\n"
                        f"Дата первого отзыва: {item.get('firstcommentdate', 'Нет данных')}\n"
                        f"Артикул: {item.get('id', 'Нет артикула')}\n"
                        f"Ссылка на товар: {item.get('url', 'Нет ссылки')}\n"
                    )
                    photo_url = "https:" + item.get('thumb_middle', '')  
                    if photo_url:
                        try:
                            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url, caption=message)
                        except Exception as e:
                            logger.error(f"Ошибка при отправке фото: {e}")
                            await update.message.reply_text(message)  # Отправляем сообщение без фото при ошибке
                    else:
                        await update.message.reply_text(message)  # Если нет фото, отправляем только текст
                    await asyncio.sleep(1.5)
            else:
                await update.message.reply_text("Товары не найдены.")
        else:
            await update.message.reply_text(f"Ошибка: {response.status_code}\n{response.text}")


async def register_user(update, context):
    user_id = update.effective_user.id
    username = update.effective_user.username
    chat_id = update.effective_chat.id
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    async with aiosqlite.connect('products.db') as db:
        cursor = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user = await cursor.fetchone()

        if not existing_user:
            await db.execute('''
                INSERT INTO users (user_id, username, chat_id, created_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, chat_id, created_at))
            await db.commit()





