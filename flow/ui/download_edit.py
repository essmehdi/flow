import os
from gi.repository import Gtk, Adw, Gio
from gettext import gettext as _

from flow.core.controller import DownloadsController

@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/download_edit.ui")
class DownloadEdit(Adw.Window):
    __gtype_name__ = "DownloadPrompt"

    url_label = Gtk.Template.Child()
    filename_entry = Gtk.Template.Child()
    directory_button = Gtk.Template.Child()
    save_button_content = Gtk.Template.Child()
    cancel_button_content = Gtk.Template.Child()

    def __init__(self, initial, id, url, filename, directory, **kwargs):
        super().__init__(**kwargs)
        self.save_action = None
        # Check if it's download confirmation prompt
        self.initial = initial
        if self.initial:
            self.save_button_content.set_label(_("Download"))
            self.cancel_button_content.set_label(_("Cancel download"))
            self.save_button_content.set_icon_name("go-down-symbolic")
        # Register download ID
        self.id = id
        # Save original data
        self.og_filename = filename
        self.og_directory = directory
        self.filename_flag = False
        self.directory_flag = False
        # Set fields with original data
        self.directory_button.value = self.og_directory
        self.directory_button.connect('notify::value', self.on_directory_change)
        self.filename_entry.set_text(self.og_filename)
        self.url_label.set_label(url)
        self.url_label.set_tooltip_text(url)
        # Setup window actions
        self.setup_actions()
        self.refresh_save_action()

    @Gtk.Template.Callback()
    def filename_changed(self, entry, *_):
        if entry.get_text() != self.og_filename:
            self.filename_flag = True
        else:
            self.filename_flag = False
        self.refresh_save_action()

    def refresh_save_action(self):
        if self.save_action is not None:
            self.save_action.set_enabled(self.filename_flag or self.directory_flag or self.initial)

    def setup_actions(self):
        self.actions = Gio.SimpleActionGroup()
        # Save action
        self.save_action = Gio.SimpleAction(name='save')
        self.save_action.connect('activate', self.save)
        self.actions.add_action(self.save_action)
        # Cancel action
        self.cancel_action = Gio.SimpleAction(name='cancel')
        self.cancel_action.connect('activate', self.cancel_download if self.initial else self.cancel)
        self.actions.add_action(self.cancel_action)
        # Insert actions into window
        self.insert_action_group('dedit', self.actions)
    
    def on_directory_change(self, *_):
        selected_path = self.directory_button.value
        if os.path.normpath(selected_path) != os.path.normpath(self.og_directory):
            self.new_directory = selected_path
            self.directory_flag = True
        else:
            self.directory_flag = False
        self.refresh_save_action()
    
    def save(self, *_):
        DownloadsController.get_instance().edit(
            self.id,
            self.filename_entry.get_text() if self.filename_flag else None,
            self.new_directory if self.directory_flag else None
        )
        self.destroy()

    def cancel_download(self, *_):
        DownloadsController.get_instance().delete(self.id)
        self.destroy()

    def cancel(self, *_):
        DownloadsController.get_instance().disable_edit_mode(self.id)
        self.destroy()
