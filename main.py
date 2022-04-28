import asyncio

import schedule
from telegram import Bot, Message, ReplyKeyboardMarkup
import datetime

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
bot = Bot(TOKEN)
MAIN_KEYBOARD = [['/add', '/complete', '/change_time'],
                 ['/show', '/help']]


def start(update, context):
    user_id = update.message.from_user.id
    db_sess = db_session.create_session()
    if not db_sess.query(User).filter(User.user_id == user_id).first():
        update.message.reply_text('Здравствуйте!\n'
                                  'Я - бот-помощник, который будет напоминать вам\n'
                                  'сделать или доделать какие-то задачи')
        update.message.reply_text("Но для начала представьтесь")
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
    sup = db_sess.query(Tasks).filter(Tasks.user_id == user.id, Tasks.done == 0).all()
    if not sup:
        num = 1
    else:
        num = sup[-1].number + 1
    print(num)
    task = Tasks(user_id=user.id,
                 title=title,
                 number=num)
    db_sess.add(task)
    db_sess.commit()
    markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, one_time_keyboard=True)
    update.message.reply_text(f'Отлично! Задача "{title}" добавлена в список задач', reply_markup=markup)
    return ConversationHandler.END


def complete_task(update, context):
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
    update.message.reply_text(text)
    db_sess = db_session.create_session()
    sup = db_sess.query(Tasks).filter(Tasks.user_id == user.id, Tasks.done == 0).all()
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
    tasks = db_sess.query(Tasks).filter(Tasks.user_id == user.id, Tasks.done == 0).all()
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
    update.message.reply_text("Постарайтесь выполнить, поставленные вами задачи", reply_markup=markup)
    return ConversationHandler.END


def show_tasks(update, context):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.user_id == update.message.from_user.id).first()
    text = f'Вот задачи, которые вам необходимо выполнить, {user.name}:\n'
    sup = db_sess.query(Tasks).filter(Tasks.user_id == user.id, Tasks.done == 0, Tasks.time == datetime.datetime.now().date()).all()
    overdue = db_sess.query(Tasks).filter(Tasks.user_id == user.id, Tasks.time < datetime.datetime.now().date(), Tasks.done == 0).all()
    if overdue:
        text += '\nЗадачи, оставшиеся с прошлых дней:\n'
        for i in overdue:
            text += u'\U0000274C' + f' {i.title} ' + '\n'
    if not (sup or overdue):
        text += 'Все задачи выполнены!'
        update.message.reply_text(text)
        return
    if sup:
        text += '\nЗадачи, записанные на сегодня:\n'
        for i in sup:
            text += u'\U0000274C' + f' {i.title} ' + '\n'
    sup = db_sess.query(Tasks).filter(Tasks.user_id == user.id, Tasks.done == 1).all()
    if sup:
        text += '\nЗадачи, которые вы выполнили за сегодня:\n'
    for i in sup:
        text += u'\U00002705' + f' {i.title} ' + '\n'
    update.message.reply_text(text)


def print_help(update, context):
    update.message.reply_text('''Функции, которые может выполнить бот:
    
/show - показать все актуальные задачи на сегодняшний день и их состояния

/add - добавить новую задачу в список дел

/complete - убрать задачу из списка дел

/help - показать подсказку по командам бота

/change_time - изменить частоту отправки уведомлений ботом''')


def announcement():
    print(datetime.datetime.now())
    db_sess = db_session.create_session()
    hour = datetime.datetime.now().hour
    if hour == 0:
        done_tasks = db_sess.query(Tasks).filter(Tasks.done == 1).all()
        for i in done_tasks:
            db_sess.delete(i)
            db_sess.commit()
    users = db_sess.query(User).filter(hour % User.time == 0).all()
    for user in users:
        undone_tasks = db_sess.query(Tasks).filter(Tasks.done == 0, Tasks.user_id == user.id).all()
        if undone_tasks:
            text = f'''{user.name}, сейчас {datetime.datetime.now().strftime("%H:%M")},
эти задачи вам необходимо выполнить:'''
            for task in undone_tasks:
                text += '\n' + u'\U0000274C' + f' {task.title}'
            bot.send_message(chat_id=user.user_id, text=text)
    print(datetime.datetime.now())


def start_changing(update, context):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.user_id == update.message.from_user.id).first()

    keyboard = [['Раз в 1 час', "Раз в 2 часа", "Раз в 3 часа"],
                ["Раз в 4 часа", "Раз в 8 часов", "/cancel"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)
    text = 'Как часто присылать уведомления?'
    if user.time == 1:
        text += '(сейчас уведомления присылаются раз в 1 час)'
    elif user.time == 8:
        text += '(сейчас уведомления присылаются раз в 8 часов)'
    else:
        text += f'(сейчас уведомления присылаются раз в {user.time} часа)'
    update.message.reply_text(text, reply_markup=markup)
    return 1


def enter_time(update, context):
    answers = {
        'Раз в 1 час': 1,
        'Раз в 2 часа': 2,
        'Раз в 3 часа': 3,
        'Раз в 4 часа': 4,
        "Раз в 8 часов": 8
    }
    answer = update.message.text
    if answer not in answers.keys():
        update.message.reply_text('Выбрано некорректное время\nвведите ещё раз:')
        return 1
    time = answers[answer]
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.user_id == update.message.from_user.id).first()
    user.time = time
    db_sess.commit()
    text = f'Успешно! Теперь уведомления будут присылаться {answer.lower()}'
    markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, one_time_keyboard=False)
    update.message.reply_text(text, reply_markup=markup)
    return ConversationHandler.END


def cancel_changing_task(update, context):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.user_id == update.message.from_user.id).first()
    if user.time == 1:
        text = 'Уведомления продолжат присылаться раз в 1 час'
    elif user.time == 8:
        text = 'Уведомления продолжат присылаться раз в 8 часов'
    else:
        text = f'Уведомления продолжат присылаться раз в {user.time} часа'
    markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, one_time_keyboard=False)
    update.message.reply_text(text, reply_markup=markup)
    return ConversationHandler.END


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    greeting = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, acquaintance)],
        },
        fallbacks=[CommandHandler('dkgWw12kjT3525k7nGeg', stop)]
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

    changing_time = ConversationHandler(
        entry_points=[CommandHandler('change_time', start_changing)],
        states={
            1: [MessageHandler(Filters.text & ~Filters.command, enter_time)]
        },
        fallbacks=[CommandHandler('cancel', cancel_changing_task)]
    )

    showing_task = CommandHandler('show', show_tasks)
    ask_for_help = CommandHandler('help', print_help)
    dp.add_handler(changing_time)
    dp.add_handler(ask_for_help)
    dp.add_handler(executing_task)
    dp.add_handler(showing_task)
    dp.add_handler(greeting)
    dp.add_handler(adding_task)
    schedule.every().hour.do(announcement)
    updater.start_polling()
    while True:
        schedule.run_pending()
    updater.idle()
    # Ждём завершения приложения.
    # (например, получения сигнала SIG_TERM при нажатии клавиш Ctrl+C)
    # updater.idle()


if __name__ == '__main__':
    db_session.global_init('db/todo_list.db')
    main()