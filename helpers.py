import logging

# Настраиваем логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def send_long_message(chat_id, text, context):
    max_message_length = 4096
    for i in range(0, len(text), max_message_length):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text[i:i + max_message_length])
            logger.info(f"Сообщение успешно отправлено в чат {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке длинного сообщения: {e}")

async def log_message(context, chat_id, message):
    try:
        logger.info(f"Попытка отправить сообщение в чат {chat_id}: {message}")
        await context.bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Сообщение успешно отправлено в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в чат {chat_id}: {e}")