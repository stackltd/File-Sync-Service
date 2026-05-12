import sys
import os
import time

from loguru import logger

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from control.cloud_control import UploaderToCloud
from control.local_control import LocalsFiles
from clouds.yandex_cloud import YandexDiskProvider

path_source = os.getenv("path_source")
timeout = int(os.getenv("timeout"))
yandex_token = os.getenv("TOKEN")
cloud_scan_time_delta = int(os.getenv("cloud_scan_time_delta"))
os.chdir(path_source)

# выбираем в качестве облака yandex disc
yandex_storage = YandexDiskProvider(yandex_token)
uploader = UploaderToCloud(yandex_storage)

# получение списка локальных файлов
LocalsFiles.get_all_local_files()


def main():
    """
    Функция синхронизации папки на локальном диске с облачным хранилищем
    :return:
    """
    load_dotenv(find_dotenv())

    path_to_log = os.getenv("path_to_log")
    time_reload = int(os.getenv("time_reload"))

    logger.remove()
    format_out = "{module} <green>{time:YYYY-MM-DD HH:mm:ss,SSS}</green> {level} <level>{message}</level>"
    logger.add(sys.stdout, format=format_out, level="INFO", colorize=True)
    logger.add(path_to_log, format=format_out, level="INFO")

    while True:
        try:
            # Инициализация, получение данных с облака
            uploader.initializing()
            # контроль папки слежения, загрузка в облако новых, или измененных файлов
            uploader.control_local_folder()
            if uploader.check_changed is None:
                break
            # удаление посторонних файлов из облака
            result = uploader.delete()
            if result is None:
                uploader.errors = True
            else:
                uploader.is_changed = True
            # завершение периода слежения, подготовка к следующему
            uploader.finishing()

        except (FileNotFoundError, AttributeError) as ex:
            info_error = ex.__repr__()
            uploader.errors = True
            if "FileNotFoundError" in info_error:
                logger.error(f"{ex}. Неверно указан путь к локальной папке")
            logger.info(f"Следующая попытка синхронизации через {time_reload} c.")
            time.sleep(time_reload)


if __name__ == "__main__":
    main()
