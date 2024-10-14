async def send_long_message(chat_id, text, context):
    max_message_length = 4096
    for i in range(0, len(text), max_message_length):
        await context.bot.send_message(chat_id=chat_id, text=text[i:i + max_message_length])

async def log_message(context, chat_id, message):
    """Функция для отправки логов пользователю."""
    await context.bot.send_message(chat_id=chat_id, text=message)