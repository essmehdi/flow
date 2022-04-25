import logging

from ..settings import Settings
from .category_editor import CategoryEditor
from gi.repository import Gtk, Adw
from gettext import gettext as _


@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/preferences/category_row.ui")
class CategoryRow(Adw.ActionRow):
    __gtype_name__ = "CategoryRow"

    def __init__(self, category, settings, **kwargs):
        super().__init__(**kwargs)
        self.category = category
        self.settings = settings
        self.refresh_ui()

    def refresh_ui(self):
        self.set_title(self.category)
        self.set_subtitle(self.settings.get("path", "-empty-"))
    
    @Gtk.Template.Callback()
    def activate_handler(self, *_):
        self.editor = CategoryEditor(self.category, self.settings, self.update_ui, transient_for=self.get_root(), application=self.get_root().get_application())
        self.editor.show()

    @Gtk.Template.Callback()
    def delete_category(self, *__):
        confirm_dialog = Gtk.MessageDialog(
            transient_for = self.get_root(),
            message_type = Gtk.MessageType.WARNING,
            buttons = Gtk.ButtonsType.YES_NO,
            text = _("Are you sure?"),
            secondary_text = _("This action cannot be undone. You will permanently delete this category.")
        )
        confirm_dialog.connect("response", self.confirm_delete_category)
        confirm_dialog.set_modal(True)
        confirm_dialog.show()

    def confirm_delete_category(self, dialog, response):
        if response == Gtk.ResponseType.YES:
            Settings.get().remove_category(self.category)
            dialog.destroy()
            self.get_parent().remove(self)
        else:
            dialog.destroy()

    def update_ui(self, category, settings):
        self.category = category
        self.settings = settings
        self.refresh_ui()
