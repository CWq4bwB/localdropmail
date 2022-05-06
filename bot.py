# Импортируем необходимые классы.
import logging
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from based_requests import fetch_users_messages, new_address, loaded_domains

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.ERROR
)

logger = logging.getLogger(__name__)

TOKEN = '' # токен телеграм бота

reply_keyboard = [['Новый адрес', 'Активные адреса'], ['Проверить входящие'],
                  ['Восстановить адрес', 'Доп. функции']]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)


def echo(update, context):
    result = fetch_users_messages(update.message.from_user.id, update.message.text)
    if type(result) == list and len(result) == 2:
        update.message.reply_text(result[0], reply_markup=result[1])
    else:
        update.message.reply_text(result, reply_markup=markup)


def button(update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    uid = query.message.chat.id
    query.answer()
    returned = new_address(uid, query.data)
    query.edit_message_text(text=returned)


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    text_handler = MessageHandler(Filters.text, echo)
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    dp.add_handler(text_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
