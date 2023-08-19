from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup


class Hospital(StatesGroup):
    title = State()
    inn = State()
    key_words = State()

class HospitalDeleter(StatesGroup):
    title = State()

