import os
import shutil
import time
from datetime import datetime

abs_path = os.path.abspath('')
path_source = os.path.join(abs_path, "source")
path_dist = os.path.join(os.path.abspath("E:/"), "destination")

is_dist_folder_changed = False
all_files = []
stop = False
is_changed = False
print("Слежение включено")

while True:
    try:
        os.chdir(path_source)
        for file in os.listdir():
            if os.path.isfile(file) and file == "0":
                os.remove("0")
                print("Слежение отключено")
                stop = True
                break
            elif os.path.isfile(file):
                all_files.append(file)
                data_change_source = datetime.fromtimestamp(os.path.getmtime(file))
                os.chdir(path_dist)
                if not os.path.isfile(file):
                    name = shutil.copy(src=os.path.join(path_source, file), dst=file)
                    is_changed = True
                    print(f"Файл {name} загружен")
                else:
                    data_change_dist = datetime.fromtimestamp(os.path.getmtime(file))
                    is_changed_file = data_change_source > data_change_dist
                    if is_changed_file:
                        name = shutil.copy(src=os.path.join(path_source, file), dst=file)
                        is_changed = True
                        print(f"Файл {name} перезаписан")
                os.chdir(path_source)

        if stop:
            break

        os.chdir(path_dist)
        for file in os.listdir():
            if os.path.isfile(file) and file not in all_files:
                os.remove(file)
                is_changed = True
                print(f'Файл {file} удален')

        if is_changed:
            print('Директории синхронизированы. Текущее содержимое:', ', '.join(all_files))
            is_changed = False

        all_files.clear()
        os.chdir(path_source)
        time.sleep(5)

    except FileNotFoundError as ex:
        print(f'{ex =}')
        time.sleep(5)
