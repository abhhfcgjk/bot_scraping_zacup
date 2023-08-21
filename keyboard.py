from aiogram.types import (

    KeyboardButton,

    Message,

    ReplyKeyboardMarkup,

    ReplyKeyboardRemove,

)

button1 = KeyboardButton(text="Добавить больницу")
button2 = KeyboardButton(text="Удалить больницу")
button3 = KeyboardButton(text="Получить файл")
button4 = KeyboardButton(text="Список больниц")
button5 = KeyboardButton(text="Изменить ключевые слова")
button6 = KeyboardButton(text="Изменить ИНН больницы")

kb_arr1 = [
    [
        button1, button2
    ],
    [
        button3, button4
    ],
    [
        button5, button6
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