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

@dp.message(F.text == "cancel", StateFilter(any_state))
@dp.message(Command(commands="cancel"), StateFilter(any_state))
async def process_cancel(message: types.Message, state: FSMContext):
    # last_state = await state.get_state()
    # user_id = message.from_user.id
    # bot_logger.info(f"User: {user_id}, Action: cancel, State: {last_state}")
    await state.clear()
    await message.reply("Отменено", reply_markup=keyboard.greet_kb)

@dp.message(F.text == "Список больниц")
@dp.message(Command(commands="print"))
async def process_print_hospitals(message: types.Message):
    # user_id = message.from_user.id
    # bot_logger.info(f"User: {user_id}, Action: print, State: {None}")
    msg: str = bj.print_all_hospitals()
    if(len(msg)!=0):
        await message.answer(msg, reply_markup=keyboard.greet_kb)
    else:
        await message.answer("Больниц пока не добавлено")


@dp.message(StateFilter(default_state), F.text=="Добавить больницу")
@dp.message(StateFilter(default_state), Command(commands=["add"]))
async def add_hospital(message: types.Message, state: FSMContext):
    # last_state = await state.get_state()
    # user_id = message.from_user.id
    # bot_logger.info(f"User: {user_id}, Action: add, State: {last_state}")
    await state.set_state(Hospital.title)
    await message.reply("Введите название больницы(какое будет удобнее)", reply_markup=keyboard.cancel_kb)

@dp.message(StateFilter(default_state), F.text=="Удалить больницу")
@dp.message(StateFilter(default_state), Command(commands=["remove"]))
async def del_hospital(message: types.Message, state: FSMContext):
    # last_state = await state.get_state()
    # user_id = message.from_user.id
    # bot_logger.info(f"User: {user_id}, Action: rm_command, State: {last_state}")
    await state.set_state(HospitalDeleter.title)
    await message.reply("Введите название больницы")

@dp.message(StateFilter(HospitalDeleter.title))
async def process_delete_hospital(message: types.Message, state: FSMContext):
    # last_state = await state.get_state()
    # user_id = message.from_user.id
    # bot_logger.info(f"User: {user_id}, Action: remove_hospital, State: {last_state}")
    hosp_name = message.text.strip()
    ans:bool = bj.del_hospital_json(hosp_name)
    await state.clear()
    if(ans):
        await message.answer("Больница удалена", reply_markup=keyboard.greet_kb)
    else:
        await message.answer("Такой больницы нет в списке", reply_markup=keyboard.greet_kb)

@dp.message(StateFilter(Hospital.title))
async def process_title(message: types.Message, state: FSMContext):
    # last_state = await state.get_state()
    # user_id = message.from_user.id
    # bot_logger.info(f"User: {user_id}, Action: input_title, State: {last_state}")
    global hospital_title
    hospital_title = message.text.strip()
    await message.reply("Введите ИНН больницы", reply_markup=keyboard.cancel_kb)
    await state.set_state(Hospital.inn)

@dp.message(StateFilter(Hospital.inn))
async def process_inn(message: types.Message, state: FSMContext):
    # last_state = await state.get_state()
    # user_id = message.from_user.id
    # bot_logger.info(f"User: {user_id}, Action: input_inn, State: {last_state}")
    await state.update_data(inn=message.text.strip())
    await message.reply("Введите ключевые слова через запятую",reply_markup=keyboard.cancel_kb)
    await state.set_state(Hospital.key_words)

@dp.message(StateFilter(Hospital.key_words))
async def process_key_words(message: types.Message, state: FSMContext):
    # last_state = await state.get_state()
    # user_id = message.from_user.id
    # bot_logger.info(f"User: {user_id}, Action: input_keywords, State: {last_state}")
    keys = message.text.split(",")
    for i in range(len(keys)):
        keys[i] = keys[i].strip().lower()
    await state.update_data(keys_words=keys)
    hospital[hospital_title] = await state.get_data()
    bj.add_hospital(hospital)
    hospital.clear()
    await state.clear()
    await message.answer("Больница добавлена", reply_markup=keyboard.greet_kb)
    # bot_logger.info(f"User: {user_id}, Action: hospital_added, State: {last_state}")

@dp.message(F.text == "Получить файл с урожаем")
@dp.message(Command(commands=["get"]))
async def process_get_file(message: types.Message):
    # user_id = message.from_user.id
    # bot_logger.info(f"User: {user_id}, Action: get_file, State: {None}")
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
    # user_id = message.from_user.id
    # bot_logger.info(f"User: {user_id}, Action: unknown_message, Message: {message}")
    await message.answer("Комменда не распознана", reply_markup=keyboard.greet_kb)


if __name__ == '__main__':
    dp.run_polling(bot)