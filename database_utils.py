import logging
import aiosqlite
from telegram.error import Forbidden

logger = logging.getLogger(__name__)

ALLOWED_USER_ID = 380441767

async def purge_database_except_user():
    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        # Удаляем всех пользователей, кроме указанного
        await db.execute(
            'DELETE FROM users WHERE user_id != ?',
            (ALLOWED_USER_ID,)
        )
        logger.info("Удалены все пользователи, кроме указанного.")

        # Удаляем все товары, кроме товаров указанного пользователя
        await db.execute(
            'DELETE FROM products WHERE user_id != ?',
            (ALLOWED_USER_ID,)
        )
        logger.info("Удалены все товары, кроме товаров указанного пользователя.")

        # Сохраняем изменения
        await db.commit()

async def init_db():
    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                chat_id INTEGER,
                created_at TEXT,
                revenue_min INTEGER,
                revenue_max INTEGER,
                mpstats_api_key TEXT  -- добавляем поле для API-ключа
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                revenue REAL,
                first_comment_date TEXT,
                product_id INTEGER,
                product_url TEXT,
                user_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        await db.commit()

async def save_product_for_user(item, user_id):
    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        await db.execute('''
            INSERT INTO products (name, revenue, first_comment_date, product_id, product_url, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            item.get('name', 'Нет названия'),
            item.get('revenue', 0),
            item.get('firstcommentdate', ''),
            item.get('id', ''),
            item.get('url', ''),
            user_id
        ))
        await db.commit()

import logging

logger = logging.getLogger(__name__)

async def delete_user_data(user_id):
    logger.info(f"Начинаем удаление данных для пользователя с user_id={user_id}")
    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        # Удаляем товары пользователя
        await db.execute('DELETE FROM products WHERE user_id = ?', (user_id,))
        logger.info(f"Удалены товары для user_id={user_id}")

        # Очищаем даты и диапазоны выручки в таблице users
        await db.execute('''
            UPDATE users
            SET revenue_min = NULL, revenue_max = NULL
            WHERE user_id = ?
        ''', (user_id,))
        logger.info(f"Очищены данные диапазона выручки для user_id={user_id}")

        # Сохраняем изменения
        await db.commit()
        logger.info(f"Данные для user_id={user_id} успешно удалены")






async def get_user_api_key(user_id):
    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        cursor = await db.execute('SELECT mpstats_api_key FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else None  # Возвращаем ключ или None, если он не найден
