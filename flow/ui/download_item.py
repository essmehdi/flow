import logging
from gi.repository import Gtk, GLib, GObject, Gio, Gdk
from gettext import gettext as _
from flow.ui.download_edit import DownloadEdit
from flow.core.download import Download
from flow.core.controller import DownloadsController
from flow.utils.misc import convert_size, get_eta
from flow.core import daemon
import os


@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/download_item.ui")
class DownloadItem(Gtk.ListBoxRow):
    __gtype_name__ = "DownloadItem"

    # ERROR_MESSAGES = {
    #     Download.STATUS_REQUEST_ERROR: _("Could not make request"),
    #     Download.STATUS_CONNECTION_ERROR: _("Could not connect to server"),
    #     Download.STATUS_TIMEOUT_ERROR: _("Connection timed out"),
    #     Download.STATUS_RESUME_ERROR: _("Could not resume download")
    # }

    DATE_TAG_TODAY = _("Today")
    DATE_TAG_YESTERDAY = _("Yesterday")
    DATE_TAG_LAST_WEEK = _("Last week")
    DATE_TAG_THIS_MONTH = _("This month")
    DATE_TAG_LAST_MONTH = _("Last month")
    DATE_TAG_THIS_YEAR = _("This year")
    DATE_TAG_LAST_YEAR = _("Last year")
    DATE_TAG_MORE_YEAR = _("More than a year")

    filename_text = Gtk.Template.Child()
    details_text = Gtk.Template.Child()
    open_folder_button = Gtk.Template.Child()
    cancel_button = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()
    actions_stack = Gtk.Template.Child()
    state_stack = Gtk.Template.Child()
    download_menu = Gtk.Template.Child()
    left_stack = Gtk.Template.Child()
    select_box = Gtk.Template.Child()
    file_icon = Gtk.Template.Child()

    # Download properties
    id                      = GObject.Property(type=GObject.GType.from_name('gulong'), default=0, flags=GObject.ParamFlags.READWRITE)
    status                  = GObject.Property(type=int, default=0, flags=GObject.ParamFlags.READWRITE)
    url                     = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    temp_file               = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    output_file             = GObject.Property(type=str, default=None, flags=GObject.ParamFlags.READWRITE)
    detected_output_file    = GObject.Property(type=str, default=None, flags=GObject.ParamFlags.READWRITE)
    date_added              = GObject.Property(type=int, default=0, flags=GObject.ParamFlags.READWRITE)
    date_completed          = GObject.Property(type=int, default=None, flags=GObject.ParamFlags.READWRITE)
    # category                = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    size                    = GObject.Property(type=GObject.GType.from_name('gulong'), default=None, flags=GObject.ParamFlags.READWRITE)
    resumable               = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)

    progress                = GObject.Property(type=int, default=0, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.progress_subscription = None
        self._init_watchers()

        match self.status:
            case 5:
                self._populate_completed()
            case 2:
                self._connect_progress()
            case _:
                pass

    def _init_watchers(self):
        self.connect("notify::output_file", lambda *_: self._update_filename_text())
        self.connect("notify::detected_output_file", lambda *_: self._update_filename_text())
        self._update_filename_text()

    def _update_filename_text(self):
        """Update the filename text label with the output file name."""
        filename = None
        if self.output_file:
            filename = os.path.basename(self.output_file)
        elif self.detected_output_file:
            filename = os.path.basename(self.detected_output_file)
        else:
            filename = os.path.basename(self.url)
        self.filename_text.set_label(filename)

    def _populate_completed(self):
        self.state_stack.set_visible_child_name("done")
        self.actions_stack.set_visible_child_name("open")
        self.progress_bar.set_visible(False)
        self.details_text.set_label(convert_size(self.size))

        self.file_icon.set_from_gicon(Gio.content_type_get_icon(Gio.content_type_guess(self._get_file_path(), None)[0]))

    def _get_file_path(self):
        return self.output_file if self.output_file else self.detected_output_file

    def _connect_progress(self):
        self.progress_subscription = daemon.subscribe_to_download_progress(
            lambda _, __, ___, ____, data: (
                self._on_download_progress(data)
            )
        )

    def _on_download_progress(self, data):
        download_id, progress, size = data
        if download_id != self.id:
            return
        logging.debug(f"Download progress: {data}")
        progress_fraction = progress / size
        progress_percentage = progress_fraction * 100
        self.progress = progress
        self.progress_bar.set_fraction(progress_fraction)
        self.details_text.set_label(f"{convert_size(progress)} / {convert_size(size)} - {progress_percentage:.2f}%")
