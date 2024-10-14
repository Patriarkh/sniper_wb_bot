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

yesterday = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
last_30_days_from_today = (datetime.datetime.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')




async def check_for_new_items(context: CallbackContext) -> None:
    """Функция для проверки новых товаров и добавления их в базу данных."""
    
    two_weeks_ago_from_today = (datetime.datetime.today() - datetime.timedelta(days=14)).strftime('%Y-%m-%d')

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
                'filter': 200000,
                'filterTo': 1200000,
            }
        }
    }

    url = f'https://mpstats.io/api/wb/get/category?path=Женщинам&d1={last_30_days_from_today}&d2={yesterday}' #возможно стоит поставить формулу актуальную дату
    headers = {
        'X-Mpstats-TOKEN': settings.MPSTATS_API_KEY,
        'Content-Type': 'application/json'
    }

    # Выполняем запрос к API
    response = requests.post(url, headers=headers, data=json.dumps(json_data))
    
    if response.status_code == 200:
        try:
            data = response.json().get('data', [])
        except json.JSONDecodeError as e:
            # Уведомляем, если формат ответа изменился
            await log_message(context, chat_id=380441767, message=f"Ошибка в формате данных: {e}")
            return

        if data:
            new_items = []
            async with aiosqlite.connect('products.db') as db:
                for item in data:
                    product_id = item.get('id', None)

                    if not product_id:
                        continue

                    # Проверяем, есть ли товар в базе данных
                    cursor = await db.execute('SELECT id FROM products WHERE product_id = ?', (product_id,))
                    existing_item = await cursor.fetchone()

                    if not existing_item:
                        # Товар новый, добавляем его в базу и собираем для уведомления
                        new_items.append(item)
                        await db.execute('''
                            INSERT INTO products (name, revenue, first_comment_date, product_id, product_url)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            item.get('name', 'Нет названия'),
                            item.get('revenue', 0),
                            item.get('firstcommentdate', ''),
                            product_id,
                            item.get('url', '')
                        ))
                await db.commit()

            if new_items:
                # Формируем сообщение с новыми товарами
                message = "Найдены новые товары:\n\n"
                for item in new_items:
                    message += f"Название товара: {item.get('name', 'Нет названия')}\n"
                    message += f"Выручка: {item.get('revenue', 'Нет данных')}\n"
                    message += f"Дата первого отзыва: {item.get('firstcommentdate', 'Нет данных')}\n"
                    message += f"Артикул: {item.get('id', 'Нет артикула')}\n"
                    message += f"Ссылка на товар: {item.get('url', 'Нет ссылки')}\n\n"
                # Отправляем сообщение
                await send_long_message(380441767, message, context)
            else:
                # Логирование, если новых товаров не найдено
                await log_message(context, chat_id=380441767, message="Новых товаров не найдено.")
        else:
            await log_message(context, chat_id=380441767, message="Товары не найдены.")
    else:
        await log_message(context, chat_id=380441767, message=f"Ошибка API: {response.status_code}\n{response.text}")

