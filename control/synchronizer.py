import os
import time
from datetime import datetime
import datetime as dt

from requests.exceptions import ConnectionError
from loguru import logger

from clouds.base import CloudStorage
from locals.local_storage import LocalsFiles
from settings import exit_from_program, _file_signals


class UploaderToCloud:

    def __init__(
        self,
        file_storage: LocalsFiles,
        storage: CloudStorage,
        cloud_scan_time_delta: int,
        timeout: int,
        path_source: str,
    ):

        self.cloud_scan_time_delta = cloud_scan_time_delta
        self.timeout = timeout
        self.path_source = path_source
        self.file_list = []

        self.file_storage = file_storage
        self.storage = storage
        self.cloud_info = {}  # {"name": "время создания/изменения"}
        self.start_program = True  # Флаг старта программы
        self.data_time = (
            datetime.now()
        )  # начальная дата для отсчета таймаута контроля папки облака
        self.error_check = False  # флаг появления ошибки
        self.check_changed = False
        self.limit_len_dist = 0
        self.pause = False

    def _initializing(self):
        """
        Функция получения данных из облака при старте, возникновении ошибки, или по истечении таймаута для облака.
        """
        self.file_list = self.file_storage.get_all_local_files()

        data_cloud_2 = datetime.now()
        data_cloud_delta = (data_cloud_2 - self.data_time).seconds
        if (
            self.start_program
            or data_cloud_delta > self.cloud_scan_time_delta
            or self.error_check
        ):
            self.limit_len_dist = len(self.file_list) + 5
            self.cloud_info = self.storage.get_files(limit=self.limit_len_dist)
            if not self.start_program:
                self.data_time = datetime.now()
            if self.cloud_info is not None:
                message = (
                    f"Синхронизация включена. Период сканирования исходной папки: {self.timeout}c, "
                    f"облака: не чаще {self.cloud_scan_time_delta}c."
                )
                if self.start_program and not self.error_check:
                    logger.info(message)
                self.start_program = False
                if self.error_check:
                    logger.info(f"Соединение восстановлено. {message}")

                self.error_check = False

    def _finishing(self):
        """завершение периода слежения, подготовка к следующем"""
        if self.check_changed:
            self.check_changed = False
            self.data_time = datetime.now()
            self.limit_len_dist = len(self.file_list) + 5
            self.cloud_info = self.storage.get_files(limit=self.limit_len_dist)
            if self.cloud_info is None:
                self.error_check = True
        self.file_list = self.file_storage.get_all_local_files()
        time.sleep(self.timeout)

    def _upload_file_control(self, file_name, overwrite=False):
        path_to_local_file = os.path.join(self.path_source, file_name)
        try:
            with open(path_to_local_file, "rb") as file_obj:
                result = self.storage.upload(file_name, file_obj, overwrite)
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

    def _mode_control(self, file_signal):
        message = _file_signals[file_signal]
        self.file_storage.delete(file_signal)
        logger.info(message)
        if file_signal == exit_from_program:
            exit(0)
        self.pause = not int(file_signal)

    def check_local_folder(self):
        """Проверка локальной папки, загрузка в облако новых, или измененных файлов"""
        self._initializing()
        for file in self.file_list:
            # Отключение слежения, если создан файл "0"
            if file in _file_signals:
                self._mode_control(file)
            elif not self.pause:
                last_modified_time = self.file_storage.get_last_modified_time(file)
                data_change_source = datetime.fromtimestamp(last_modified_time)
                # Загрузка файла в облако
                if file not in self.cloud_info.keys() and not self.error_check:
                    is_loaded = self._upload_file_control(file)
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
                        is_loaded = self._upload_file_control(file, overwrite=True)
                        if is_loaded:
                            self.check_changed = True
                            logger.info(f"Файл {file} перезаписан")

    def control_cloud_folder(self):
        """удаление посторонних файлов из облака"""
        cloud_files = self.cloud_info
        try:
            for file_name in cloud_files:
                if file_name not in self.file_list:
                    result = self.storage.delete(file_name)
                    if result:
                        logger.info(f"Файл {file_name} удален")
            else:
                self.check_changed = True

        except ConnectionError:
            self.error_check = True
            logger.error(f"Ошибка соединения при выполнении операции удаления.")
        finally:
            self._finishing()
