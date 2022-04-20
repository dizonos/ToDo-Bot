from telegram import Bot, Message, ReplyKeyboardMarkup

from data import db_session

import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from data.users import User
from data.tasks import Tasks

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

TOKEN = '5237014408:AAGW2SKLTeqzJoaGHFoWxgT-SMPohD0gYzw'

MAIN_KEYBOARD = [['/add', '/complete'],
                 ['/show', '/help']]


def start(update, context):
    user_id = update.message.from_user.id
    db_sess = db_session.create_session()
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
    markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, one_time_keyboard=False)
    user_id = update.message.from_user.id
    db_sess = db_session.create_session()
    name = update.message.text
    update.message.reply_text(f'Приятно познакомиться, {name}!')
    user = User(user_id=user_id,
                name=name)
    db_sess.add(user)
    db_sess.commit()
    update.message.reply_text("Для ознакомления с моими функциями введите: /help \n"
                              "Или нажмите кнопку help",
                              reply_markup=markup)
    return ConversationHandler.END


def stop(update, context):
    markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, one_time_keyboard=False)
    update.message.reply_text('Как хотите.\n'
                              'Но если мы с вами не познакомимся\n'
                              'я не смогу вам помочь,\n'
                              'а вы не сможет пользоваться моими функциями.', reply_markup=markup)
    return ConversationHandler.END


def cancel_task(update, context):
    markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, one_time_keyboard=False)
    update.message.reply_text("Добавление задачи отменено", reply_markup=markup)
    return ConversationHandler.END


def add_task(update, context):
    reply_keyboard = [['/cancel']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Введите название задачи:",
                              reply_markup=markup)
    return 1


def enter_name(update, context):
    title = update.message.text
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.user_id == update.message.from_user.id).first()
    sup = db_sess.query(Tasks).filter(Tasks.user_id == user.id).all()
    if not sup:
        num = 1
    else:
        num = sup[-1].number + 1
    task = Tasks(user_id=user.id,
                 title=title,
                 number=num)
    db_sess.add(task)
    db_sess.commit()
    markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, one_time_keyboard=True)
    update.message.reply_text(f'Отлично! Задача "{title}" добавлена в список задач', reply_markup=markup)
    return ConversationHandler.END


def complete_task(update, context):
    show_tasks(update, context)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.user_id == update.message.from_user.id).first()
    sup = db_sess.query(Tasks).filter(Tasks.user_id == user.id).all()
    tasks = []
    sup_list = []
    for i in range(len(sup)):
        sup_list.append(sup[i].number)
        if len(sup_list) == 4:
            print(sup_list)
            tasks.append(sup_list)
            sup_list = []
    tasks.append(sup_list)
    if len(tasks[-1]) < 4:
        tasks[-1].append('/cancel')
    else:
        tasks.append(['/cancel'])
    markup = ReplyKeyboardMarkup(tasks, one_time_keyboard=True)
    print(tasks)
    update.message.reply_text('Какую задачу вы уже выполнили?', reply_markup=markup)
    return 1


def enter_number(update, context):
    number = update.message.text
    if not number.isdigit():
        update.message.reply_text('Неправильный номер задачи')
        return 1

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.user_id == update.message.from_user.id).first()
    if not db_sess.query(Tasks).filter(Tasks.user_id == user.id, Tasks.number == int(number)).all():
        update.message.reply_text('Неправильный номер задачи')
        return 1
    tasks = db_sess.query(Tasks).filter(Tasks.user_id == user.id).all()
    for i in tasks:
        if i.number < int(number):
            pass
        elif i.number == int(number):
            i.done = True
            db_sess.commit()
        else:
            i.number = i.number - 1
            db_sess.commit()
    markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, one_time_keyboard=False)
    text = u'\U0001F389' + 'Поздравляю с ещё одной выполненой задачей' + u'\U0001F389'
    update.message.reply_text(text, reply_markup=markup)
    return ConversationHandler.END


def cancel_executing_task(update, context):
    markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, one_time_keyboard=False)
    update.message.reply_text("Постарайтесь её выполнить", reply_markup=markup)
    return ConversationHandler.END


def show_tasks(update, context):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.user_id == update.message.from_user.id).first()
    text = f'Вот задачи, которые вам необходимо выполнить, {user.name}:\n'
    sup = db_sess.query(Tasks).filter(Tasks.user_id == user.id, Tasks.done == 0).all()
    if not sup:
        text += 'Все задачи выполнены!'
        update.message.reply_text(text)
        return
    for i in sup:
        text += f'{i.number}) {i.title} ' + u'\U0000274C' + '\n'
    sup = db_sess.query(Tasks).filter(Tasks.user_id == user.id, Tasks.done == 1).all()
    if sup:
        text += '\nЗадачи, которые вы уже выполнили\n'
    for i in sup:
        text += f'· {i.title} ' + u'\U00002705' + '\n'
    update.message.reply_text(text)


def print_help(update, context):
    update.message.reply_text('''Функции, которые может выполнить бот:
    
/show - показать все актуальные задачи на сегодняшний день и их состояния

/add - добавить новую задачу в список дел

/complete - убрать задачу из списка дел

/help - показать подсказку по командам бота''')


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    greeting = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, acquaintance)],
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    adding_task = ConversationHandler(
        entry_points=[CommandHandler('add', add_task)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, enter_name)]
        },
        fallbacks=[CommandHandler('cancel', cancel_task)]
    )

    executing_task = ConversationHandler(
        entry_points=[CommandHandler('complete', complete_task)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, enter_number)]
        },
        fallbacks=[CommandHandler('cancel', cancel_executing_task)]
    )

    showing_task = CommandHandler('show', show_tasks)
    ask_for_help = CommandHandler('help', print_help)

    dp.add_handler(ask_for_help)
    dp.add_handler(executing_task)
    dp.add_handler(showing_task)
    dp.add_handler(greeting)
    dp.add_handler(adding_task)
    # Регистрируем обработчик в диспетчере.
    # Запускаем цикл приема и обработки сообщений.
    updater.start_polling()

    # Ждём завершения приложения.
    # (например, получения сигнала SIG_TERM при нажатии клавиш Ctrl+C)
    updater.idle()


if __name__ == '__main__':
    db_session.global_init('db/todo_list.db')
    main()