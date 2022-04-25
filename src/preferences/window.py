from .category_editor import CategoryEditor

from ..settings import Settings
from .category_row import CategoryRow
from ..components.file_chooser_button import FileChooserButton

from gi.repository import Gtk, Adw, Gio

@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/preferences/window.ui")
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesWindow"

    categories_group = Gtk.Template.Child()
    connection_timeout_spin = Gtk.Template.Child()
    connection_proxy = Gtk.Template.Child()
    connection_proxy_address_entry = Gtk.Template.Child()
    connection_proxy_port_spin = Gtk.Template.Child()
    user_agent_entry = Gtk.Template.Child()
    force_dark_toggle = Gtk.Template.Child()
    fallback_directory_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for binding in self.get_bindings():
            Settings.get().bind(binding.get('key'), binding.get('widget'), binding.get('property'), Gio.SettingsBindFlags.DEFAULT)
        self.force_dark_toggle.connect('state-set', self.dark_mode_handler)
        self.populate_categories()

    def dark_mode_handler(self, _, state):
        style_manager = Adw.StyleManager.get_default()
        if state:
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.PREFER_LIGHT)
    
    def populate_categories(self):
        self.categories = Settings.get().categories
        for category, settings in self.categories.items():
            self.categories_group.add(CategoryRow(category, settings))
        self.append_add_button()

    def append_add_button(self):
        builder = Gtk.Builder()
        builder.add_from_resource("/com/github/essmehdi/flow/layout/preferences/add_row.ui")
        self.add_row = builder.get_object("add_row")
        self.add_button = builder.get_object("add_button")
        self.add_button.connect("clicked", self.add_handler)
        self.categories_group.add(self.add_row)

    def update_ui(self, category, settings):
        self.categories_group.remove(self.add_row)
        self.categories_group.add(CategoryRow(category, settings))
        self.categories_group.add(self.add_row)

    def add_handler(self, *_):
        self.editor = CategoryEditor(None, None, self.update_ui, transient_for=self, application=self.get_application())
        self.editor.show()

    def get_bindings(self):
        return [
            { 
                "widget": self.connection_timeout_spin,
                "key": "connection-timeout",
                "property": "value"
            },
            { 
                "widget": self.connection_proxy,
                "key": "connection-proxy",
                "property": "enable-expansion"
            },
            { 
                "widget": self.connection_proxy_address_entry,
                "key": "connection-proxy-address",
                "property": "text"
            },
            { 
                "widget": self.connection_proxy_port_spin,
                "key": "connection-proxy-port",
                "property": "value"
            },
            {
                "widget": self.user_agent_entry,
                "key": "user-agent",
                "property": "text"
            },
            {
                "widget": self.force_dark_toggle,
                "key": "force-dark",
                "property": "active"
            },
            {
                "widget": self.fallback_directory_button,
                "key": "fallback-directory",
                "property": "value"
            }
        ]