# database_utils.py
import aiosqlite

async def init_db():
    async with aiosqlite.connect('products.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                chat_id INTEGER,
                created_at TEXT,
                revenue_min INTEGER,
                revenue_max INTEGER
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
    async with aiosqlite.connect('products.db') as db:
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
