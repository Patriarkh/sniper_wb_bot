from telegram import Update
from telegram.ext import CallbackContext 
from common import make_mpstats_request
from check_dostup import access_restricted

@access_restricted
async def handle_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    count = context.user_data.get('count', 100)
    date_from = context.user_data.get('date')

    # Добавляем задание в JobQueue для выполнения make_mpstats_request
    context.job_queue.run_once(
        make_mpstats_request,
        0,  # Запуск без задержки
        data={'user_id': user_id, 'update': update, 'count': count, 'date_from': date_from}  # Передаем count и date_from
    )

    # Уведомляем пользователя о запуске задачи
    await update.message.reply_text("Ваш запрос обрабатывается. Это может занять некоторое время.")
