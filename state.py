from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup


class Hospital(StatesGroup):
    name = State()
    inn = State()
    # key_words = State()

class HospitalDeleter(StatesGroup):
    name = State()

class CorrectHospitalKeyWords(StatesGroup):
    name = State()
    key_words = State()

class CorrectHospitalINN(StatesGroup):
    name = State()
    inn = State()

class GetFile(StatesGroup):
    status = State()
    key_words = State()

