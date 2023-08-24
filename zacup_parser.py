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


def find_keyword(text, words) -> bool:
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

class MethodsInfoFromPage:
    @staticmethod
    def generate_URL(hosp, filter_: str, page_number: int):
        page_url = f"&pageNumber={page_number}"
        hosp_inn = hosp['inn']
        if(filter_ == "analize_data"):
            URL = f"{config.URL_MAIN}/epz/order/extendedsearch/results.html?searchString={hosp_inn}&ca=on&pc=on&pa=on{page_url}"
        elif(filter_ == "current_data"):
            URL = f"{config.URL_MAIN}/epz/order/extendedsearch/results.html?searchString={hosp_inn}&af=on{page_url}"            
    
    @staticmethod
    def get_current_page_number(next_page_number: int)->int:
        if next_page_number == 0:
            return 0
        else:
            return next_page_number - 1
    
    
    @staticmethod
    def get_URL(hospital_inn: str, filter_: str, page_number: int)->str:
        page_url = f"&pageNumber={page_number}"
        URL = f"{config.URL_MAIN}/epz/order/extendedsearch/results.html?searchString={hospital_inn}{filter_}{page_url}"
        return URL


class InfoFromSitePage(MethodsInfoFromPage):
    def __init__(self, filter_, hospital_inn, page_number):
        self.__URL = super().get_URL(hospital_inn, filter_, page_number)
        web_request = requests.get(self.__URL, headers=config.headers) # Getting a page by URL
        src =  web_request.text
        self.__soup = BeautifulSoup(src, 'lxml') # Format a page to bs4 format
        # self.__next_page = super().get_next_page_number(self.__soup)
        # self.__current_page = super().get_current_page_number(self.__next_page)
        self.__hospital_inn = hospital_inn
        self.__filter = filter_
        self.__lots = self.__soup.find_all("div", class_="search-registry-entry-block box-shadow-search-input")
        self.__col_inn: list = []
        self.__col_id: list = []
        self.__col_text: list = []
        self.__col_price: list = []
        self.__col_url: list = []


    @property
    def soup(self):
        return self.__soup

    @property
    def lots(self):
        return self.__lots

    def write_data_cols(self, text, lot, hosp_inn):
        self.__col_text.append(text)
        price = lot.find("div", class_="price-block__value").string.strip() # Цена лота
        self.__col_price.append(price)
        lot_id = lot.find("div", class_="registry-entry__header-mid__number").a.string.strip() # Номер лота
        self.__col_id.append(lot_id)
        lot_url = config.URL_MAIN + lot.find("div", class_="registry-entry__header-mid__number").a["href"] # Ссылка на лот
        self.__col_url.append(lot_url)
        self.__col_inn.append(hosp_inn)
        logger.info(f"INN: {hosp_inn.encode('UTF-8')}, PRICE: {price.encode('UTF-8')}, LOT: {lot_id.encode('UTF-8')}")

    def write_data_to_xlsxfile(self):
        df = pd.DataFrame({
            "ИНН": self.__col_inn,
            "Номер лота": self.__col_id,
            "Лот": self.__col_text,
            "Цена": self.__col_price,
            "URL": self.__col_url,
        })

        df.to_excel("./ex.xlsx", index=False)



def create_file(filter_: str, key_words: list)->None:
    with open(config.args_file) as file:
        templates = json.load(file)

    for hospital in templates['hospitals']:
        current_page = 1
        isNoInnOnPage = False
        hospital_inn = hospital['inn']

        pbar = tqdm(total=100, desc=hospital['name'], unit="page")
        while(current_page != 0):
            pbar.update(1)
            sp = InfoFromSitePage(filter_, hospital_inn, current_page)
            for lot in sp.lots:
                if not check_inn_for_finded_lot(lot, hospital_inn):
                    isNoInnOnPage = True
                    break
                
                text = lot.find("div", class_="registry-entry__body-value").string # Название лота
                if(text is not None):
                    text = text.lower()

                if(find_keyword(text, key_words)):
                    sp.write_data_cols(text, lot, hospital_inn)
            
            if isNoInnOnPage:
                break
            current_page = get_next_page_number(sp.soup)
        pbar.close()
    sp.write_data_to_xlsxfile()

