import logging
import asyncio

import pytz
import datetime

from telegram import Update
import settings
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from formirovanie_zaprosa import zapros_start, get_quantity_goods, get_otzyv, get_diapazon_revenue, cancel, init_db, check_for_new_items
from helpers import send_long_message, log_message


async def check(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="Бот запущен")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования: INFO (можно заменить на DEBUG для более подробных логов)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sniper_bot.log"),  # Логи будут сохраняться в файл
        logging.StreamHandler()  # Логи также будут выводиться в консоль
    ]
)
logger = logging.getLogger(__name__)



async def schedule_daily_check(context: CallbackContext):
    try:
        await check_for_new_items(context)
        await log_message(context, chat_id=380441767, message="Проверка новых товаров выполнена успешно.")
    except Exception as e:
        await log_message(context, chat_id=380441767, message=f"Ошибка при проверке новых товаров: {e}")



# Константы этапов диалога
SET_ITEMS, SET_DATE, SET_REVENUE = range(3)

async def main() -> None:
    await init_db()
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Сбор данных от пользователя для запроса к мпстат (диалог)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', zapros_start)],
        states={
            SET_ITEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity_goods)],
            SET_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_otzyv)],
            SET_REVENUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_diapazon_revenue)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('check', check))

    # Планируем ежедневную задачу по проверке новых товаров
    application.job_queue.run_daily(
        schedule_daily_check,
        time=datetime.time(hour=10, tzinfo=pytz.timezone('Europe/Moscow'))
    )

    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())