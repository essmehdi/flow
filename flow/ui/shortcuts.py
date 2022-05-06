from operator import imod
from gi.repository import Gtk

@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/shortcuts.ui")
class Shortcuts(Gtk.ShortcutsWindow):
    __gtype_name__ = "Shortcuts"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)