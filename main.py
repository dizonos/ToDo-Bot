from telegram import Bot, Message

from data import db_session

import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from data.users import User

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

TOKEN = '5237014408:AAGW2SKLTeqzJoaGHFoWxgT-SMPohD0gYzw'


def start(update, context):
    user_id = update.message.from_user.id
    db_sess = db_session.create_session()
    update.message.reply_text('Здравствуйте!\n')
    if not db_sess.query(User).filter(User.user_id == user_id).first():
        update.message.reply_text('Здравствуйте!\n'
                                  'Я - бот-помощник, который будет напоминать вам\n'
                                  'сделать или доделать какие-то задачи')
        update.message.reply_text("Но для начала предаставьтесь")
        return 1
    else:
        update.message.reply_text('Я уже вас знаю')
        return ConversationHandler.END


def acquaintance(update, context):
    user_id = update.message.from_user.id
    db_sess = db_session.create_session()
    name = update.message.text
    update.message.reply_text(f'Приятно познакомиться, {name}!')
    user = User(user_id=user_id,
                name=name)
    db_sess.add(user)
    db_sess.commit()
    update.message.reply_text("Для ознакомления с моими функциями введите: /help \n"
                              "Или нажмите кнопку help")
    return ConversationHandler.END


def stop(update, context):
    update.message.reply_text('Как хотите.\n'
                              'Но если мы с вами не познакомимся\n'
                              'я не смогу вам помочь,\n'
                              'а вы не сможет пользоваться моими функциями.')


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, acquaintance)],
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    dp.add_handler(conv_handler)
    # Регистрируем обработчик в диспетчере.
    # Запускаем цикл приема и обработки сообщений.
    updater.start_polling()

    # Ждём завершения приложения.
    # (например, получения сигнала SIG_TERM при нажатии клавиш Ctrl+C)
    updater.idle()


if __name__ == '__main__':
    db_session.global_init('db/todo_list.db')
    main()