from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, any_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Document, FSInputFile, CallbackQuery, Message
from datetime import date
import logging
import sentry_sdk

from state import *
from config import TOKEN, EX_FILE, DSN
import keyboard
import bot_json as bj
import zacup_parser as zp


bot_logger = logging.getLogger(__name__)
bot_logger.setLevel(logging.INFO)

# настройка обработчика и форматировщика для logger2
handler = logging.FileHandler(f"{__name__}.log", mode='w')
formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")

# добавление форматировщика к обработчику
handler.setFormatter(formatter)
# добавление обработчика к логгеру
bot_logger.addHandler(handler)

sentry_sdk.init(
  dsn = DSN,
  # Set traces_sample_rate to 1.0 to capture 100%
  # of transactions for performance monitoring.
  # We recommend adjusting this value in production.
  traces_sample_rate = 1.0,
  attach_stacktrace = True
)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

hospital: dict[str, dict[str, str | list]] = {}
hospital_title: str = ""
filt: str


@dp.message(Command(commands=['start']), StateFilter(default_state))
async def process_start_command(message: Message):
    """Команда для начала работ"""
    await message.reply("Привет!\nНапиши мне что-нибудь!", reply_markup=keyboard.greet_kb)


@dp.message(F.text == "cancel", StateFilter(any_state))
@dp.message(Command(commands="cancel"), StateFilter(any_state))
async def process_cancel(message: Message, state: FSMContext):
    """Отмена действия при любом значении state"""
    await state.clear()
    await message.reply("Отменено", reply_markup=keyboard.greet_kb)


@dp.message(F.text == "Список больниц")
@dp.message(Command(commands="print"))
async def process_print_hospitals(message: Message):
    """Вывод влех больниц в списке"""
    msg: str = bj.print_all_hospitals()
    if(len(msg)!=0):
        await message.answer(msg, reply_markup=keyboard.greet_kb)
    else:
        await message.answer("Больниц пока не добавлено")


@dp.message(F.text == "Изменить ИНН больницы", StateFilter(default_state))
async def correct_key_words(message: Message, state: FSMContext):
    """Обработчик команды для изменения ИНН"""
    await state.set_state(CorrectHospitalINN.name)
    await message.reply("Введите название больницы", reply_markup=keyboard.cancel_kb)


@dp.message(StateFilter(CorrectHospitalINN.name))
async def input_hospital_title_correct_inn(message: Message, state: FSMContext):
    """Получение имени больницы для изменения ИНН"""
    await state.update_data(name=message.text.strip())
    await state.set_state(CorrectHospitalINN.inn)
    await message.answer("Введите новый ИНН", reply_markup=keyboard.cancel_kb)


@dp.message(StateFilter(CorrectHospitalINN.inn))
async def input_inn_correct(message: Message, state: FSMContext):
    """Получение ИНН для изменения ИНН"""
    await state.update_data(inn=message.text.strip())
    hospital_data = await state.get_data()
    if(bj.correct_inn(hospital_data['name'], hospital_data['inn'])):
        await message.answer("Данные изменены", reply_markup=keyboard.greet_kb)
    else:
        await message.answer("Введенная больница не найдена", reply_markup=keyboard.greet_kb)
    await state.clear()


@dp.message(StateFilter(default_state), F.text=="Добавить больницу")
@dp.message(StateFilter(default_state), Command(commands=["add"]))
async def add_hospital(message: Message, state: FSMContext):
    """Обработчик команды для добавления больниц"""
    await state.set_state(Hospital.name)
    await message.reply("Введите название больницы(какое будет удобнее)", reply_markup=keyboard.cancel_kb)


@dp.message(StateFilter(default_state), F.text=="Удалить больницу")
@dp.message(StateFilter(default_state), Command(commands=["remove"]))
async def del_hospital(message: Message, state: FSMContext):
    """Обработчик команды на удаление больницы из списка"""
    await state.set_state(HospitalDeleter.name)
    await message.reply("Введите название больницы", reply_markup=keyboard.cancel_kb)


@dp.message(StateFilter(HospitalDeleter.name))
async def process_delete_hospital(message: Message, state: FSMContext):
    """Ввод названия больницы для удаления из списка"""
    hosp_name = message.text.strip()
    ans:bool = bj.del_hospital_json(hosp_name)
    await state.clear()
    if(ans):
        await message.answer("Больница удалена", reply_markup=keyboard.greet_kb)
    else:
        await message.answer("Такой больницы нет в списке", reply_markup=keyboard.greet_kb)


@dp.message(StateFilter(Hospital.name))
async def process_title(message: Message, state: FSMContext):
    """Ввод названия больницы при добавлении больницы"""
    await state.update_data(name=message.text.strip())
    await state.set_state(Hospital.inn)
    await message.reply("Введите ИНН больницы", reply_markup=keyboard.cancel_kb)


@dp.message(StateFilter(Hospital.inn))
async def process_inn(message: Message, state: FSMContext):
    """Ввод ИНН при добавлении больниц"""
    await state.update_data(inn=message.text.strip())
    hospital = await state.get_data() # записываем полученные данные в переменную
    bj.add_hospital(hospital) # добавляем больницу в файл
    await state.clear()
    await message.answer("Больница добавлена", reply_markup=keyboard.greet_kb)



@dp.message(F.text == "Получить файл", StateFilter(default_state))
@dp.message(Command(commands=["get"]), StateFilter(default_state))
async def process_get_file(message: Message, state: FSMContext):
    """Обработчик команды для получения файла"""
    await state.set_state(GetFile.filter_)
    await message.answer("Выберите фильтр", reply_markup=keyboard.file_kb.as_markup())


@dp.callback_query(StateFilter(GetFile.filter_))
async def get_filter_file(callback: CallbackQuery, state: FSMContext):
    """Выбор фильтра для формирования файла"""
    await state.update_data(state=callback.data)
    await state.set_state(GetFile.key_words)
    await callback.message.answer("Введите ключевые слова")


@dp.message(StateFilter(GetFile.key_words))
async def get_key_words_file(message: Message, state: FSMContext):
    """Ввод ключевых слов и отправка файла"""
    kw = convert_key_words(message.text)
    await state.update_data(key_words=kw)
    st_data = await state.get_data()
    filt, key_words = st_data['state'], st_data['key_words']
    await state.clear()
    await message.answer("Делаю")
    zp.create_file(filt, key_words)
    user_id = message.from_user.id
    fname = f"{key_words}-{date.today()}"
    uploaded_file = FSInputFile(EX_FILE, filename=fname)
    await bot.send_document(user_id, uploaded_file,
                            caption='Этот файл специально для тебя!',
                            reply_markup=keyboard.greet_kb)



@dp.message()
async def unknown_message(message: Message):
    """Обработка неизвестной команды"""
    await message.answer("Комманда не распознана", reply_markup=keyboard.greet_kb)


def convert_key_words(msg: str)->list:
    """Преобразует сообщение ключевых слов в список"""
    keys = msg.split(",") # разбиваем список слов на list
    for i in range(len(keys)):
        keys[i] = keys[i].strip().lower() # удаляем лишние пробелы и делаем все буквы маленькими
    keys = [x for x in keys if len(x)>0]
    return keys

if __name__ == '__main__':
    dp.run_polling(bot)