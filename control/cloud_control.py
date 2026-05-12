import os
import time
from datetime import datetime
import datetime as dt

from requests.exceptions import ConnectionError
from loguru import logger

from clouds.base import CloudStorage
from control.local_control import LocalsFiles

cloud_scan_time_delta = int(os.getenv("cloud_scan_time_delta"))
timeout = int(os.getenv("timeout"))


class UploaderToCloud:

    def __init__(self, storage: CloudStorage):
        self.storage = storage
        self.cloud_info = {}  # {"name": "время создания/изменения"}
        self.file_for_delete = ""
        self.start_program = True  # Флаг старта программы
        self.data_time = (
            datetime.now()
        )  # начальная дата для отсчета таймаута контроля папки облака
        self.error_check = False  # флаг появления ошибки
        self.check_changed = False
        self.limit_len_dist = 0

    def initializing(self):
        """
        Функция получения данных из облака при старте, возникновении ошибках, или по истечении таймаута для облака.
        """
        data_cloud_2 = datetime.now()
        data_cloud_delta = (data_cloud_2 - self.data_time).seconds
        if (
            self.start_program
            or data_cloud_delta > cloud_scan_time_delta
            or self.error_check
        ):
            self.limit_len_dist = len(LocalsFiles.all_files) + 5
            self.cloud_info = self.__get_files_list(limit=self.limit_len_dist)
            if not self.start_program:
                self.data_time = datetime.now()
            if self.cloud_info is not None:
                message = (
                    f"Синхронизация включена. Период сканирования исходной папки: {timeout}c, "
                    f"облака: не чаще {cloud_scan_time_delta}c."
                )
                if self.start_program and not self.error_check:
                    logger.info(message)
                self.start_program = False
                if self.error_check:
                    logger.info(f"Соединение восстановлено. {message}")

                self.error_check = False

    def control_local_folder(self):
        for file in os.listdir():
            # Отключение слежения, если создан файл "0"
            if os.path.isfile(file) and file == "0":
                os.remove("0")
                logger.info(f"Синхронизация отключена.")
                return
            elif os.path.isfile(file):
                data_change_source = datetime.fromtimestamp(os.path.getmtime(file))
                # Загрузка файла в облако
                if file not in self.cloud_info.keys() and not self.error_check:
                    is_loaded = self.__load_file_control(file)
                    if is_loaded:
                        self.check_changed = True
                        logger.info(f"Файл {file} загружен")
                else:
                    # Перезапись файл в облако, если в он был изменен
                    delta_tz = abs(
                        time.timezone
                    )  # Добавляем разницу в часовом поясе к метаданным из облака
                    delta = dt.timedelta(seconds=delta_tz)
                    data_in = self.cloud_info[file][:-6]
                    data_change_dist = (
                        dt.datetime.strptime(data_in, "%Y-%m-%dT%H:%M:%S") + delta
                    )
                    is_changed_file = data_change_source > data_change_dist
                    if is_changed_file:
                        is_loaded = self.__load_file_control(file, overwrite=True)
                        if is_loaded:
                            self.check_changed = True
                            logger.info(f"Файл {file} перезаписан")

    def finishing(self):
        if self.check_changed:
            self.check_changed = False
            self.data_time = datetime.now()
            self.limit_len_dist = len(LocalsFiles.all_files) + 5
            self.cloud_info = self.__get_files_list(limit=self.limit_len_dist)
            if self.cloud_info is None:
                self.error_check = True
        LocalsFiles.get_all_local_files()
        time.sleep(timeout)

    def __get_files_list(self, limit):
        try:
            names = self.storage.get_files(limit)
            return names
        except KeyError:
            logger.error(
                f"Ошибка при получении данных с {self.storage}."
                " Возможно, в облаке отсутствует указанная папка, или не найден токен"
            )
        except ConnectionError:
            logger.error(
                f"Ошибка при получении данных с {self.storage}. Не удается установить связь с облаком"
            )

    def __load_file_control(self, file_name, overwrite=False):
        print(file_name)
        try:
            result = self.storage.upload(file_name, overwrite)
            return result
        except (KeyError, ConnectionError) as ex:
            info_error = ex.__repr__()
            if "ConnectionError" in info_error and overwrite:
                logger.error(
                    f"Не удалось перезаписать файл {file_name}. Проверьте соединение."
                )
            elif not overwrite:
                logger.error(
                    f"Не удалось загрузить файл {file_name}. Проверьте соединение."
                )

    def delete(self):
        cloud_files = self.cloud_info
        try:
            result = self.storage.delete(
                cloud_files, list_local_folder=LocalsFiles.all_files
            )
            return result
        except ConnectionError:
            logger.error(
                f"Ошибка соединения. Не удалось удалить файл {self.file_for_delete}."
            )
            return


if __name__ == "__main__":
    pass
