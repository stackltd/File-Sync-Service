import os

import requests
from loguru import logger

from clouds.base import CloudStorage

BASE_URL = "https://cloud-api.yandex.net/v1/disk/resources"
path_source = os.getenv("path_source")
path_dist = os.getenv("path_dist")


class YandexDiskProvider(CloudStorage):

    def __init__(self, token: str):
        self.HEADERS = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"OAuth {token}",
        }

    def __str__(self):
        return "Яндекс-диск"

    def get_files(self, limit: int):
        url = f"{BASE_URL}?path={path_dist}&limit={limit}"
        result = requests.get(url=url, headers=self.HEADERS).json()
        meta_info = result["_embedded"]["items"]
        names = {info["name"]: info["modified"] for info in meta_info}
        return names

    def upload(self, file_name, overwrite: bool = False):
        url = f"{BASE_URL}/upload?path={path_dist}/{file_name}&overwrite={overwrite}"
        result = requests.get(url=url, headers=self.HEADERS).json()
        path_to_local_file = os.path.join(path_source, file_name)
        with open(path_to_local_file, "rb") as f:
            requests.put(result["href"], files={"file": f})
        return True

    def delete(self, cloud_files, list_local_folder):
        for file_name in cloud_files:
            url = f"{BASE_URL}?path={path_dist}/{file_name}"
            if file_name not in list_local_folder:
                self.file_for_delete = file_name
                requests.delete(url=url, headers=self.HEADERS)
                logger.info(f"Файл {file_name} удален")
        else:
            return True
