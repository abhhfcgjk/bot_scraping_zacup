from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup


class Hospital(StatesGroup):
    name = State()
    inn = State()
    # key_words = State()

class HospitalDeleter(StatesGroup):
    name = State()

class CorrectHospitalINN(StatesGroup):
    name = State()
    inn = State()

class GetFile(StatesGroup):
    filter_ = State()
    key_words = State()

