# common.py
import aiosqlite
import datetime

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

async def init_db():
    async with aiosqlite.connect('products.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                chat_id INTEGER,
                created_at TEXT
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


