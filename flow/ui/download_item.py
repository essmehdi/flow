import logging
from gi.repository import Gtk, GLib, GObject, Gio, Gdk
from gettext import gettext as _
from flow.ui.download_edit import DownloadEdit
from flow.core.download import Download
from flow.core.controller import DownloadsController
from flow.utils.misc import convert_size, get_eta


@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/download_item.ui")
class DownloadItem(Gtk.ListBoxRow):
    __gtype_name__ = "DownloadItem"

    ERROR_MESSAGES = {
        Download.STATUS_REQUEST_ERROR: _("Could not make request"),
        Download.STATUS_CONNECTION_ERROR: _("Could not connect to server"),
        Download.STATUS_TIMEOUT_ERROR: _("Connection timed out"),
        Download.STATUS_RESUME_ERROR: _("Could not resume download")
    }

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

    id                  = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    filename            = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    status              = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    size                = GObject.Property(type=GObject.GType.from_name('glong'), default=-1, flags=GObject.ParamFlags.READWRITE)
    resumable           = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
    progress            = GObject.Property(type=GObject.GType.from_name('gulong'), default=0, flags=GObject.ParamFlags.READWRITE)
    output_directory    = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    url                 = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    category            = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    date_initiated      = GObject.Property(type=GObject.GType.from_name('gulong'), default=0, flags=GObject.ParamFlags.READWRITE)
    date_started        = GObject.Property(type=GObject.GType.from_name('gulong'), default=0, flags=GObject.ParamFlags.READWRITE)
    date_finished       = GObject.Property(type=GObject.GType.from_name('gulong'), default=0, flags=GObject.ParamFlags.READWRITE)
    date_tag            = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    selected            = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
    selection_mode      = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Selection mode connect handler ID
        self.connect_id = None
        # Progress & speed data init
        self.last_checked = 0
        self.last_progress = 0
        self.speed = "0 B/s"
        self.eta = None
        # Context menu
        self.menu = Gtk.PopoverMenu.new_from_model(self.download_menu)
        #self.menu.set_has_arrow(False)
        self.menu.set_parent(self)
        # Setup actions
        self.setup_actions()
        # Setup drag & drop
        self.dnd = Gtk.DragSource.new()
        self.dnd.connect("prepare", self.prepare_dnd)
        self.add_controller(self.dnd)
        # Handle right click to open context menu
        self.right_click_handler = Gtk.GestureClick.new()
        self.right_click_handler.connect('pressed', self.handle_press)
        self.right_click_handler.set_button(3)
        self.add_controller(self.right_click_handler)
        # Handle double click to open file
        self.click_handler = Gtk.GestureClick.new()
        self.click_handler.connect_after('pressed', self.handle_press)
        self.add_controller(self.click_handler)
        # Handle properties changes
        self.connect('notify::filename', lambda *_: GLib.idle_add(self.on_filename_change))
        self.connect('notify::status', lambda *_: GLib.idle_add(self.on_status_change))
        self.connect('notify::progress', lambda *_: GLib.idle_add(self.on_progress_change))
        self.connect('notify::size', lambda *_: GLib.idle_add(self.on_size_change))
        self.connect('notify::resumable', lambda *_: GLib.idle_add(self.on_status_change))
        self.connect_after('notify::selection-mode', self.on_selection_mode_change)
        self.select_box.set_sensitive(False)
        # Sync selected status with checkbox
        self.bind_property("selected", self.select_box, "active", GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL)

    def on_selected_change(self, *_):
        if self.selected:
            DownloadsController.get_instance().select(self.id)
        else:
            DownloadsController.get_instance().unselect(self.id)

    def on_selection_mode_change(self, *_):
        if self.status == Download.STATUS_DONE:
            if self.selection_mode:
                self.left_stack.set_visible_child_name('select_mode')
                self.connect_id = self.connect('notify::selected', self.on_selected_change)
            else:
                if self.connect_id is not None:
                    self.disconnect(self.connect_id)
                    self.connect_id = None
                    self.selected = False
                self.left_stack.set_visible_child_name('action_mode')

    def on_filename_change(self, *__):
        if self.filename == "":
            self.filename_text.set_label(_("Loading..."))
        else:
            self.filename_text.set_label(self.filename)

    def on_status_change(self, *__):
        self.progress_bar.set_visible(self.size > 0 and self.status in ['downloading', 'paused'])
        if self.status == "init":
            self.state_stack.set_visible_child_name('pause')
            self.details_text.set_label(_("Please wait"))
            self.actions_stack.set_visible_child_name('empty')
            self.actions_activator('delete')
        elif self.status == "downloading":
            self.state_stack.set_visible_child_name('pause')
            self.actions_stack.set_visible_child_name('cancel')
            self.actions_activator('pause' if self.resumable else '', 'delete', 'edit')
        elif self.status == "paused":
            self.last_checked = 0
            self.state_stack.set_visible_child_name('resume' if self.resumable else 'restart')
            self.actions_stack.set_visible_child_name('cancel')
            self.actions_activator('restart', 'delete')
        elif "error" in self.status:
            self.state_stack.set_visible_child_name('restart')
            self.actions_stack.set_visible_child_name('cancel')
            self.details_text.set_label(DownloadItem.ERROR_MESSAGES.get(self.status, _("An error occurred")))
            self.actions_activator('restart', 'delete', 'resume-with-link')
        elif self.status == "moving":
            self.details_text.set_label(_("Moving file..."))
            self.state_stack.set_visible_child_name('pause')
            self.actions_stack.set_visible_child_name('cancel')
            self.actions_activator()
        elif self.status == "done":
            self.state_stack.set_visible_child_name('done')
            self.actions_stack.set_visible_child_name('open')
            self.actions_activator('open-folder', 'open-file', 'delete', 'delete-with-file')
            self.details_text.set_label(
                (convert_size(self.size) if self.size > 0 else '') + (" • " if self.category and self.size > 0 else '') + self.category
            )
            self.set_selectable(True)
            self.file_icon.set_from_gicon(Gio.content_type_get_icon(self.get_file_mimetype()))

    def actions_activator(self, *actions):
        for action in self.actions.list_actions():
            self.actions.lookup_action(action).set_enabled(action in actions or action == 'copy-url')

    def update_details_text(self):
        text = f"{convert_size(self.progress)}" + (f" / {convert_size(self.size)}" if self.size > 0 else "") + (f" • {self.eta}" if self.eta and self.status == Download.STATUS_STARTED else "")
        if self.speed:
            if self.speed == "0 B/s" and self.status == Download.STATUS_PAUSED:
                text += " • Paused"
            else:
                text += f" • { self.speed }"
        self.details_text.set_label(text)

    def on_progress_change(self, *_):
        # Speed & ETA
        current_time = GLib.get_monotonic_time()
        if self.last_checked == 0:
            if self.status == "downloading" or self.status == "paused":
                self.update_details_text()
            self.last_checked = current_time
            self.last_progress = self.progress
        time_delta = current_time - self.last_checked
        if time_delta >= 10**6:
            # Amount of data download in a second
            progress_delta = self.progress - self.last_progress
            # Update the progress
            if self.size > 0:
                self.progress_bar.set_fraction(float(self.progress / self.size))
                self.eta = get_eta(progress_delta, self.size - self.progress)
            self.speed = f"{convert_size(progress_delta)}/s" if progress_delta > 0 else "0 B/s"
            if self.status == "downloading" or self.status == "paused":
                self.update_details_text()
            self.last_progress = self.progress
            self.last_checked = current_time

    def on_size_change(self, *_):
        self.progress_bar.set_visible(self.size > 0 and self.status in ('downloading', 'paused'))

    def handle_press(self, controller, clicks, x, y):
        if controller.get_button() == 3:
            # TODO: Fix weird warnings
            pointing_position = Gdk.Rectangle(x, y, 1, 1)
            pointing_position.x = x
            pointing_position.y = y
            pointing_position.height = 1
            pointing_position.width = 1
            self.menu.set_pointing_to(pointing_position)
            self.menu.show()
        elif controller.get_button() == 1:
            if clicks == 2 and not self.selection_mode:
                if self.status == Download.STATUS_DONE:
                    self.actions.lookup_action('open-file').activate()
                else:
                    self.actions.lookup_action('edit').activate()
            elif clicks == 1 and self.selection_mode:
                self.selected = not self.selected

    def open_folder(self, *_):
        DownloadsController.get_instance().open(self.id, True)

    def prepare_dnd(self, *_):
        if self.status == 'done' and not self.selection_mode:
            file = DownloadsController.get_instance().get_file(self.id)
            if file:
                return Gdk.ContentProvider.new_union([
                    Gdk.ContentProvider.new_for_value(file),
                    Gdk.ContentProvider.new_for_value(file.get_path()),
                    Gdk.ContentProvider.new_for_value(file.get_uri()),
                    Gdk.ContentProvider.new_for_bytes("text/uri-list", GLib.Bytes.new(file.get_uri().encode()))
                ])

    def setup_actions(self):
        self.actions = Gio.SimpleActionGroup.new()
        actions_list = [
            {
                "name": 'copy-url',
                "activate": lambda _, __, row: DownloadsController.get_instance().copy_url(row.id)
            },
            {
                "name": 'open-file',
                "activate": lambda _, __, row: DownloadsController.get_instance().open(row.id, False)
            },
            {
                "name": 'open-folder',
                "activate": lambda _, __, row: DownloadsController.get_instance().open(row.id, True)
            },
            {
                "name": 'delete',
                "activate": lambda _, __, row: DownloadsController.get_instance().delete(row.id)
            },
            {
                "name": 'delete-with-file',
                "activate": lambda _, __, row: DownloadsController.get_instance().delete(row.id, True)
            },
            {
                "name": 'pause',
                "activate": lambda _, __, row: DownloadsController.get_instance().pause(row.id)
            },
            {
                "name": 'restart',
                "activate": lambda _, __, row: DownloadsController.get_instance().restart(row.id)
            },
            {
                "name": 'edit',
                "activate": self.show_edit_window
            },
            {
                "name": 'resume-with-link',
                "activate": lambda _, __, row: DownloadsController.get_instance().resume_with_link(row.id)
            }
        ]
        for action in actions_list:
            _action = Gio.SimpleAction.new(action.get('name'), None)
            _action.connect('activate', action.get('activate'), self)
            self.actions.add_action(_action)
        self.insert_action_group('download', self.actions)

    def get_file_mimetype(self):
        return Gio.content_type_guess(self.filename)[0]

    def show_edit_window(self, *_):
        DownloadsController.get_instance().enable_edit_mode(self.id)
