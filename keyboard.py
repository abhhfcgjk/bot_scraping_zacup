from aiogram.types import (

    KeyboardButton,

    ReplyKeyboardMarkup,

    ReplyKeyboardRemove,

    InlineKeyboardButton

)
from aiogram.utils.keyboard import InlineKeyboardBuilder

button1 = KeyboardButton(text="Добавить больницу")
button2 = KeyboardButton(text="Удалить больницу")
button3 = KeyboardButton(text="Получить файл")
button4 = KeyboardButton(text="Список больниц")
# button5 = KeyboardButton(text="Изменить ключевые слова")
button6 = KeyboardButton(text="Изменить ИНН больницы")
# button7 = KeyboardButton(text="Добавить ключевые слова")

kb_arr1 = [
    [
        button1, button2
    ],
    [
        button3, button4
    ],
    [
        button6
    ]
]
greet_kb = ReplyKeyboardMarkup(keyboard=kb_arr1)

buttonCancel = KeyboardButton(text="cancel")
kb_arr2 = [
    [
        buttonCancel
    ]
]
cancel_kb = ReplyKeyboardMarkup(keyboard=kb_arr2)


button_cur_zacup = InlineKeyboardButton(text="Определение Поставщика", callback_data="&af=on")
button_analize_zacup = InlineKeyboardButton(text="Завершенный Закупки", callback_data="&ca=on&pc=on&pa=on")

file_kb = InlineKeyboardBuilder()
file_kb.row(button_cur_zacup, button_analize_zacup)



