from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, ConversationHandler
from key import TOKEN
from openpyxl import load_workbook
from connect_to_database import stickers, replies, insert_sticker, insert_user, in_database


WAIT_NAME, WAIT_SEX, WAIT_GRADE = range(3)


bd = load_workbook('database.xlsx')


def main():
    updater = Updater(
        token=TOKEN,
        use_context=True
    )

    dispatcher = updater.dispatcher

    echo_handler = MessageHandler(Filters.all, do_echo)
    text_handler = MessageHandler(Filters.text, meet)
    sticker_handler = MessageHandler(Filters.sticker, new_sticker)
    hello_handler = MessageHandler(Filters.text('Привет'), say_hello)
    murad_handler = MessageHandler(Filters.text('Мурад'), say_ahay)
    da_handler = MessageHandler(Filters.text('Да'), say_da)
    keyboard_handler = MessageHandler(Filters.text('Клавиатура'), keyboard)
    conv_handler = ConversationHandler(
        entry_points=[text_handler],  # Точка старта диалога
        states={
            WAIT_NAME: [MessageHandler(Filters.text, ask_sex)],
            WAIT_SEX: [MessageHandler(Filters.text, ask_grade)],
            WAIT_GRADE: [MessageHandler(Filters.text, greet)],
        },  # Состояния конечного автомата для диалога
        fallbacks=[],  # Общие точки выхода или отмены
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(echo_handler)
    dispatcher.add_handler(hello_handler)
    dispatcher.add_handler(text_handler)
    dispatcher.add_handler(keyboard_handler)
    dispatcher.add_handler(sticker_handler)
    dispatcher.add_handler(murad_handler)
    dispatcher.add_handler(da_handler)

    updater.start_polling()
    print('Всё чики-пуки!')
    updater.idle()


def do_echo(update: Update, context: CallbackContext):
    name = update.message.from_user.first_name
    id = update.message.chat_id
    text = update.message.text if update.message.text else "текста нет"
    sticker = update.message.sticker
    if sticker:
        sticker_id = sticker.file_id
        update.message.reply_sticker(sticker_id)
    update.message.reply_text(text=f'Твой id: {id}\n'
                                   f'Твой текст: {text}\n'
                                   f'Твой стикер: {sticker}')


def say_hello(update: Update, context: CallbackContext):
    name = update.message.from_user.first_name
    id = update.message.chat_id
    text = update.message.text
    update.message.reply_text(text=f'Здарова, {name}!\n'
                                   f'Приятно познакомиться с живым человеком!\n'
                                   f'Я - бот!')


def new_sticker(update: Update, context: CallbackContext):
    sticker_id = update.message.sticker.file_id
    for keyword in stickers:
        if sticker_id == stickers[keyword]:
            update.message.reply_text('У меня тоже такой есть!')
            update.message.reply_sticker(sticker_id)
            break
    else:
        context.user_data['new_sticker'] = sticker_id
        update.message.reply_text('Скажи мне ключевое слово для этого стикера, и я его запомню')


def new_keyword(update: Update, context: CallbackContext):
    if 'new_sticker' not in context.user_data:
        say_smth(update, context)
    else:
        keyword = update.message.text
        sticker_id = context.user_data['new_sticker']
        insert_sticker(keyword, sticker_id)
        context.user_data.clear()


def say_ahay(update: Update, context: CallbackContext):
    text = update.message.text
    update.message.reply_text(text=f'Ахай!')


def say_da(update: Update, context: CallbackContext):
    text = update.message.text
    update.message.reply_text(text=f'во рту вода ахаха')


def say_smth(update: Update, context: CallbackContext):
    name = update.message.from_user.first_name
    text = update.message.text
    for keyword in stickers:
        if keyword in text:
            if stickers[keyword]:
                update.message.reply_sticker(stickers[keyword])
            if replies[keyword]:
                update.message.reply_text(replies[keyword].format(name))
            break
    else:
        do_echo(update, context)


def keyboard(update: Update, context: CallbackContext):
    buttons = [
        ['Добавить стикер'],
        ['привет','пока']
    ]
    keys = ReplyKeyboardMarkup(
        buttons
    )

    update.message.reply_text(
        text='Смотри! У тебя появилась клавиатура',
        reply_markup=ReplyKeyboardMarkup(
            buttons,
            resize_keyboard=True,
            # one_time_keyboard=True

        )
    )


def meet(update: Update, context: CallbackContext):
    '''
    Старт диалога по добавлению пользователя в базу данных.
    Будут собраны последовательно:
        имя
        пол
        класс
        id пользователя
    '''
    user_id = update.message.from_user.id
    if in_database(user_id):
        update.message.reply_text(
            f'Добро пожаловать, {update.message.from_user.first_name}\n',
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    return ask_name(update, context)


def ask_name(update: Update, context: CallbackContext):
    '''
    Спрашивает у пользователя его имя
    TODO проверить имя пользователя в телеге
    '''
    update.message.reply_text(
        'Привет! Тебя еще нет в моей Базе Данных\n'
        'Давай знакомиться!\n'
        'Введи твое имя'
    )

    return WAIT_NAME


def ask_sex(update: Update, context: CallbackContext):
    '''
    Спрашивает у пользователя его пол
    '''
    name = update.message.text
    if not name_is_valid(name):
        update.message.reply_text(
            'Такое имя не подходит!\n'
            'Оно должно состоять из букв и начинаться с большой буквы.\n'
            'Введи имя еще раз'
        )
        return WAIT_NAME
    context.user_data['name'] = name  # Запоминаем имя
    buttons = [
        ['Мужчина', 'Женщина', 'Оптимус Прайм']
    ]
    keys = ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True
    )
    reply_text = f'Приятно познакомиться, {name}!\n' + 'Теперь укажи свой пол'
    update.message.reply_text(
        reply_text,
        reply_markup=keys
    )

    return WAIT_SEX


def ask_grade(update: Update, context: CallbackContext):
    '''
    Спрашивает у пользователя его класс
    '''
    sex = update.message.text
    if not sex_is_valid(sex):
        update.message.reply_text(
            'Ну выбери ты нормальный пол емае\n'
            'Возпользуйся клавиатурой'
        )
        return WAIT_SEX
    context.user_data['sex'] = sex
    buttons = [
        ['1', '2', '3', '4', '5'],
        ['6', '7', '8', '9', '10', '11']
    ]
    keys = ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True
    )
    reply_text = f'Отлично!\n' + 'Теперь скажи, в каком ты классе?'
    update.message.reply_text(
        reply_text,
        reply_markup=keys
    )

    return WAIT_GRADE


def greet(update: Update, context: CallbackContext):
    '''
    Записывает в базу данных:
        user_id (сообщение)
        name (context)
        sex (context)
        grade (сообщение)

    и приветствует нового пользователя
    '''
    grade = update.message.text
    if not grade_is_valid(grade):
        update.message.reply_text(
            'Ну выбери ты класс емае\n'
            'Возпользуйся клавиатурой'
        )
        return WAIT_GRADE
    user_id = update.message.from_user.id
    name = context.user_data['name']
    sex = context.user_data['sex']
    grade = update.message.text
    # Добавляем пользователя в БД
    insert_user(user_id, name, sex, grade)

    update.message.reply_text(  # Ответ на этапе отладки
        f'Новая запись в Базе Данных\n'
        f'{user_id=}\n'
        f'{name=}\n'
        f'{sex=}\n'
        f'{grade=}\n'
    )

    return ConversationHandler.END


def name_is_valid(name: str) -> bool:
    return name.isalpha() and name[0].isupper() and name[1:].islower()


def sex_is_valid(sex: str) -> bool:
    return sex in ('Мужчина', 'Женщина', 'Оптимус Прайм')


def grade_is_valid(grade: str) -> bool:
    return grade in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11')


if __name__ == '__main__':
    main()
