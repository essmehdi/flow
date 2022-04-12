from gi.repository import Gtk, GObject
from gettext import gettext as _
import os

@Gtk.Template(resource_path="/com/github/essmehdi/flow/layout/file_chooser_button.ui")
class FileChooserButton(Gtk.Button):
    __gtype_name__ = 'FileChooserButton'

    button_content = Gtk.Template.Child()
    value          = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)

    def __init__(self, initial_value=None, **kwargs):
        super().__init__(**kwargs)
        if initial_value:
            self.value = initial_value
        else:
            self.value = ""
        self.connect('notify::value', self.on_value_change)

    def on_value_change(self, *__):
        self.button_content.set_label(self.value if self.value else _("Choose a directory"))
    
    @Gtk.Template.Callback()
    def button_clicked(self, *__):
        root = self.get_root()
        chooser = Gtk.FileChooserDialog(transient_for=root, application=root.get_application())
        chooser.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        chooser.set_title(_("Choose a directory"))
        chooser.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL, 
            _("Select"), Gtk.ResponseType.OK)
        chooser.set_modal(True)
        chooser.get_widget_for_response(response_id=Gtk.ResponseType.OK).get_style_context().add_class(class_name="suggested-action")
        chooser.connect("response", self.path_chooser_response)
        chooser.show()

    def path_chooser_response(self, chooser, response):
        if response == Gtk.ResponseType.OK:
            selected_path = chooser.get_file().get_path()
            if os.access(selected_path, os.W_OK):
                self.value = selected_path
            else:
                error_dialog = Gtk.MessageDialog(
                    transient_for = self.get_root(),
                    message_type = Gtk.MessageType.ERROR,
                    buttons = Gtk.ButtonsType.OK,
                    text = _("Permission error"),
                    secondary_text = _("{} is not writable").format(selected_path)
                )
                error_dialog.connect("response", lambda *__: error_dialog.destroy())
                error_dialog.set_modal(True)
                error_dialog.show()
        chooser.destroy()
        