from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
from telegram import Update

async def check_subscription(update: Update, context: CallbackContext) -> bool:
    user_id = update.effective_user.id
    chat_member = await context.bot.get_chat_member(chat_id="@nikitaraikov", user_id=user_id)
    return chat_member.status in ["member", "administrator", "creator"]


def subscription_required(func):
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if not await check_subscription(update, context):
            await update.message.reply_text("Чтобы использовать бота, пожалуйста, подпишитесь на канал: @nikitaraikov")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

