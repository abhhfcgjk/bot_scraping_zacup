# необходимо добавить перебор по названиям больниц
from tqdm import tqdm

from bs4 import BeautifulSoup
import requests
import pandas as pd
import json

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# настройка обработчика и форматировщика для logger2
handler = logging.FileHandler(f"{__name__}.log", mode='w')
formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")

# добавление форматировщика к обработчику
handler.setFormatter(formatter)
# добавление обработчика к логгеру
logger.addHandler(handler)

import config

def find_word(text, words) -> bool:
    if(text is None):
        return False
    ans = False
    for word in words:
        ans = (text.find(word) != -1)
        if(ans):
            break
    return ans



def create_file(reg: str)->None:
    col_id, col_text, col_price, col_url, col_inn = [], [], [], [], [] # Задаем колонки для записи в таблицу
    with open(config.args_file) as file:
        templates = json.load(file)

    for hosp in templates["hospitals"]: # Перебираем все бальницы
        hosp_title = list(hosp.keys())[0] # Имя больницы
        hospital = hosp[hosp_title] # больницы
        page_number = 0 # определяем переменную для пагинации

        print(hosp_title)
        pbar = tqdm(total=100)

        while(True and page_number < 100):
            page_number += 1 # Переходим по странице
            page_url = f"&pageNumber={page_number}"

            inn = hospital["inn"]
            key_words = hospital["keys_words"]

            URL = f"{config.URL_MAIN}/epz/order/extendedsearch/results.html?searchString={inn}&ca=on&pc=on&pa=on{page_url}"
            #URL = f"{config.URL_MAIN}/epz/order/extendedsearch/results.html?searchString={inn}&af=on{page_url}"
            # "7728008953" # Генерируем URL для заданной странице

            web_request = requests.get(URL, headers=config.headers) # Getting a page by URL
            src =  web_request.text

            soup = BeautifulSoup(src, 'lxml') # Format a page to bs4 format
            # print(soup)
            lots = soup.find_all("div", class_="search-registry-entry-block box-shadow-search-input") # Находим все карточки с лотами
            if(len(lots) == 0):############## # Если Страница пустая, то выходим из цикла для больницы
                if(page_number==1):
                    logger.warning("NO DATA")
                break
            
            pbar.update(1)

            for lot in lots:
                # print(lot)
                text = lot.find("div", class_="registry-entry__body-value") # Название лота
                if(text is not None):
                    text = text.string.lower()
                #print(text)
                if(find_word(text, key_words)):
                    col_text.append(text)
                    price = lot.find("div", class_="price-block__value").string.strip() # Цена лота
                    col_price.append(price)
                    lot_id = lot.find("div", class_="registry-entry__header-mid__number").a.string.strip() # Номер лота
                    col_id.append(lot_id)
                    lot_url = config.URL_MAIN + lot.find("div", class_="registry-entry__header-mid__number").a["href"] # Ссылка на лот
                    col_url.append(lot_url)
                    col_inn.append(inn)
                    logger.info(f"INN: {inn.encode('UTF-8')}, PRICE: {price.encode('UTF-8')}, LOT: {lot_id.encode('UTF-8')}")

        pbar.close()
    df = pd.DataFrame({
        "ИНН": col_inn,
        "Номер лота": col_id,
        "Лот": col_text,
        "Цена": col_price,
        "URL": col_url,
    })

    df.to_excel("./ex.xlsx", index=False)

