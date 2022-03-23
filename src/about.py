from gi.repository import Gtk

@Gtk.Template(resource_path="/com/github/essmehdi/atay/layout/about.ui")
class AboutDialog(Gtk.AboutDialog):
    __gtype_name__ = 'AboutDialog'

    def __init__(self, version, **kwargs):
        super().__init__(**kwargs)
        self.set_version(version)