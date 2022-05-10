from gi.repository import Gtk
from flow.utils.app_info import AppInfo

@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/about.ui")
class AboutDialog(Gtk.AboutDialog):
    __gtype_name__ = 'AboutDialog'

    def __init__(self, version, **kwargs):
        super().__init__(**kwargs)
        self.set_version(version)
        self.set_program_name(AppInfo.name)