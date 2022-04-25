import os

from ..settings import Settings
from gi.repository import Gtk, Adw, Gio
from gettext import gettext as _

@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/preferences/category_editor.ui")
class CategoryEditor(Adw.Window):
    __gtype_name__ = "CategoryEditor"

    name_entry = Gtk.Template.Child()
    path_button = Gtk.Template.Child()
    extensions_entry = Gtk.Template.Child()

    def __init__(self, category, settings, callback, **kwargs):
        super().__init__(**kwargs)
        # If category is not supplied, editor is in "Add Mode"
        if category:
            self.category = category
            self.settings = settings
            self.name_entry.set_text(category)
            self.path_button.value = settings["path"]
            self.extensions_entry.set_text(settings["extensions"])
            self.add_mode = False
        else:
            self.add_mode = True
        self.callback = callback
        # Actions
        self.actions = Gio.SimpleActionGroup.new()
        self.save_edit_action = Gio.SimpleAction.new('save')
        self.save_edit_action.connect('activate', self.save_edit)
        self.actions.add_action(self.save_edit_action)
        self.cancel_edit_action = Gio.SimpleAction.new('cancel')
        self.cancel_edit_action.connect('activate', self.cancel_edit)
        self.actions.add_action(self.cancel_edit_action)
        self.insert_action_group('cedit', self.actions)

    # @Gtk.Template.Callback()
    # def path_button_clicked(self, *_):
    #     chooser = Gtk.FileChooserDialog(transient_for=self, application=self.get_application())
    #     chooser.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
    #     chooser.set_title("Choose a directory")
    #     chooser.add_buttons(
    #         "Cancel", Gtk.ResponseType.CANCEL, 
    #         "Select", Gtk.ResponseType.OK)
    #     chooser.set_modal(True)
    #     chooser.get_widget_for_response(response_id=Gtk.ResponseType.OK).get_style_context().add_class(class_name="suggested-action")
    #     chooser.connect("response", self.path_chooser_response)
    #     chooser.show()

    # def path_chooser_response(self, chooser, response):
    #     if response == Gtk.ResponseType.OK:
    #         selected_path = chooser.get_file().get_path()
    #         if os.access(selected_path, os.W_OK):
    #             self.current_path = selected_path
    #             self.path_button_content.set_label(self.current_path)
    #         else:
    #             error_dialog = Gtk.MessageDialog(
    #                 transient_for = self,
    #                 message_type = Gtk.MessageType.ERROR,
    #                 buttons = Gtk.ButtonsType.OK,
    #                 text = _("Permission error"),
    #                 secondary_text = _("{} is not writable").format(selected_path)
    #             )
    #             error_dialog.connect("response", lambda *_: error_dialog.destroy())
    #             error_dialog.set_modal(True)
    #             error_dialog.show()
    #     chooser.destroy()
    
    @Gtk.Template.Callback()
    def entry_edit(self, entry):
        if not len(entry.get_text()):
            self.set_empty_error(entry)
        else:
            self.clear_empty_error(entry)

    def set_empty_error(self, widget):
        widget.add_css_class("error")
        widget.set_tooltip_text(_("Must not be empty"))
    
    def clear_empty_error(self, widget):
        widget.remove_css_class("error")
        widget.set_tooltip_text("")

    def save_edit(self, *args):
        new_category = self.name_entry.get_text()
        new_settings = {
            "path": self.path_button.value,
            "extensions": self.extensions_entry.get_text().strip()
        }
        if not len(new_category):
            self.name_entry.grab_focus()
            self.set_empty_error(self.name_entry)
            return
        if not len(new_settings["path"]):
            self.path_button.grab_focus()
            self.set_empty_error(self.path_button)
            return
        if not len(new_settings["extensions"]):
            self.extensions_entry.grab_focus()
            self.set_empty_error(self.name_entry)
            return
        if self.add_mode:
            Settings.get().add_category(
                new_category,
                new_settings["path"],
                new_settings["extensions"],
            )
        else:
            Settings.get().set_category_settings(
                new_category,
                new_settings["path"],
                new_settings["extensions"],
                self.category if new_category != self.category else None
            )
        if self.callback:
            self.callback(new_category, new_settings)
        self.destroy()

    def cancel_edit(self, *_):
        self.destroy()
