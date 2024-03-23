from pydbus import SessionBus
from flow.core.download import Download
from gi.repository import GLib
import logging
import tomllib
import os

CONFIG_PATH = os.path.join(GLib.get_home_dir(), ".config/flow/config.toml")
dbus = SessionBus()

def get_listener():
    return dbus.get("com.github.essmehdi.Flowd", "/com/github/essmehdi/Flowd/Listener")


def get_sorted_downloads():
    return map(_download_mapper, get_listener().GetSortedDownloads())


def get_all_downloads():
    return map(_download_mapper, get_listener().GetAllDownloads())


def get_downloads_by_completed_status(completed):
    return map(
        _download_mapper, get_listener().GetDownloadsByCompletedStatus(completed)
    )

def pause_download(download_id):
    logging.debug("Pausing download" + str(download_id))
    return get_listener().PauseDownload(download_id)

def resume_download(download_id):
    return get_listener().ResumeDownload(download_id)

def new_download_confirmed(url):
    return get_listener().NewDownloadConfirmed(url)

def subscribe_to_download_update(callback):
    logging.debug("Subscribing to download update")
    # return get_listener().NotifyDownloadUpdate().connect(callback)
    return dbus.subscribe(
        "com.github.essmehdi.Flowd",
        "com.github.essmehdi.Flowd",
        "NotifyDownloadUpdate",
        "/com/github/essmehdi/Flowd/Listener",
        signal_fired=callback,
    )    

def subscribe_to_download_progress(callback):
    logging.debug("Subscribing to download progress")
    # return get_listener().NotifyDownloadProgress.connect(callback)
    return dbus.subscribe(
        "com.github.essmehdi.Flowd",
        "com.github.essmehdi.Flowd",
        "NotifyDownloadProgress",
        "/com/github/essmehdi/Flowd/Listener",
        signal_fired=callback,
    )

def _download_mapper(download):
    return Download(
        id=download.get("id"),
        status=download.get("status"),
        url=download.get("url"),
        temp_file=download.get("temp_file"),
        output_file=download.get("output_file", None),
        detected_output_file=download.get("detected_output_file", None),
        date_added=download.get("date_added"),
        date_completed=download.get("date_completed", -1),
        size=download.get("size", 0),
        resumable=download.get("resumable"),
    )

def get_config():
    with open(CONFIG_PATH, "r") as config:
        return tomllib.loads(config.read())
    
def get_category_name(file_name):
  if not file_name:
      return None
  config = get_config()
  for category in config.get("categories"):
    for extension in config.get("categories").get(category).get("extensions"):
      if file_name.endswith(extension):
        return category
