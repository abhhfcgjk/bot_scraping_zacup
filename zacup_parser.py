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

def get_next_page_number(soup) -> int:
    arrow = soup.find("a", class_="paginator-button paginator-button-next")
    if(arrow is None):
        return 0
    return int(arrow["data-pagenumber"])

def check_inn_for_finded_lot(lot, inn: str)->bool:
    lot_organization_inn = lot.find('div', class_='registry-entry__body-href').a['href'].split('=')[-1]
    if(inn!=lot_organization_inn):
        return False
    else:
        return True

def write_data_to_xlsxfile(col_inn:list, col_id:list, col_text:list, col_price:list, col_url:list):
    df = pd.DataFrame({
        "ИНН": col_inn,
        "Номер лота": col_id,
        "Лот": col_text,
        "Цена": col_price,
        "URL": col_url,
    })

    df.to_excel("./ex.xlsx", index=False)


def create_file(filt: str, key_words: list)->None:
    col_id, col_text, col_price, col_url, col_inn = [], [], [], [], [] # Задаем колонки для записи в таблицу
    with open(config.args_file) as file:
        templates = json.load(file)

    for hosp in templates["hospitals"]: # Перебираем все бальницы
        hosp_name = hosp['name']
        page_number = 1 # определяем переменную для пагинации
        isNoInnOnPage = False

        pbar = tqdm(total=100, desc=hosp_name, unit="page")

        while(page_number!=0):
            pbar.update(1)

            page_url = f"&pageNumber={page_number}"

            hosp_inn = hosp["inn"]
            if(filt == "analize_data"):
                URL = f"{config.URL_MAIN}/epz/order/extendedsearch/results.html?searchString={hosp_inn}&ca=on&pc=on&pa=on{page_url}"
            elif(filt == "current_data"):
                URL = f"{config.URL_MAIN}/epz/order/extendedsearch/results.html?searchString={hosp_inn}&af=on{page_url}"
            

            web_request = requests.get(URL, headers=config.headers) # Getting a page by URL
            src =  web_request.text

            soup = BeautifulSoup(src, 'lxml') # Format a page to bs4 format

            lots = soup.find_all("div", class_="search-registry-entry-block box-shadow-search-input") # Находим все карточки с лотами

            if(len(lots) == 0): # Если Страница пустая, то выходим из цикла для больницы
                if(page_number==1):
                    logger.warning("NO DATA")
                break
            for lot in lots:
                if check_inn_for_finded_lot(lot, hosp_inn) == False:
                    isNoInnOnPage = True
                    break

                text = lot.find("div", class_="registry-entry__body-value").string # Название лота
                if(text is not None):
                    text = text.lower()

                if(find_word(text, key_words)):
                    col_text.append(text)
                    price = lot.find("div", class_="price-block__value").string.strip() # Цена лота
                    col_price.append(price)
                    lot_id = lot.find("div", class_="registry-entry__header-mid__number").a.string.strip() # Номер лота
                    col_id.append(lot_id)
                    lot_url = config.URL_MAIN + lot.find("div", class_="registry-entry__header-mid__number").a["href"] # Ссылка на лот
                    col_url.append(lot_url)
                    col_inn.append(hosp_inn)
                    logger.info(f"INN: {hosp_inn.encode('UTF-8')}, PRICE: {price.encode('UTF-8')}, LOT: {lot_id.encode('UTF-8')}")
            
            if isNoInnOnPage:   # Если выводятся больница с неверным ИНН,
                break           # то зовершаем парсинг для больницы
            page_number = get_next_page_number(soup)
        pbar.close()
    write_data_to_xlsxfile(col_inn, col_id, col_text, col_price, col_url)