from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, any_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Document
from aiogram.types import FSInputFile
import asyncio
from datetime import date

# import logging
import sentry_sdk

from state import *
from config import TOKEN, EX_FILE
import keyboard
import bot_json as bj
import zacup_parser as zp


sentry_sdk.init(
  dsn="https://193ca85583edbe786beb78b3baca992f@o4505727864012800.ingest.sentry.io/4505727869583360",

  # Set traces_sample_rate to 1.0 to capture 100%
  # of transactions for performance monitoring.
  # We recommend adjusting this value in production.
  traces_sample_rate=1.0
)


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

hospital: dict[str, dict[str, str | list]] = {}
hospital_title: str = ""

@dp.message(Command(commands=['start']), StateFilter(default_state))
async def process_start_command(message: types.Message):
    await message.reply("Привет!\nНапиши мне что-нибудь!", reply_markup=keyboard.greet_kb)


# @dp.message(Command(commands=['help']))
# async def process_help_command(message: types.Message):
#     await message.reply("Напиши мне что-нибудь, и я отпрпавлю этот текст тебе в ответ!")

# @dp.message(Command(commands=['file']))
# async def process_file_command(message: types.Message):
#     # user_id = message.from_user.id
#     # await bot.send_chat_action(user_id, ChatActions.UPLOAD_DOCUMENT)
#     # await asyncio.sleep(1)  # скачиваем файл и отправляем его пользователю
#     # await bot.send_document(user_id, EX_FILE,
#     #                         caption='Этот файл специально для тебя!')
#     await message.reply_document(open(EX_FILE, 'rb'), caption="Информация по запрошенным больницам")

@dp.message(F.text == "Отмена", Command(commands="cancel"), StateFilter(any_state))
async def process_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.reply("Отменено", reply_markup=keyboard.greet_kb)

@dp.message(F.text == "Список больниц")
@dp.message(Command(commands="print"))
async def process_print_hospitals(message: types.Message):
    msg: str = bj.print_all_hospitals()
    if(len(msg)!=0):
        await message.answer(msg, reply_markup=keyboard.greet_kb)
    else:
        await message.answer("Больниц пока не добавлено")

@dp.message(StateFilter(default_state), F.text=="Добавить больницу")
@dp.message(StateFilter(default_state), Command(commands=["add"]))
async def add_hospital(message: types.Message, state: FSMContext):
    await state.set_state(Hospital.title)
    await message.reply("Введите название больницы(какое будет удобнее)", reply_markup=keyboard.cancel_kb)

@dp.message(StateFilter(default_state), F.text=="Удалить больницу")
@dp.message(StateFilter(default_state), Command(commands=["rm"]))
async def del_hospital(message: types.Message, state: FSMContext):
    await state.set_state(HospitalDeleter.title)
    await message.reply("Введите название больницы")

@dp.message(StateFilter(HospitalDeleter.title))
async def process_delete_hospital(message: types.Message, state: FSMContext):
    hosp_name = message.text.strip()
    ans:bool = bj.del_hospital_json(hosp_name)
    await state.clear()
    if(ans):
        await message.answer("Больница удалена", reply_markup=keyboard.greet_kb)
    else:
        await message.answer("Такой больницы нет в списке", reply_markup=keyboard.greet_kb)

@dp.message(StateFilter(Hospital.title))
async def process_title(message: types.Message, state: FSMContext):
    global hospital_title
    hospital_title = message.text.strip()
    await message.reply("Введите ИНН больницы", reply_markup=keyboard.cancel_kb)
    await state.set_state(Hospital.inn)

@dp.message(StateFilter(Hospital.inn))
async def process_inn(message: types.Message, state: FSMContext):
    await state.update_data(inn=message.text.strip())
    await message.reply("Введите ключевые слова через запятую",reply_markup=keyboard.cancel_kb)
    await state.set_state(Hospital.key_words)

@dp.message(StateFilter(Hospital.key_words))
async def process_key_words(message: types.Message, state: FSMContext):
    keys = message.text.split(",")
    for i in range(len(keys)):
        keys[i] = keys[i].strip().lower()
    await state.update_data(keys_words=keys)
    hospital[hospital_title] = await state.get_data()
    print(hospital)
    bj.add_hospital(hospital)
    hospital.clear()
    await state.clear()
    await message.answer("Больница добавлена", reply_markup=keyboard.greet_kb)

@dp.message(F.text == "Получить файл с урожаем")
@dp.message(Command(commands=["get"]))
async def process_get_file(message: types.Message):
    zp.create_file()
    user_id = message.from_user.id
    fname = f"ex{date.today()}"
    uploaded_file = FSInputFile(EX_FILE, filename=fname)
    await asyncio.sleep(1)  # скачиваем файл и отправляем его пользователю
    await bot.send_document(user_id, uploaded_file,
                            caption='Этот файл специально для тебя!',
                            reply_markup=keyboard.greet_kb)

# @dp.message(content_types=ContentType.ANY)
# async def unknown_message(msg: types.Message):
#     message_text = fmt.text(fmt.text('Я не знаю, что с этим делать'),
#                         fmt.italic('\nВоспользуйтесь'),
#                         fmt.code('командой'), '/help')
#     await msg.reply(message_text, parse_mode=ParseMode.MARKDOWN)

@dp.message()
async def unknown_message(message: types.Message):
    await message.answer("Комменда не распознана", reply_markup=keyboard.greet_kb)

if __name__ == '__main__':
    dp.run_polling(bot)