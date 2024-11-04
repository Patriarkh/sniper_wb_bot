from telegram import Update
from telegram.ext import CallbackContext 
from common import make_mpstats_request

async def handle_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Добавляем задание в JobQueue для выполнения make_mpstats_request
    context.job_queue.run_once(
        make_mpstats_request,  # Функция, которую нужно выполнить
        1,  # Задержка перед выполнением (0 = немедленно)
        data={'user_id': user_id, 'update': update}  # Параметры для задания
    )

    # Уведомляем пользователя, что задача выполняется
    await update.message.reply_text("Ваш запрос обрабатывается. Это может занять некоторое время.")
