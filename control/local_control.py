import os


class LocalsFiles:
    all_files = []

    @classmethod
    def get_all_local_files(cls):
        cls.all_files = [file for file in os.listdir() if os.path.isfile(file)]
