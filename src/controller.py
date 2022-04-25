from email.mime import application
from .components.browser_wait import BrowserWait
from .notifier import Notifier
from .download import Download
from .status_manager import StatusManager
from gi.repository import Gio, Gtk, GObject, Gdk, Notify, GLib
from gettext import gettext as _
import logging


class DownloadsController(GObject.GObject):
    __gtype_name__ = "DownloadsController"
    __instance = None

    selection_mode = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)

    @staticmethod
    def get_instance():
        if DownloadsController.__instance is None:
            DownloadsController()
        return DownloadsController.__instance

    def __init__(self):
        if DownloadsController.__instance is not None:
            raise Exception("Cannot make another instance")
        else:
            DownloadsController.__instance = self
        GObject.GObject.__init__(self)
        self.finished_downloads = Gio.ListStore.new(Download)
        self.running_downloads = Gio.ListStore.new(Download)

        finished_downloads = StatusManager.get_downloads(True)
        for id, item in finished_downloads.items():
            self.finished_downloads.insert(0, Download(id=id, status=item))

        running_downloads = StatusManager.get_downloads(False)
        for id, item in running_downloads.items():
            self.running_downloads.insert(0, Download(id=id, status=item))

        self.finished_list_box = None
        self.running_list_box = None
        self.clamp = None
        self.content = None
        self.delete_action = None
        self.selected_downloads = set()
        self.empty_stack = None
        self.waiting_for_link = None

    def load_ui(self, window):
        # Register UI components
        self.finished_list_box = window.finished_downloads_list
        self.running_list_box = window.running_downloads_list
        self.clamp = window.clamp
        self.content = window.content
        self.finished_list_box.bind_model(self.finished_downloads, self._binder)
        self.finished_list_box.set_header_func(self._finished_header_function)
        self.running_list_box.bind_model(self.running_downloads, self._binder)
        self.delete_action = window.delete_selected
        self.empty_stack = window.empty_stack
        self._update_ui()

    def disable_edit_mode(self, id):
        download = self._get_download(id)
        download.edit_mode = False

    def enable_edit_mode(self, id):
        download = self._get_download(id)
        from .components.download_edit import DownloadEdit
        edit_window = DownloadEdit(False, download.id, download.url, download.filename, download.output_directory, transient_for=download.row.get_root(), application=download.row.get_root().get_application())
        edit_window.show()
        download.edit_mode = True

    def confirm_download(self, download):
        download.row.get_root().present()
        from .components.download_edit import DownloadEdit
        edit_window = DownloadEdit(True, download.id, download.url, download.filename, download.output_directory, transient_for=download.row.get_root(), application=download.row.get_root().get_application())
        edit_window.show()
        download.edit_mode = True
        
    def edit(self, id, new_filename, new_directory):
        logging.debug(f"Editing download - {new_filename} - {new_directory}")
        download = self._get_download(id)
        if download.status != 'done':
            if new_filename is not None:
                download.filename = new_filename
            if new_directory is not None:
                download.custom_directory = True
                download.output_directory = new_directory
                download.category = ""
        if download.edit_mode:
            download.edit_mode = False

    def download_finished(self, id):
        StatusManager.download_finished(id)
        index = self._find_position_from_running(id)
        download = self.running_downloads.get_item(index)
        self.running_downloads.remove(index)
        self.finished_downloads.insert(0, download)
        self._update_ui()
        # Notify user
        Notifier.notify(_("Download finished"), download.filename, "folder-download-symbolic")
    
    def add_from_url(self, url, headers=None, raw_headers=None):
        if self.waiting_for_link is None:
            self.running_downloads.insert(0, Download(url=url, headers=headers, raw_headers=raw_headers))
            self._update_ui()
        else:
            self._update_link(url, headers, self.waiting_for_link[0], raw_headers is not None)

    def get_file(self, id):
        return self._get_download(id).get_file()

    def open(self, id, folder=False):
        self._get_download(id).open_folder() if folder else self._get_download(id).open_file()
        
    def pause(self, id):
        self._get_download(id).pause()

    def restart(self, id):
        download = self._get_download(id)
        if download.resumable:
            download.resume()
        else:
            url = download.url
            self._delete_with_id(id)
            self.add_from_url(url, raw_headers=download.custom_headers if download.custom_headers else None)

    def copy_url(self, id):
        # Set download URL as clipboard content
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set_content(Gdk.ContentProvider.new_for_value(self._get_download(id).url))

    def resume_with_link(self, id):
        download = self._get_download(id)
        popup = BrowserWait(transient_for=download.row.get_root(), application=download.row.get_root().get_application())
        popup.show()
        self.waiting_for_link = (download, popup)

    def _update_link(self, new_url, new_headers, download, raw):
        self.waiting_for_link[1].destroy()
        self.waiting_for_link = None
        download.resumable = True
        download.url = new_url
        download.setup_request_headers(new_headers, raw)
        download.resume()

    def delete(self, id, delete_file=False):
        self._delete_with_id(id, delete_file)

    def delete_selected_rows(self, _, __, window):
        self._delete_dialog(window)

    def enable_selection(self):
        self.selection_mode = True

    def disable_selection(self):
        self.delete_action.set_enabled(False)
        self.selected_downloads = set()
        self.selection_mode = False

    def select(self, id):
        self.delete_action.set_enabled(True)
        self.selected_downloads.add(id)

    def unselect(self, id):
        self.selected_downloads.remove(id)
        if len(self.selected_downloads) == 0:
            self.disable_selection()

    def _delete_with_index(self, index, running=False, delete_file=False):
        d_list = self.running_downloads if running else self.finished_downloads
        download = d_list.get_item(index)
        if download.delete(delete_file):
            d_list.remove(index)
            self._update_ui()
        # Check if it exists in selected downloads & remove it
        if self.selection_mode and download.id in self.selected_downloads:
            self.unselect(download.id)
    
    def _delete_with_id(self, id, delete_file=False):
        index = self._find_position_from_finished(id)
        if index != -1:
            return self._delete_with_index(index, False, delete_file)
        index = self._find_position_from_running(id)
        if index != -1:
            return self._delete_with_index(index, True, delete_file)
        else:
            logging.error(f"Controller: Could not find download with id: {id}")

    def _delete_dialog(self, window):
        delete_files_check = Gtk.CheckButton()
        delete_files_check.set_label(_("Delete with files"))
        confirm_dialog = Gtk.MessageDialog(
            transient_for = window,
            message_type = Gtk.MessageType.WARNING,
            buttons = Gtk.ButtonsType.YES_NO,
            text = _("Are you sure ?"),
            secondary_text = _("This will delete the selected download(s) from history.")
        )
        confirm_dialog.get_message_area().append(delete_files_check)
        confirm_dialog.connect("response", self._delete_dialog_response)
        confirm_dialog.set_modal(True)
        confirm_dialog.show()

    def _delete_dialog_response(self, dialog, response):
        delete_files_response = dialog.get_message_area().get_last_child().get_active()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            self._confirm_delete_selected(delete_files_response)
    
    def _confirm_delete_selected(self, delete_files=False):
        selected_list = [ self._get_download(id) for id in self.selected_downloads ]
        for row in selected_list:
            self._delete_with_id(row.id, delete_files)
        self.disable_selection()

    def _update_row_date_tag(self, row):
        if row.date_finished != 0:
            today: GLib.DateTime = GLib.DateTime.new_now_local()
            finished: GLib.DateTime = GLib.DateTime.new_from_unix_local(row.date_finished)
            delta = today.difference(finished) // 10**6 # From microseconds to seconds
            hours = delta / 3600
            if 0 <= hours < 24:
                # Day scale
                if finished.get_hour() > today.get_hour():
                    row.date_tag = row.DATE_TAG_YESTERDAY
                else:
                    row.date_tag = row.DATE_TAG_TODAY
            elif hours < 48 and finished.get_hour() < today.get_hour():
                row.date_tag = row.DATE_TAG_YESTERDAY
            else:
                # Weeks scale
                if hours < 168:
                    if finished.get_day_of_week() > today.get_day_of_week():
                        row.date_tag = row.DATE_TAG_LAST_WEEK
                    else:
                        row.date_tag = finished.format('%A')
                elif hours < 336 and finished.get_day_of_week() < today.get_day_of_week():
                    row.date_tag = row.DATE_TAG_LAST_WEEK
                else:
                    # Month scale
                    days = hours // 24
                    if days < 62:
                        month_delta = today.get_month() - finished.get_month()
                        if month_delta == 1 or month_delta == -11:
                            row.date_tag = row.DATE_TAG_LAST_MONTH
                        elif month_delta == 0:
                            row.date_tag = row.DATE_TAG_THIS_MONTH
                    else:
                        # Year scale
                        year_delta = today.get_year() - finished.get_year()
                        if year_delta == 1:
                            row.date_tag = row.DATE_TAG_LAST_YEAR
                        elif year_delta == 0:
                            row.date_tag = row.DATE_TAG_THIS_YEAR
                        else:
                            row.date_tag = row.DATE_TAG_MORE_YEAR

    def _finished_header_function(self, row, before, *_):
        self._update_row_date_tag(row)
        if before is None or row.date_tag != before.date_tag:
            label = Gtk.Label()
            label.set_label(row.date_tag)
            label.add_css_class("dim-label")
            label.set_halign(Gtk.Align.START)
            label.set_valign(Gtk.Align.CENTER)
            label.set_margin_start(10)
            label.set_margin_end(10)
            label.set_margin_top(10)
            label.set_margin_bottom(10)
            row.set_header(label)
        elif row.get_header() is not None:
            row.set_header(None)
        
    def _get_download(self, id):
        # Search in finished list
        index = self._find_position_from_finished(id)
        if index != -1:
            return self.finished_downloads.get_item(index)
        # Search in running list
        index = self._find_position_from_running(id)
        if index != -1:
            return self.running_downloads.get_item(index)
        else:
            logging.error(f"Could not find a download with the specified ID: {id}")

    def _find_position_from_finished(self, id):
        index = 0
        for download in self.finished_downloads:
            if download.id == id:
                return index
            index += 1
        return -1
    
    def _find_position_from_running(self, id):
        index = 0
        for download in self.running_downloads:
            if download.id == id:
                return index
            index += 1
        return -1

    def _foreach(self, box, row, *_):
        logging.debug(row.filename)

    def _binder(self, item):
        from .components.download_item import DownloadItem
        row = DownloadItem()
        item.bind_property("id", row, "id", GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("status", row, "status", GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("filename", row, "filename", GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("resumable", row, "resumable", GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("progress", row, "progress", GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("size", row, "size", GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("url", row, "url", GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("output_directory", row, "output_directory", GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("category", row, "category", GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("date_started", row, "date_started", GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("date_initiated", row, "date_initiated", GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("date_finished", row, "date_finished", GObject.BindingFlags.SYNC_CREATE)
        self.bind_property("selection_mode", row, "selection_mode", GObject.BindingFlags.SYNC_CREATE)
        item.row = row
        return row
        
    def _update_ui(self):
        if self.finished_list_box is not None:
            finished_count = self.finished_downloads.get_n_items() > 0
            running_count = self.running_downloads.get_n_items() > 0
            #                      Frame        ListBox 
            self.finished_list_box.get_parent().get_parent().set_visible(finished_count)
            self.running_list_box.get_parent().get_parent().set_visible(running_count)
            if not finished_count and not running_count:
                self.empty_stack.set_visible_child_name('empty_page')
            else:
                self.empty_stack.set_visible_child_name('not_empty_page')