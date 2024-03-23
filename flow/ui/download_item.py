import logging
from gi.repository import Gtk, GLib, GObject, Gio, Gdk
from gettext import gettext as _
from flow.ui.download_edit import DownloadEdit
from flow.core.download import Download
from flow.core.controller import DownloadsController
from flow.utils.misc import convert_size, get_eta
from flow.core import daemon
import os
import pathlib

from flow.utils.toaster import Toaster


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

        self._setup_actions()

        self._handle_status_change()

    def _handle_status_change(self):
        self.action_group.lookup("restart").set_enabled(self.status == 3)
        self.actions_stack.set_visible_child_name("open" if self.status == 5 else ("empty" if self.status == 1 else "cancel"))
        self.state_stack.set_visible_child_name("pause" if self.status == 2 else "resume")
        match self.status:
            case 1:
                self.details_text.set_label("Starting")
            case 5:
                self._populate_completed()
            case 2:
                self._connect_progress()
            case 3:
                self._disconnect_progress()
                self._handle_pause_ui()
            case _:
                pass

    def _handle_pause_ui(self):
        self.state_stack.set_visible_child_name("resume" if self.resumable else "restart")
        new_details_text = _("Paused") + " • " + self._get_progress_text()
        self.details_text.set_label(new_details_text)
        

    def _init_watchers(self):
        self.connect("notify::status", lambda *_: self._handle_status_change())
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

        download_category = daemon.get_category_name(self._get_file_path())
        category_suffix = f" • {download_category}" if download_category else ""

        self.details_text.set_label(convert_size(self.size) + category_suffix)

        self.file_icon.set_from_gicon(Gio.content_type_get_icon(Gio.content_type_guess(self._get_file_path(), None)[0]))

    def _get_file_path(self):
        return self.output_file if self.output_file else self.detected_output_file

    def _connect_progress(self):
        if self.progress_subscription is None:
            self.progress_subscription = daemon.subscribe_to_download_progress(
                lambda _, __, ___, ____, data: (
                    self._on_download_progress(data)
                )
            )

    def _disconnect_progress(self):
        if self.progress_subscription:
            self.progress_subscription.disconnect()
            self.progress_subscription = None

    def _on_download_progress(self, data):
        download_id, progress, _ = data
        if download_id != self.id:
            return
        self.progress = progress
        self.progress_bar.set_fraction(self._get_progress_fraction())
        self.details_text.set_label(self._get_progress_text())

    def _get_progress_text(self):
        size_text = "" if self.size == 0 else f" / {convert_size(self.size)}"
        return f"{convert_size(self.progress)}{size_text} - {self._get_progress_fraction() * 100:.2f}%"

    def _get_progress_fraction(self):
        return 0 if self.size == 0 else self.progress / self.size

    def _pause_download(self):
        daemon.pause_download(self.id)

    def _restart_download(self):
        daemon.resume_download(self.id)

    def _open_folder(self):
        if self.status == 5:
            file_path = self._get_file_path()
            file_path = pathlib.Path(file_path)
            file_path_parent = file_path.parent
            if os.path.exists(file_path_parent):
                Gio.AppInfo.launch_default_for_uri(f"file://{os.path.dirname(file_path)}")
            else:
                Toaster.show(_("Directory deleted or moved"))

    def _setup_actions(self):
        self.action_group = Gio.SimpleActionGroup.new()

        # Pause action
        pause_action = Gio.SimpleAction.new("pause", None)
        pause_action.connect("activate", lambda *_: self._pause_download())
        self.action_group.insert(pause_action)

        # Resume action
        resume_action = Gio.SimpleAction.new("restart", None)
        resume_action.connect("activate", lambda *_: self._restart_download())
        self.action_group.insert(resume_action)

        # Open folder action
        open_folder_action = Gio.SimpleAction.new("open-folder", None)
        open_folder_action.connect("activate", lambda *_: self._open_folder())
        self.action_group.insert(open_folder_action)

        self.insert_action_group("download", self.action_group)

