import os
import sys
import time
import datetime as dt
from datetime import datetime

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
    cloud_scan_time_delta = 10

    logger.remove()
    format_out = "{module} <green>{time:YYYY-MM-DD HH:mm:ss,SSS}</green> {level} <level>{message}</level>"
    logger.add(sys.stdout, format=format_out, level="INFO", colorize=True)
    logger.add(path_to_log, format=format_out, level="INFO")

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
        os.chdir(path_source)
        if start_program or data_cloud_delta > cloud_scan_time_delta or error_check:
            uploader.cloud_info = uploader.get_info()
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

    def control_local_folder(check_changed):
        for file in os.listdir():
            # Отключение слежения, если создан файл "0"
            if os.path.isfile(file) and file == "0":
                os.remove("0")
                logger.info(f"Синхронизация отключена.")
                return
            elif os.path.isfile(file):
                all_files.append(file)
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

    def finishing(check_changed, data_time, error_check):
        if check_changed:
            check_changed = False
            data_time = datetime.now()
            uploader.cloud_info = uploader.get_info()
            if uploader.cloud_info is None:
                error_check = True
        all_files.clear()
        time.sleep(timeout)
        return check_changed, data_time, error_check

    while True:
        try:
            # Инициализация, получение данных с облака
            start, data_cloud_1, errors = initializing(start_program=start, data_time=data_cloud_1, error_check=errors)
            # контроль папки слежения, загрузка в облаков новых, или измененных файлов
            result = control_local_folder(check_changed=is_changed)
            if result is None:
                break
            else:
                is_changed = result
            # удаление посторонних файлов из облака
            result = uploader.delete(list_local_folder=all_files)
            if result is None:
                errors = True
            else:
                is_changed = True
            # завершение периода слежения, подготовка к следующему
            is_changed, data_cloud_1, errors = finishing(is_changed, data_cloud_1, errors)

        except (FileNotFoundError, AttributeError) as ex:
            info_error = ex.__repr__()
            errors = True
            if "FileNotFoundError" in info_error:
                logger.error(f"{ex}. Неверно указан путь к локальной папке")
            logger.info(f"Следующая попытка синхронизации через {time_reload} c.")
            time.sleep(time_reload)


if __name__ == "__main__":
    main()
