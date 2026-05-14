from typing import BinaryIO, Dict

import requests

from clouds.base import CloudStorage


class YandexDiskProvider(CloudStorage):

    def __init__(self, token: str, base_url: str, path_dist: str):
        self.BASE_URL = base_url
        self.path_dist = path_dist
        self.HEADERS = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"OAuth {token}",
        }

    def __str__(self):
        return "Яндекс-диск"

    def get_files(self, limit: int) -> Dict[str, str]:
        url = f"{self.BASE_URL}?path={self.path_dist}&limit={limit}"
        result = requests.get(url=url, headers=self.HEADERS).json()
        meta_info = result["_embedded"]["items"]
        names = {info["name"]: info["modified"] for info in meta_info}
        return names

    def upload(self, file_name, file_obj: BinaryIO, overwrite: bool = False):
        url = f"{self.BASE_URL}/upload?path={self.path_dist}/{file_name}&overwrite={overwrite}"
        result_1 = requests.get(url=url, headers=self.HEADERS)
        result_2 = requests.put(result_1.json()["href"], files={"file": file_obj})
        if result_1.status_code == 200 and result_2.status_code == 201:
            return True

    def delete(self, file_name):
        url = f"{self.BASE_URL}?path={self.path_dist}/{file_name}"
        result = requests.delete(url=url, headers=self.HEADERS)
        if result.status_code == 204:
            return True
