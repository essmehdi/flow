import logging
import os
import json
from gi.repository import GLib

class DownloadNotFound(Exception):
    pass

class StatusManager():

    @staticmethod
    def add_to_finished(id: str, download: dict):
        with StatusManager.get_status_file(True) as file:
            status = json.loads(file.read())
            status[id] = download
            file.seek(0)
            file.write(json.dumps(status))
            file.truncate()

    @staticmethod
    def download_finished(id: str):
        finished_id, download = StatusManager.remove_download(id, False, False)
        StatusManager.add_to_finished(finished_id, download)

    @staticmethod
    def get_status_file(finished=True):
        home_dir = GLib.get_home_dir()
        atay_status_file = os.path.join(home_dir, ".atay/finished.json" if finished else ".atay/running.json")
        if not os.path.exists(os.path.dirname(atay_status_file)):
            os.makedirs(os.path.dirname(atay_status_file), exist_ok=True)
        if not os.path.exists(atay_status_file) or os.path.getsize(atay_status_file) == 0:
            with open(atay_status_file, "w") as file:
                file.write("{}")
        return open(atay_status_file, 'r+')

    @staticmethod
    def get_downloads(finished):
        with StatusManager.get_status_file(finished) as file:
            return json.loads(file.read())    

    @staticmethod
    def update_property(id: str, property: str, value):
        with StatusManager.get_status_file(False) as file:
            item_status = json.loads(file.read())
            item_status[id][property] = value
            file.seek(0)
            file.write(json.dumps(item_status))
            file.truncate()

    @staticmethod
    def register_download(id, **kwargs):
        item = { **kwargs, "date_initiated": GLib.DateTime.new_now_local().to_unix() }
        with StatusManager.get_status_file(False) as file:
            status = json.loads(file.read())
            status[id] = item
            file.seek(0)
            file.write(json.dumps(status))
            file.truncate()
            return item

    @staticmethod
    def get_status(id: str, finished: bool):
        with StatusManager.get_status_file(finished) as file:
            status = json.loads(file.read())
            if id in status:
                return status[id]
            else:
                raise DownloadNotFound(f"Cannot find a download with ID: {id}")

    def remove_download(id: str, finished: bool, delete_file:bool = False):
        to_delete = None
        with StatusManager.get_status_file(finished) as file:
            status = json.loads(file.read())
            if id in status:
                download = status.get(id)
                if delete_file and download.get('status') == 'done':
                    path = os.path.join(download.get('output_directory'), download.get('filename'))
                    # A naive precaution to be sure it's the downloaded file
                    if os.path.exists(path) and os.path.getsize(path) == download.get('size'):
                        logging.info("File found. Deleting...")
                        os.remove(path)
                    else:
                        logging.info("File not found")
                tmp = download.get('tmp')
                if tmp and os.path.exists(tmp):
                    os.remove(tmp)
                to_delete = status[id]
                del status[id]
            else:
                raise DownloadNotFound(f"Cannot find a download with ID: {id}")
            file.seek(0)
            file.write(json.dumps(status))
            file.truncate()
            return (id, to_delete)