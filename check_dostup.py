import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from functools import wraps


logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sniper_bot.log"),  # Логи будут сохраняться в файл
        logging.StreamHandler()  # Логи также будут выводиться в консоль
    ]
)
logger = logging.getLogger(__name__)

# ID пользователя, которому разрешен доступ
ALLOWED_USER_ID = 380441767


# Декоратор для ограничения доступа
def access_restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        if update.effective_user.id != ALLOWED_USER_ID:
            await update.message.reply_text("У вас нет подписки. Напишите @nikiraikov")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

