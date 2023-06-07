from aiogram.dispatcher.filters.state import State, StatesGroup


class BotStates(StatesGroup):
    add_task = State()
    replan_task = State()
    print_tasks = State()
    wait_choose_task = State()
    del_task = State()
    del_account = State()