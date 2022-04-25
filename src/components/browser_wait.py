from gi.repository import Gtk, Adw, Gio
from gettext import gettext as _

@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/browser_wait.ui")
class BrowserWait(Adw.Window):
    __gtype_name__ = 'BrowserWait'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
