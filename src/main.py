import json
import gi
import sys
import logging

from .toaster import Toaster

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Notify", "0.7")

from gi.repository import Gtk, Adw, Gio, GObject, Notify
from .preferences.window import PreferencesWindow
from .controller import DownloadsController
from .components.url_prompt import URLPrompt
from .about import AboutDialog
from .settings import Settings
from gettext import gettext as _
import argparse


@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/main.ui")
class FlowWindow(Adw.ApplicationWindow):
    
    __gtype_name__ = "FlowWindow"
    
    clamp = Gtk.Template.Child()
    content = Gtk.Template.Child()
    finished_downloads_list = Gtk.Template.Child()
    running_downloads_list = Gtk.Template.Child()
    scrolled_window = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    empty_stack = Gtk.Template.Child()
    selection_mode_toggle = Gtk.Template.Child()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.about = None
        # Discard selection mode action
        self.discard_action = Gio.SimpleAction.new('discard-selection-mode', None)
        self.discard_action.connect('activate', self.discard_selection_mode)
        self.add_action(self.discard_action)
        # New download action
        self.new_action = Gio.SimpleAction.new('new', None)
        self.new_action.connect('activate', self.show_url_prompt)
        self.add_action(self.new_action)
        # List actions
        self.delete_selected = Gio.SimpleAction.new('delete-selected', None)
        self.delete_selected.connect('activate', DownloadsController.get_instance().delete_selected_rows, self)
        self.delete_selected.set_enabled(False)
        self.add_action(self.delete_selected)
        # Preferences action
        preferences_action = Gio.SimpleAction.new('preferences', None)
        preferences_action.connect('activate', self.preferences_action_handler)
        self.add_action(preferences_action)
        # Shortcuts
        shortcuts_action = Gio.SimpleAction.new('shortcuts', None)
        shortcuts_action.connect('activate', self.shortcuts_action_handler)
        self.add_action(shortcuts_action)
        # About action
        about_action = Gio.SimpleAction.new('about', None)
        about_action.connect('activate', self.about_action_handler)
        self.add_action(about_action)
        # Init the controller
        DownloadsController.get_instance().load_ui(self)
        # Register toast overlay
        Toaster.get_instance().register_overlay(self.toast_overlay)
        # Setup shortcuts
        self.setup_shortcuts()
        self.prompt = None
        self.preferences = None
        # Save window state
        settings = Gio.Settings("com.github.essmehdi.flow")
        settings.bind('window-width', self, 'default-width', Gio.SettingsBindFlags.DEFAULT)
        settings.bind('window-height', self, 'default-height', Gio.SettingsBindFlags.DEFAULT)
        settings.bind('window-maximized', self, 'maximized', Gio.SettingsBindFlags.DEFAULT)
        # Selection mode toggle
        self.selection_mode_toggle.bind_property('active', DownloadsController.get_instance(), 'selection-mode', GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.BIDIRECTIONAL)

    def discard_selection_mode(self, *_):
        self.selection_mode_toggle.set_active(False)

    def setup_shortcuts(self):
        self.get_application().set_accels_for_action("win.delete-selected", ["Delete", None])
        self.get_application().set_accels_for_action("win.new", ["<Ctrl>n", None])
        self.get_application().set_accels_for_action("win.discard-selection-mode", ["Escape", None])
        self.get_application().set_accels_for_action("prompt.confirm", ["Return", None])
        self.get_application().set_accels_for_action("prompt.cancel", ["Escape", None])
        self.get_application().set_accels_for_action("dedit.save", ["Return", None])
        self.get_application().set_accels_for_action("dedit.cancel", ["Escape", None])
        self.get_application().set_accels_for_action("cedit.save", ["Return", None])
        self.get_application().set_accels_for_action("cedit.cancel", ["Escape", None])
        
    def show_url_prompt(self, *_):
        # New download prompt
        self.prompt = URLPrompt(transient_for=self, application=self.get_application())
        self.prompt.show()

    def preferences_action_handler(self, *_):
        self.preferences = PreferencesWindow(transient_for=self, application=self.get_application())
        self.preferences.show()

    def about_action_handler(self, *_):
        app = self.get_application()
        self.about = AboutDialog(app.version, application=app, transient_for=self)
        self.about.show()

    def shortcuts_action_handler(self, *_):
        # TODO: Create shortcuts window
        pass


class MainApplication(Adw.Application):

    version = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)

    def __init__(self, version, **kwargs):
        super().__init__(application_id="com.github.essmehdi.flow", **kwargs)
        self.window = None
        self.version = version

    def do_activate(self):
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK if Settings.get().force_dark else Adw.ColorScheme.PREFER_LIGHT)
        self.window = self.props.active_window
        if not self.window:
            self.window = FlowWindow(application=self)
        self.window.show()

    def do_command_line(self, acl):
        parser = argparse.ArgumentParser(
            description="A download manager for GNOME"
        )
        parser.add_argument(
            "-H", "--headers",
            metavar="headers",
            help=_("Download request headers"),
            required=False
        )
        parser.add_argument(
            "-u", "--url",
            metavar="url",
            help=_("Download link"),
            required=False
        )
        parser.add_argument(
            "-l", "--logs-level",
            metavar="level",
            dest="level",
            help=_("Logs verbose level"),
            required=False
        )
        args = parser.parse_args(acl.get_arguments()[1:])

        # Setup logs
        level = None
        format = "[%(levelname)s] %(message)s"
        if args.level:
            level = getattr(logging, args.level)
        if not isinstance(level, int):
            print("Unspecified or invalid logs level. Fallback to INFO.")
            logging.basicConfig(level=logging.INFO, format=format, datefmt="%Y-%m-%d %H:%M:%S ")
        else:
            logging.basicConfig(level=level, format=format)
            
        if args.url:
            logging.debug(args.headers)
            DownloadsController.get_instance().add_from_url(args.url, json.loads(args.headers) if args.headers is not None else {})
        elif self.window and not self.window.get_visible():
            logging.debug("Window hidden")
            self.window.show()
        self.do_activate()
        return 0
        
    
def main(version):
    app = MainApplication(flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, version=version)
    app.run(sys.argv)
