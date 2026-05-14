import argparse
import sys
import os
import time

from loguru import logger

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from control.cloud_control import UploaderToCloud
from settings import clouds


parser = argparse.ArgumentParser(description="Сервис синхронизации файлов")
# передача нужного облако из консоли
parser.add_argument("cloud")
args = parser.parse_args()
current_cloud = args.cloud

cloud = clouds[current_cloud]
token = cloud.get("token")

path_source = cloud.get("path_source")
os.chdir(path_source)

path_to_log = cloud.get("path_to_log")
time_reload = cloud.get("time_reload")
base_url = cloud.get("base_url")
path_dist = cloud.get("path_dist")
cloud_scan_time_delta = cloud.get("cloud_scan_time_delta")
timeout = cloud.get("timeout")

storage = cloud.get("storage")(token, base_url, path_dist)
uploader = UploaderToCloud(storage, cloud_scan_time_delta, timeout, path_source)


logger.remove()
format_out = "{module} <green>{time:YYYY-MM-DD HH:mm:ss,SSS}</green> {level} <level>{message}</level>"
logger.add(sys.stdout, format=format_out, level="INFO", colorize=True)
logger.add(path_to_log, format=format_out, level="INFO")


def main():
    """
    Синхронизация папки на локальном диске с облачным хранилищем
    """

    while True:
        try:
            uploader.check_local_folder()
            if not uploader.pause:
                uploader.control_cloud_folder()
        except AttributeError as ex:
            uploader.error_check = True
            logger.info(f" {ex} Следующая попытка синхронизации через {time_reload} c.")
            time.sleep(time_reload)
        except FileNotFoundError as ex:
            uploader.error_check = True
            logger.error(f"{ex}. Неверно указан путь к локальной папке")
            time.sleep(time_reload)
        except KeyError:
            logger.error(
                f"Ошибка при получении данных с {storage}."
                " Возможно, в облаке отсутствует указанная папка, или не найден токен"
            )
            time.sleep(time_reload)
        except ConnectionError as ex:
            uploader.error_check = True
            logger.error(
                f"{ex} Ошибка при получении данных с {storage}. Не удается установить связь с облаком"
            )
            time.sleep(time_reload)


if __name__ == "__main__":
    main()
