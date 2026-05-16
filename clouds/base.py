# Интерфейс
from abc import ABC, abstractmethod
from typing import BinaryIO


class CloudStorage(ABC):
    """Контроль состояния облака"""

    @abstractmethod
    def get_files(self, limit: int):
        """
        Получение списка файлов в облаке
        :param limit: Количество файлов из облака, которое нужно получить
        """
        pass

    @abstractmethod
    def upload(self, file_name: str, file_obj: BinaryIO, overwrite: bool):
        """
        Загрузка/изменение файла в облако из локальной папки
        :param file_name: Имя файла
        :param overwrite: Разрешение перезаписи
        :return: При успешном удалении возвращает True
        """
        pass

    @abstractmethod
    def delete(self, file_name: str):
        """
        Удаление файла из облака.
        :param file_name: имя файла
        :return: При успешном удалении возвращает True
        """
        pass
