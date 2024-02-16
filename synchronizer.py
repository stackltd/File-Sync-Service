import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv, find_dotenv
from loguru import logger

from sync_utils import utils


def main():
    """
    Функция синхронизации папки на локальном диске с облачным хранилищем
    :return:
    """
    start = True
    is_changed = False
    errors = False
    load_dotenv(find_dotenv())

    path_to_log = os.getenv("path_to_log")
    time_reload = 5
    data_cloud_1 = datetime.now()

    logger.remove()
    format_out = "{module} <green>{time:YYYY-MM-DD HH:mm:ss,SSS}</green> {level} <level>{message}</level>"
    logger.add(sys.stdout, format=format_out, level="INFO", colorize=True)
    logger.add(path_to_log, format=format_out, level="INFO")

    while True:
        try:
            # Инициализация, получение данных с облака
            start, data_cloud_1, errors = utils.initializing(start_program=start, data_time=data_cloud_1,
                                                             error_check=errors)
            # контроль папки слежения, загрузка в облако новых, или измененных файлов
            result = utils.control_local_folder(check_changed=is_changed, errors=errors)
            if result is None:
                break
            else:
                is_changed = result
            # удаление посторонних файлов из облака
            result = utils.delete()
            if result is None:
                errors = True
            else:
                is_changed = True
            # завершение периода слежения, подготовка к следующему
            is_changed, data_cloud_1, errors = utils.finishing(is_changed, data_cloud_1, errors)

        except (FileNotFoundError, AttributeError) as ex:
            info_error = ex.__repr__()
            errors = True
            if "FileNotFoundError" in info_error:
                logger.error(f"{ex}. Неверно указан путь к локальной папке")
            logger.info(f"Следующая попытка синхронизации через {time_reload} c.")
            time.sleep(time_reload)


if __name__ == "__main__":
    main()
