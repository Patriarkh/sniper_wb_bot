from telegram import Update
from telegram.ext import CallbackContext 
from common import make_mpstats_request

async def handle_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Добавляем задание в JobQueue для выполнения make_mpstats_request
    context.job_queue.run_once(
        make_mpstats_request,
        0,  # Запуск без задержки
        data={'user_id': user_id, 'update': update}  # Передаем данные для задания через `data`
    )

    # Уведомляем пользователя о запуске задачи
    await update.message.reply_text("Ваш запрос обрабатывается. Это может занять некоторое время.")
