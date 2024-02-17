from pydbus import SessionBus
from flow.core.download import Download
import logging

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
        size=download.get("size"),
        resumable=download.get("resumable"),
    )
