# Интерфейс
from abc import ABC, abstractmethod


class CloudStorage(ABC):
    @abstractmethod
    def get_files(self, limit: int):
        """
        Получение списка файлов в облаке
        :param limit: Количество файлов из облака, которое нужно получить
        """
        pass

    @abstractmethod
    def upload(self, file_name: str, overwrite: bool):
        """
        Загрузка/изменение файла в облако из локальной папки
        :param file_name: Имя файла
        :param overwrite: Разрешение перезаписи
        :return: При успешном удалении возвращает True
        """
        pass

    @abstractmethod
    def delete(self, cloud_files, list_local_folder: list):
        """
        Удаление файлов из облака, если они отсутствует в папке слежения.
        :param cloud_files: словарь файлов в облаке {"name": "время создания/изменения"}
        :param list_local_folder: список файлов в папке слежения
        :return: При успешном удалении возвращает True
        """
        pass
