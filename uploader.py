import os

import requests
from dotenv import dotenv_values
from requests.exceptions import ConnectionError
from loguru import logger

BASE_URL = 'https://cloud-api.yandex.net/v1/disk/resources'
TOKEN = dotenv_values()["TOKEN"]
HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {TOKEN}'}


class UploaderToCloud:

    def __init__(self, path_source, path_dist):
        self.path_source = path_source
        self.path_dist = path_dist
        self.cloud_info = {}
        self.file_for_delete = ""

    def get_info(self):
        url = f'{BASE_URL}?path={self.path_dist}'
        try:
            result = requests.get(url=url, headers=HEADERS).json()
            meta_info = result["_embedded"]["items"]
            names = {info["name"]: info["modified"] for info in meta_info}
            return names
        except KeyError:
            logger.error("Ошибка при получении данных с Яндекс-диска."
                         " Возможно, в облаке отсутствует указанная папка, или не найден токен")
        except ConnectionError:
            logger.error("Ошибка при получении данных с Яндекс-диска. Не удается установить связь с облаком")

    def load_file(self, file_name, overwrite=False):
        url = f'{BASE_URL}/upload?path={self.path_dist}/{file_name}&overwrite={overwrite}'
        try:
            result = requests.get(url=url, headers=HEADERS).json()
            path_to_local_file = os.path.join(self.path_source, file_name)
            with open(path_to_local_file, 'rb') as f:
                requests.put(result['href'], files={'file': f})
            return True
        except (KeyError, ConnectionError) as ex:
            info_error = ex.__repr__()
            if "ConnectionError" in info_error and overwrite:
                logger.error(f"Не удалось перезаписать файл {file_name}. Проверьте соединение.")
            elif not overwrite:
                logger.error(f"Не удалось загрузить файл {file_name}. Проверьте соединение.")

    def delete(self, list_local_folder):
        """
        Функция удаления файла из облака, если он отсутствует в папке слежения.
        :param list_local_folder:
        :return: При успешной работе функции возвращает True, иначе - False
        """
        try:
            check_delete = False
            for file_name in self.cloud_info:
                url = f'{BASE_URL}?path={self.path_dist}/{file_name}'
                if file_name not in list_local_folder:
                    self.file_for_delete = file_name
                    requests.delete(url=url, headers=HEADERS)
                    logger.info(f'Файл {file_name} удален')
                    check_delete = True
            return check_delete
        except ConnectionError:
            logger.error(f"Ошибка соединения. Не удалось удалить файл {self.file_for_delete}.")
            return

if __name__ == "__main__":
    pass
