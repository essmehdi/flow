from gi.repository import Gtk, Adw, Gio
from gettext import gettext as _

@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/browser_wait.ui")
class BrowserWait(Adw.Window):
    __gtype_name__ = 'BrowserWait'

    stack = Gtk.Template.Child()
    url = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.confirm_id = None
        self.separate_id = None

        actions = Gio.SimpleActionGroup()

        self.cancel_action = Gio.SimpleAction(name='cancel')
        self.cancel_action.connect('activate', self.cancel)
        actions.add_action(self.cancel_action)

        self.confirm_action = Gio.SimpleAction(name='use-link')
        actions.add_action(self.confirm_action)

        self.separate_action = Gio.SimpleAction(name='separate')
        actions.add_action(self.separate_action)

        self.insert_action_group('bwait', actions)

    def show_confirm_dialog(self, url, confirm_callback, separate_callback):
        if self.confirm_id is not None:
            self.disconnect(self.confirm_id)
        self.confirm_action.connect('activate', confirm_callback)

        if self.separate_id is not None:
            self.disconnect(self.separate_id)
        self.separate_action.connect('activate', separate_callback)

        self.stack.set_visible_child_name('confirm')
        self.url.set_label(url)

    def cancel(self, *__):
        from ..controller import DownloadsController
        DownloadsController.get_instance().cancel_wait_for_link()