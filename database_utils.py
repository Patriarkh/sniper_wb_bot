import aiosqlite

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

async def delete_user_data(user_id):
    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        await db.execute('DELETE FROM products WHERE user_id = ?', (user_id,))
        #await db.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        await db.commit()




async def get_user_api_key(user_id):
    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        cursor = await db.execute('SELECT mpstats_api_key FROM users WHERE user_id = ?', (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else None  # Возвращаем ключ или None, если он не найден
