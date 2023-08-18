TOKEN = "6578568079:AAH_L848xCipERsgyJnc9-GfCZsJf-pnrqQ"
EX_FILE = "ex.xlsx"

URL_MAIN = "https://zakupki.gov.ru"

args_file = "arg.json"
headers = {
    "Host": "zakupki.gov.ru",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
    "Accept": "image/avif,image/webp,*/*",
    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Cookie": "doNotAdviseToChangeLocationWhenIosReject=true",

}

import json

def init_json_file():
    print("JSON init")
    data = {
        "hospitals":[]
    }
    with open(args_file, "w") as file:
        json.dump(data,file)

#https://surik00.gitbooks.io/aiogram-lessons/content/