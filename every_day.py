import logging
import asyncio
import requests
import json
import settings
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import datetime
import aiosqlite
from helpers import send_long_message, log_message
from database_utils import save_product_for_user

# Настройка логирования
logger = logging.getLogger(__name__)

yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
last_30_days_from_today = (datetime.datetime.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')




async def check_for_new_items(context: CallbackContext, chat_id, user_id) -> None:
    """Функция для проверки новых товаров и добавления их в базу данных."""
    logger.info(f"Начало проверки новых товаров для пользователя {user_id} в чате {chat_id}")

    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        cursor = await db.execute('SELECT revenue_min, revenue_max FROM users WHERE user_id = ?', (user_id,))
        user_data = await cursor.fetchone()

        if not user_data:
            await log_message(context, chat_id=chat_id, message="Данные пользователя не найдены.")
            logger.warning(f"Данные пользователя {user_id} не найдены.")
            return

        revenue_min, revenue_max = user_data
        logger.info(f"Диапазон выручки для пользователя {user_id}: от {revenue_min} до {revenue_max}")

        two_weeks_ago_from_today = (datetime.datetime.today() - datetime.timedelta(days=14)).strftime('%Y-%m-%d')
        yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        last_30_days_from_today = (datetime.datetime.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')

        # Данные для запроса
        json_data = {
            'startRow': 0,
            'endRow': 300, 
            'filterModel': {
                'firstcommentdate': {
                    'filterType': 'date',
                    'type': 'greaterThan',
                    'dateFrom': two_weeks_ago_from_today,
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

        logger.info("Отправка запроса к MPStats API")
        response = requests.post(url, headers=headers, data=json.dumps(json_data))
        
        if response.status_code == 200:
            logger.info("Ответ от MPStats API получен успешно")
            try:
                data = response.json().get('data', [])
                logger.info(f"Количество товаров получено: {len(data)}")
            except json.JSONDecodeError as e:
                await log_message(context, chat_id=chat_id, message=f"Ошибка в формате данных: {e}")
                logger.error(f"Ошибка JSONDecodeError: {e}")
                return

            if not data:
                await log_message(context, chat_id=chat_id, message="Товары не найдены.")
                logger.info("Товары не найдены.")
                return

            new_items = []
            async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
                for item in data:
                    product_id = item.get('id', None)

                    if not product_id:
                        continue

                    cursor = await db.execute('SELECT id FROM products WHERE product_id = ? AND user_id = ?', (product_id, user_id))
                    existing_item = await cursor.fetchone()

                    if not existing_item:
                        new_items.append(item)
                        await save_product_for_user(item, user_id)

            if new_items:
                logger.info(f"Новых товаров найдено: {len(new_items)}")
                for item in new_items:
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
                            await context.bot.send_photo(chat_id=chat_id, photo=photo_url, caption=message)
                            logger.info(f"Фото товара {item.get('id', 'Нет артикула')} успешно отправлено")
                        except Exception as e:
                            await log_message(context, chat_id=chat_id, message=message)
                            logger.error(f"Ошибка при отправке фото: {e}")
                    else:
                        await log_message(context, chat_id=chat_id, message=message)
                    await asyncio.sleep(1.5)
            else:
                await log_message(context, chat_id=chat_id, message="Новых товаров не найдено.")
                logger.info("Новых товаров не найдено.")
        else:
            await log_message(context, chat_id=chat_id, message=f"Ошибка API: {response.status_code}\n{response.text}")
            logger.error(f"Ошибка API: {response.status_code}\n{response.text}")