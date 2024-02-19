import os
import time

from loguru import logger

import datetime as dt
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from sync_utils.uploader import UploaderToCloud

path_source = os.getenv("path_source")
path_dist = os.getenv("path_dist")
timeout = int(os.getenv("timeout"))
path_to_log = os.getenv("path_to_log")
cloud_scan_time_delta = 50
os.chdir(path_source)
uploader = UploaderToCloud(path_source=path_source, path_dist=path_dist)
uploader.get_all_local_files()


def initializing(start_program, data_time, error_check):
    """
    Функция получения данных из облака при старте, возникновении ошибках, или по истечении таймаута для облака.
    :param start_program: Флаг старта программы
    :param data_time: начальная дата для отсчета таймаута контроля папки облака
    :param error_check: флаг появления ошибки
    :return:
    """
    data_cloud_2 = datetime.now()
    data_cloud_delta = (data_cloud_2 - data_time).seconds
    if start_program or data_cloud_delta > cloud_scan_time_delta or error_check:
        limit_len_dist = len(uploader.all_files) + 5
        uploader.cloud_info = uploader.get_info(limit=limit_len_dist)
        if not start_program:
            data_time = datetime.now()
        if uploader.cloud_info is not None:
            message = f"Синхронизация включена. Период сканирования исходной папки: {timeout}c, " \
                      f"облака: не чаще {cloud_scan_time_delta}c."
            if start_program and not error_check:
                logger.info(message)
            start_program = False
            if error_check:
                logger.info(f"Соединение восстановлено. {message}")

            error_check = False

    return start_program, data_time, error_check


def control_local_folder(check_changed, errors):
    for file in os.listdir():
        # Отключение слежения, если создан файл "0"
        if os.path.isfile(file) and file == "0":
            os.remove("0")
            logger.info(f"Синхронизация отключена.")
            return
        elif os.path.isfile(file):
            data_change_source = datetime.fromtimestamp(os.path.getmtime(file))
            # Загрузка файла в облако
            if file not in uploader.cloud_info.keys() and not errors:
                is_loaded = uploader.load_file(file)
                if is_loaded:
                    check_changed = True
                    logger.info(f"Файл {file} загружен")
            else:
                # Перезапись файл в облако, если в он был изменен
                delta_tz = abs(time.timezone)  # Добавляем разницу в часовом поясе к метаданным из облака
                delta = dt.timedelta(seconds=delta_tz)
                data_in = uploader.cloud_info[file][:-6]
                data_change_dist = dt.datetime.strptime(data_in, '%Y-%m-%dT%H:%M:%S') + delta
                is_changed_file = data_change_source > data_change_dist
                if is_changed_file:
                    is_loaded = uploader.load_file(file, overwrite=True)
                    if is_loaded:
                        check_changed = True
                        logger.info(f"Файл {file} перезаписан")
    return check_changed


def delete():
    result = uploader.delete(list_local_folder=uploader.all_files)
    return result


def finishing(check_changed, data_time, error_check):
    if check_changed:
        check_changed = False
        data_time = datetime.now()
        limit_len_dist = len(uploader.all_files) + 5
        uploader.cloud_info = uploader.get_info(limit=limit_len_dist)
        if uploader.cloud_info is None:
            error_check = True
    uploader.get_all_local_files()
    time.sleep(timeout)
    return check_changed, data_time, error_check
