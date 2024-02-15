import os

import requests
from dotenv import dotenv_values
from requests.exceptions import ConnectionError
from loguru import logger

BASE_URL = 'https://cloud-api.yandex.net/v1/disk/resources'
TOKEN = dotenv_values()["TOKEN"]
os.environ["DEBUSSY"] = "1"
HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {TOKEN}'}


class UploaderToCloud:

    def __init__(self, path_source, path_dist):
        self.path_source = path_source
        self.path_dist = path_dist
        self.cloud_info = {}

    def get_info(self):
        try:
            url = f'{BASE_URL}?path={self.path_dist}'
            result = requests.get(url=url, headers=HEADERS).json()
            meta_info = result["_embedded"]["items"]
            names = {info["name"]: info["modified"] for info in meta_info}
            return names
        except KeyError:
            logger.error("Ошибка при получении данных с Яндекс-диска."
                         " Возможно, в облаке отсутствует указанная папка, или не найден токен")
            return None
        except ConnectionError:
            logger.error("Ошибка при получении данных с Яндекс-диска. Не удается установить связь с облаком")
            return None

    def load(self, file_name) -> None:
        try:
            url = f'{BASE_URL}/upload?path={self.path_dist}/{file_name}&overwrite=True'
            result = requests.get(url=url, headers=HEADERS).json()
            path_to_local_file = os.path.join(self.path_source, file_name)
            with open(path_to_local_file, 'rb') as f:
                requests.put(result['href'], files={'file': f})
        except KeyError:
            message = result["message"]
            if message == "Не авторизован.":
                logger.error(f"Не удалось загрузить файл. Ошибка авторизации. Проверьте ваш токен")
            else:
                logger.error(f"Не удалось загрузить файл. Ошибка: {message}")

    def delete(self, file_name) -> None:
        try:
            url = f'{BASE_URL}?path={self.path_dist}/{file_name}'
            requests.delete(url=url, headers=HEADERS)
        except ConnectionError:
            logger.error("Ошибка соединения. Не удалось удалить файл.")


if __name__ == "__main__":
    pass
