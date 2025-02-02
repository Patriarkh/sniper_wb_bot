import logging
import asyncio

import pytz
import datetime

from telegram import Update
import settings
import aiosqlite
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from formirovanie_zaprosa import zapros_start, get_quantity_goods, get_otzyv, get_diapazon_revenue, cancel, init_db
from helpers import log_message
from every_day import check_for_new_items
from database_utils import init_db, purge_database_except_user
from get_member import check_subscription, subscription_required
from database_utils import delete_user_data
from reg_api_mpstat import register_api_key, save_api_key
from handle_request import handle_request
#from check_dostup import access_restricted



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




async def clear_database_command(update: Update, context: CallbackContext):
    await purge_database_except_user()
    await update.message.reply_text("База данных очищена для всех пользователей, кроме указанного.")


async def broadcast_message(context: CallbackContext, message_text: str):
    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        cursor = await db.execute('SELECT chat_id FROM users')
        users = await cursor.fetchall()

        for user in users:
            chat_id = user[0]
            try:
                await context.bot.send_message(chat_id=chat_id, text=message_text)
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения пользователю с chat_id {chat_id}: {str(e)}")


#async def broadcast_command(update: Update, context: CallbackContext):
    #if update.effective_user.id == 380441767:  # Замените на ваш Telegram ID
     #   if context.args:
      #      message_text = " ".join(context.args)
       #     await broadcast_message(context, message_text)
        #    await update.message.reply_text("Рассылка запущена!")
        #else:
#            await update.message.reply_text("Пожалуйста, введите сообщение после команды /broadcast.")
 #   else:
  #      await update.message.reply_text("У вас нет прав на выполнение этой команды.")


#Функция для удаления фильтров
#@subscription_required
async def delete_filters(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    logger.info(f"Команда /delete вызвана для user_id={user_id}")
    await delete_user_data(user_id)
    await update.message.reply_text("Ваши товары и фильтры успешно удалены. Для создания новых фильтров введите /start_bot.")

# Функция для проверки запуска бота
#@subscription_required
async def check(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text="Бот запущен")



# Ежедневная проверка по базе данных
#@access_restricted
async def schedule_daily_check(context: CallbackContext):
    async with aiosqlite.connect('/root/sniper_wb_bot/products.db') as db:
        cursor = await db.execute('SELECT user_id, username, chat_id, created_at FROM users')
        users = await cursor.fetchall()

        tasks = []
        for user in users:
            user_id, username, chat_id, created_at = user

            # Проверка подписки для каждого пользователя
            chat_member = await context.bot.get_chat_member(chat_id="@nikitaraikov", user_id=user_id)
            if chat_member.status in ["member", "administrator", "creator"]:
                # Если пользователь подписан, добавляем задачу в список
                tasks.append(check_for_new_items(context, chat_id, user_id))

        # Параллельное выполнение всех задач
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Логирование результатов и ошибок
        for result, user in zip(results, users):
            user_id, username, chat_id, created_at = user
            if isinstance(result, Exception):
                await log_message(context, chat_id=chat_id, message=f"Ошибка при проверке новых товаров: {result}")
            else:
                await log_message(context, chat_id=chat_id, message="Проверка новых товаров выполнена успешно.")







# Константы этапов диалога для формирования базы данных товаров
SET_ITEMS, SET_DATE, SET_REVENUE = range(3)

#Константа для регистрации аи ключа
ENTER_API_KEY = 4
async def main() -> None:
    logger.info("Инициализация базы данных...")
    await init_db()
    logger.info("База данных инициализирована.")
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Диалог для формирования базы данных товаров
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start_bot', zapros_start)],
        states={
            SET_ITEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity_goods)],
            SET_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_otzyv)],
            SET_REVENUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_diapazon_revenue)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Диалог для регистрации апи ключа
    conv_handler_api = ConversationHandler(
        entry_points=[CommandHandler('start', register_api_key)],
        states={
            ENTER_API_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_api_key)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )


# Добавляем JobQueue к приложению
    job_queue = application.job_queue

    application.add_handler(conv_handler)
    application.add_handler(conv_handler_api)
    application.add_handler(CommandHandler('check', check))
    application.add_handler(CommandHandler('delete', delete_filters))
    application.add_handler(CommandHandler("start_request", handle_request))
    #application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("clear_database", clear_database_command))
    application.add_error_handler(lambda update, context: logger.error(f"Произошла ошибка: {context.error}"))




    

    # Запуск проверки по базе данныех в 10:00 мск
    application.job_queue.run_daily(
    schedule_daily_check,
    time=datetime.time(hour=13, minute=20, tzinfo=pytz.timezone('Europe/Moscow'))
)




    # Инициализация приложения
    await application.initialize()

    # Запускаем polling и ждем
    await application.start()
    await application.updater.start_polling()  # Запуск polling
    
if __name__ == '__main__':
    try:
        # Получаем текущий event loop, если он уже запущен
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Если loop не запущен, создаем новый loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Запускаем приложение как таск
    loop.create_task(main())

    # Запускаем event loop, если он еще не запущен
    if not loop.is_running():
        loop.run_forever()