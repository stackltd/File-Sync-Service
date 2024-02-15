import os
import sys
import time
import datetime as dt
from datetime import datetime

from requests.exceptions import ConnectionError
from dotenv import load_dotenv, find_dotenv
from loguru import logger

from uploader import UploaderToCloud


def main():
    """
    Функция синхронизации папки на локальном диске с облачным хранилищем
    :return:
    """
    all_files = []
    start = True
    stop = False
    is_changed = False
    errors = False

    load_dotenv(find_dotenv())

    path_source = os.getenv("path_source")
    path_dist = os.getenv("path_dist")
    timeout = int(os.getenv("timeout"))
    path_to_log = os.getenv("path_to_log")
    uploader = UploaderToCloud(path_source=path_source, path_dist=path_dist)
    time_reload = 5
    data_cloud_1 = datetime.now()
    cloud_scan_time_delta = 50

    logger.remove()
    format_out = "{module} <green>{time:YYYY-MM-DD HH:mm:ss,SSS}</green> {level} <level>{message}</level>"
    logger.add(sys.stdout, format=format_out, level="INFO", colorize=True)
    logger.add(path_to_log, format=format_out, level="INFO")

    while True:
        try:
            data_cloud_2 = datetime.now()
            data_cloud_delta = (data_cloud_2 - data_cloud_1).seconds
            os.chdir(path_source)
            # Получения данных из облака при старте, возникновении ошибках, или по истечении таймаута для облака
            if start or data_cloud_delta > cloud_scan_time_delta or errors:
                uploader.cloud_info = uploader.get_info()
                if not start:
                    data_cloud_1 = datetime.now()
                if uploader.cloud_info is not None:
                    message = f"Синхронизация включена. Период сканирования исходной папки: {timeout}c, " \
                              f"облака: не чаще {cloud_scan_time_delta}c."
                    if start and not errors:
                        logger.info(message)
                    start = False
                    if errors:
                        logger.info(f"Соединение восстановлено. {message}")

                    errors = False
                else:
                    raise ConnectionError

            for file in os.listdir():
                # Отключение слежения, если создан файл "0"
                if os.path.isfile(file) and file == "0":
                    os.remove("0")
                    logger.info(f"Синхронизация отключена.")
                    stop = True
                    break
                elif os.path.isfile(file):
                    all_files.append(file)
                    data_change_source = datetime.fromtimestamp(os.path.getmtime(file))
                    # Загрузка файла в облако
                    if file not in uploader.cloud_info.keys() and not errors:
                        uploader.load(file)
                        is_changed = True
                        logger.info(f"Файл {file} загружен")
                    else:
                        # Перезапись файл в облако, если в он был изменен
                        delta_tz = abs(time.timezone)  # Добавляем разницу в часовом поясе к метаданным из облака
                        delta = dt.timedelta(seconds=delta_tz)
                        data_in = uploader.cloud_info[file][:-6]
                        data_change_dist = dt.datetime.strptime(data_in, '%Y-%m-%dT%H:%M:%S') + delta
                        is_changed_file = data_change_source > data_change_dist
                        if is_changed_file:
                            uploader.load(file)
                            is_changed = True
                            logger.info(f"Файл {file} перезаписан")
            if stop:
                break
            # удаление файла из облака, если он отсутствует в папке слежения
            for file in uploader.cloud_info:
                if file not in all_files:
                    uploader.delete(file)
                    is_changed = True
                    logger.info(f'Файл {file} удален')
            # фиксация изменений
            if is_changed:
                is_changed = False
                data_cloud_1 = datetime.now()
                uploader.cloud_info = uploader.get_info()

            all_files.clear()
            time.sleep(timeout)

        except (FileNotFoundError, ConnectionError) as ex:
            info_error = ex.__repr__()
            errors = True
            if "FileNotFoundError" in info_error:
                logger.error(f"{ex}. Неверно указан путь к локальной папке")
            logger.info(f"Следующая попыка синхронизации через {time_reload} c.")
            time.sleep(time_reload)


if __name__ == "__main__":
    main()
