import os

from clouds.yandex_cloud import YandexDiskProvider

clouds = {
    "yandex": {
        "token": os.getenv("token_1"),
        "storage": YandexDiskProvider,
        "path_source": r"D:\Skillbox_Projects\asd",
        "base_url": "https://cloud-api.yandex.net/v1/disk/resources",
        "cloud_scan_time_delta": 15,
        "timeout": 15,
        "time_reload": 15,
        "path_dist": "Загрузки",
        "BASE_URL": "https://cloud-api.yandex.net/v1/disk/resources",
        "path_to_log": r"D:\Skillbox_Projects\asd\logs\yandex.log",
    },
    "google": {
        "token": os.getenv("token_2"),
        "storage": None,
        "path_source": r"",
        "cloud_scan_time_delta": 5,
        "timeout": 5,
        "time_reload": 5,
        "path_dist": "Загрузки",
        "BASE_URL": "",
        "path_to_log": r"D:\Skillbox_Projects\asd\logs\google.log",
    },
}
