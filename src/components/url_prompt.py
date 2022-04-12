import validators
from gi.repository import Gtk, Adw, Gio

from ..controller import DownloadsController

@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/url_prompt.ui")
class URLPrompt(Adw.Window):

    __gtype_name__ = "URLPrompt"

    url_entry = Gtk.Template.Child()
    confirm_button = Gtk.Template.Child()
    error_text = Gtk.Template.Child()
    url_value = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_actions()
        self.url_entry.set_text(self.url_value)

    def setup_actions(self):
        self.actions = Gio.SimpleActionGroup.new()
        # Confirm action
        self.confirm_action = Gio.SimpleAction.new('confirm', None)
        self.confirm_action.connect('activate', self.confirm)
        self.confirm_action.set_enabled(False)
        self.actions.add_action(self.confirm_action)
        # Cancel action
        self.cancel_action = Gio.SimpleAction.new('cancel', None)
        self.cancel_action.connect('activate', self.cancel)
        self.actions.add_action(self.cancel_action)
        self.insert_action_group('prompt', self.actions)
        
    @Gtk.Template.Callback()
    def url_text_changed(self, *_):
        if self.error_text.is_visible:
            self.error_text.set_visible(False)
        self.url_value = self.url_entry.get_text()
        if not validators.url(self.url_value):
            self.confirm_action.set_enabled(False)
        else:
            self.confirm_action.set_enabled(True)

    def cancel(self, *_):
        self.destroy()

    def confirm(self, *_):
        DownloadsController.get_instance().add_from_url(self.url_value)
        self.destroy()

