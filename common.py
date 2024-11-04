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
from database_utils import save_product_for_user, init_db, get_user_api_key



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
    api_key = await get_user_api_key(user_id)
    if not api_key:
        await update.message.reply_text("API-ключ не найден. Пожалуйста, зарегистрируйте его командой /start")
        return
    # Извлекаем данные из базы данных для пользователя
    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
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
            'X-Mpstats-TOKEN': api_key,
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
            


import logging

# Инициализация логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def register_user(update, context):
    user_id = update.effective_user.id
    username = update.effective_user.username
    chat_id = update.effective_chat.id
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    logger.info(f"Регистрация пользователя: user_id={user_id}, username={username}, chat_id={chat_id}, created_at={created_at}")

    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        cursor = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user = await cursor.fetchone()
        logger.info(f"Проверка существования пользователя: user_id={user_id}, существует={bool(existing_user)}")

        if not existing_user:
            await db.execute('''
                INSERT INTO users (user_id, username, chat_id, created_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, chat_id, created_at))
            await db.commit()
            logger.info(f"Пользователь успешно зарегистрирован: user_id={user_id}")
        else:
            logger.info(f"Пользователь с user_id={user_id} уже существует в базе данных.")



