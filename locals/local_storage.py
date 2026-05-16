import os


class LocalsFiles:
    """Контроль состояния локальной папки"""

    def __init__(self, path_source):
        self.path_source = path_source

    def _get_path_ro_file(self, file):
        return os.path.join(self.path_source, file)

    def get_all_local_files(self):
        all_files = [
            file
            for file in os.listdir(self.path_source)
            if os.path.isfile(self._get_path_ro_file(file))
        ]
        return all_files

    def get_last_modified_time(self, file):
        path = self._get_path_ro_file(file)
        return os.path.getmtime(path)

    def delete(self, file):
        path = self._get_path_ro_file(file)
        os.remove(path)
