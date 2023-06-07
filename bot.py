from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from db import BotDB
from states import BotStates

TOKEN = token

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())
Bot_db = BotDB('taskplanning_db.db')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    """Обработчик команды start"""
    # Добавление нового пользователя
    if not Bot_db.user_exists(message.from_user.id):
        Bot_db.add_user(message.from_user.id) 

    # Создание меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('Добавить задачу')
    button2 = types.KeyboardButton('Перенести задачу')
    button3 = types.KeyboardButton('Удалить задачу')
    button4 = types.KeyboardButton('Вывести список задач')
    button5 = types.KeyboardButton('Удалить аккаунт')
    markup.add(button1, button2, button3, button4, button5)

    # Вывод приветственного сообщения
    await bot.send_message(
        message.chat.id,
        'Добро пожаловать! Я помощник для планирования задач. '
        'Чтобы начать использование обратитесь к кнопкам меню. '
        'Чтобы прервать действие используйте команду /cancel.',
        reply_markup=markup
    )


@dp.message_handler(content_types=['text'])
async def menu_handler(message: types.Message):
    """Обработчики кнопок меню"""
    if message.chat.type == 'private':
        if message.text == 'Добавить задачу':
            await BotStates.add_task.set()  # Устанавливаем состояние
            await bot.send_message(
                message.chat.id,
                'Чтобы добавить новую задачу введите ее в следующем формате (описание является '
                'необязательным пунктом):\nНазвание\nДата (в формате гггг-мм-дд)\nОписание'
            )

        elif message.text == 'Перенести задачу':
            data = Bot_db.get_all_tasks(message.from_user.id)
            if not data:
                await bot.send_message(message.chat.id, 'Ничего не запланировано.')
                return
            
            markup = create_inline_marcap(data)
            await BotStates.wait_choose_task.set()
            await bot.send_message(
                message.chat.id,
                f'Выберите задачу, которую хотите перенести.',
                reply_markup=markup
            )

        elif message.text == 'Удалить задачу':
            data = Bot_db.get_all_tasks(message.from_user.id)
            if not data:
                await bot.send_message(message.chat.id, 'Ничего не запланировано.')
                return  
            
            markup = create_inline_marcap(data)
            await BotStates.del_task.set()
            await bot.send_message(
                message.chat.id,
                f'Выберите задачу, которую хотите удалить.',
                reply_markup=markup
            )

        elif message.text == 'Вывести список задач':
            await BotStates.print_tasks.set()
            await bot.send_message(
                message.chat.id, 'Введите дату в формате гггг-мм-дд.'
            )

        elif message.text == 'Удалить аккаунт':
            await BotStates.del_account.set()
            await bot.send_message(
                message.chat.id,
                'Вы уверены? Все ваши записи будут безвозвратно удалены. (Да/Нет)'
            )

        else:
            await bot.send_message(
                message.chat.id,
                'Я вас не понимаю. Попробуйте обратиться к кнопкам меню.'
            )


@dp.message_handler(state='*', commands=['cancel'])
async def cancel(message: types.Message, state: FSMContext):
    """Пропустить текущее действие"""
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.reply(
        'Действие пропущено. Для возобновления работы введите /start.',
        reply_markup=types.ReplyKeyboardRemove()
    )


@dp.message_handler(state=BotStates.del_account)
async def print_tasks_process(message: types.Message, state: FSMContext):
    """Удаление аккаунта"""
    async with state.proxy() as data:
        data['print_tasks'] = message.text
    
    user_decision = message.text
    if str.lower(user_decision) == 'да':
        Bot_db.del_user(message.from_user.id)
        await state.finish()
        await message.reply('Ваш аккаунт успешно удален.')

    elif str.lower(user_decision) == 'нет':
        await state.finish()
        await message.reply('Удаление отменено.')
    
    else:
        await state.finish()
        await message.reply('Введено некорректное значение. Удаление отменено.')


@dp.message_handler(state=BotStates.add_task)
async def add_task_process(message: types.Message, state: FSMContext):
    """Добавление задачи""" 
    # Сохранение данных, получнных от пользователя, в MemoryStorage
    async with state.proxy() as data:
        data['add_task'] = message.text
    
    task = message.text.splitlines()
    if len(task) != 3:
        task.append('')
    Bot_db.add_task(message.from_user.id, task[0], task[1], task[2])

    await state.finish()
    await bot.send_message(message.chat.id, 'Задача успешно добавлена.')


@dp.message_handler(state=BotStates.replan_task)
async def replan_task_process(message: types.Message, state: FSMContext):
    """Перенос задачи"""
    async with state.proxy() as data:
        data['replan_task'] = message.text
    
    text = message.text.split(' ')
    Bot_db.replan_task(text[0], text[1])
    await state.finish()
    await bot.send_message(message.chat.id, 'Задача успешно перенесена.')


@dp.message_handler(state=BotStates.print_tasks)
async def print_tasks_process(message: types.Message, state: FSMContext):
    """Вывод списка задач"""
    async with state.proxy() as data:
        data['print_tasks'] = message.text

    data = Bot_db.get_tasks(message.from_user.id, message.text)
    if not data:
        await state.finish()
        await bot.send_message(message.chat.id, f'Ничего не запланировано.')
        return
        
    markup = create_inline_marcap(data)
    await state.finish()
    await bot.send_message(
        message.chat.id,
        f'Задачи на {message.text}:', reply_markup=markup
    )


def create_inline_marcap(data):
    """Функция преобразования выборки из БД в набор кнопок"""
    # data = [(id, users_id, title, description, date, state),] 
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i in data:
        button_text = f'{i[4]} - {i[2]}'
        if i[3]:
            button_text += ': ' + str(i[3])
        if i[5] == 1:
            button_text = '+ ' + button_text
        else: 
            button_text = '- ' + button_text
        markup.add(
            types.InlineKeyboardButton(button_text, callback_data=f'task_id_{i[0]}')
        )
    return markup


@dp.callback_query_handler(lambda c: c.data.startswith('task_id_'), state='*')
async def change_task(call: types.CallbackQuery, state: FSMContext):
    """Изменение задачи"""
    current_state = await state.get_state()
    if current_state is None:
        Bot_db.complete_task(call.data.replace('task_id_', ''))
        await bot.send_message(
            call.message.chat.id,
            'Молодец! Так держать! Чтобы увидеть изменения выведите список задач снова.'
        )
    
    if current_state == 'BotStates:wait_choose_task':
        task_id = call.data.replace('task_id_', '')
        async with state.proxy() as data:
            data['wait_choose_task'] = task_id
        await state.finish()
        await BotStates.replan_task.set()
        await bot.send_message(
            call.message.chat.id,
            f'Введите через пробел номер задачи - {task_id} - и дату в формате гггг-мм-дд.'
        )
    
    if current_state == "BotStates:del_task":
        task_id = call.data.replace('task_id_', '')
        async with state.proxy() as data:
            data['wait_choose_task'] = task_id
        Bot_db.del_task(task_id)
        await state.finish()
        await bot.send_message(call.message.chat.id, 'Задача успешно удалена.')


if __name__ == '__main__':
    executor.start_polling(dp)
