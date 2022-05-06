import os
import threading
import uuid
from gi.repository import GObject, GLib, Gio
import pycurl

from flow.utils.notifier import Notifier

from flow.utils.misc import create_download_temp, file_extension_match

from flow.utils.status_manager import StatusManager
import logging
import shutil
import mimetypes
import cgi
import time
from urllib.parse import unquote, urlparse
from flow.core.settings import Settings
from flow.utils.toaster import Toaster
from gettext import gettext as _
import validators


class Download(GObject.Object):
    __gtype_name__ = "Download"

    # Properties that should not be saved to status file
    PROPERTIES_BLACKLIST = ["progress", "open_on_finish"]

    # Status strings
    STATUS_STARTED = 'downloading'
    STATUS_REQUEST_ERROR = 'request_error'
    STATUS_MOVE_ERROR = 'move_error'
    STATUS_RESUME_ERROR = 'resume_error'
    STATUS_DONE = 'done'
    STATUS_TIMEOUT_ERROR = 'read_timeout_error'
    STATUS_CONNECTION_ERROR = 'connection_error'
    STATUS_INIT = 'init'
    STATUS_PAUSED = 'paused'
    STATUS_MOVING = 'moving'

    # Download path fallback
    DOWNLOAD_FALLBACK_PATH = "~/Downloads"

    # Download properties
    id                  = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    status              = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    url                 = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    tmp                 = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    output_directory    = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    custom_directory    = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
    date_initiated      = GObject.Property(type=GObject.GType.from_name('gulong'), default=0, flags=GObject.ParamFlags.READWRITE)
    date_started        = GObject.Property(type=GObject.GType.from_name('gulong'), default=0, flags=GObject.ParamFlags.READWRITE)
    date_finished       = GObject.Property(type=GObject.GType.from_name('gulong'), default=0, flags=GObject.ParamFlags.READWRITE)
    filename            = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    category            = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    size                = GObject.Property(type=GObject.GType.from_name('glong'), default=-1, flags=GObject.ParamFlags.READWRITE)
    resumable           = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
    progress            = GObject.Property(type=GObject.GType.from_name('gulong'), default=0, flags=GObject.ParamFlags.READWRITE)
    open_on_finish      = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)
    custom_headers      = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    info_parsed         = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, id: str = None, status: dict = None, url: str = None, headers: dict = None, raw_headers: str = None):
        GObject.Object.__init__(self)
        # Update fallback path based on user settings
        fallback_directory = Settings.get().fallback_directory
        if fallback_directory:
            Download.DOWNLOAD_FALLBACK_PATH = fallback_directory
        # UI item for easy access
        self.row = None
        # Edit mode flag
        self.edit_mode = False
        # cURL worker
        self.worker = None
        self.worker_thread = None
        # Progress offset (when cURL resumes download, count starts from 0 not from offset)
        self.offset = 0
        # Response headers
        self.response_headers = {}
        # Write mode
        self.mode = "wb"
        # Cancel flag & confirmation
        self.cancel = False
        self.cancelled = False
        # Custom user agent
        self.ua = None
        if not status:
            # Means that this is a new download
            self.id = str(uuid.uuid4())
            new_temp_file = create_download_temp(self.id)
            status = StatusManager.register_download(self.id, url=url, tmp=new_temp_file.get_path())
            # Notify user
            Notifier.notify(self.id, _("Download initiated"), url, "folder-download-symbolic")
        else:
            self.id = id
        self.populate_properties(status)
        self.connect("notify", self.handle_property_change)
        if headers is not None:
            logging.debug("New download with custom headers")
            self.setup_request_headers(headers)
        elif raw_headers is not None:
            logging.debug("New download with custom headers (raw)")
            self.setup_request_headers(raw_headers, True)
        self.setup()

    def setup_request_headers(self, headers, raw=False):
        logging.debug('Registering request headers')
        if raw:
            self.custom_headers = headers
        else:
            new_custom_headers = ''
            for line in headers:
                if line.get('value'):
                    if line.get('name') == 'User-Agent':
                        self.ua = line.get('value')
                    new_custom_headers += f",{line['name']}: {line['value']}"
            self.custom_headers = new_custom_headers

    def populate_properties(self, status: dict):
        # Populate properties with provided status object
        for property, value in status.items():
            setattr(self, property, value)

    def setup(self):
        if self.status != Download.STATUS_DONE:
            self.worker = pycurl.Curl()
            self.worker.setopt(pycurl.FAILONERROR, True)
            self.worker.setopt(pycurl.URL, self.url)
            self.worker.setopt(pycurl.FOLLOWLOCATION, True)
            if len(self.custom_headers):
                self.worker.setopt(pycurl.HTTPHEADER, self.custom_headers.split(','))
        if self.status == Download.STATUS_MOVING:
            if os.path.exists(self.tmp):
                self._move_file()
            else:
                self._finalize()
        if self.status == Download.STATUS_STARTED:
            # Means probably that program closed unexpectedly.
            # Therefore, change status value to 'paused'
            self.status = Download.STATUS_PAUSED
        if self.status == Download.STATUS_PAUSED or ('error' in self.status and self.resumable):
            if os.path.exists(self.tmp):
                self.offset = os.path.getsize(self.tmp)
                self.worker.setopt(pycurl.RESUME_FROM, self.offset)
                self.progress = self.offset
                self.mode = "ab"
            else:
                self.resumable = False
        if self.status == "":
            self.start()

    def pause(self, *_):
        self.worker.pause(pycurl.PAUSE_ALL)
        self.status = Download.STATUS_PAUSED

    def resume(self, *_):
        if self.worker_thread is not None and self.status == 'paused':
            self.worker.pause(pycurl.PAUSE_CONT)
            self.status = Download.STATUS_STARTED
        else:
            self.setup()
            self.start()

    def start(self):
        # Starts download
        self.get_download_preferences()
        self.worker_thread = threading.Thread(target=self._start_download, daemon=True)
        self.worker_thread.start()

    def header_function(self, header_line):
        header_line = header_line.decode('iso-8859-1')
        if ':' not in header_line:
            if header_line == "\r\n" and len(self.response_headers.keys()):
                self._decode_headers()
            return
        name, value = header_line.split(':', 1)
        name = name.strip().lower()
        value = value.strip()
        self.response_headers[name] = value
    
    def _decode_headers(self):
        if not self.info_parsed:
            # Detect filename
            reported = False
            logging.debug(self.response_headers)
            if 'content-disposition' in self.response_headers:
                _, params = cgi.parse_header(self.response_headers['content-disposition'])
                if 'filename' in params:
                    self.filename = unquote(params.get('filename').encode('iso-8859-1').decode('utf8'))
                    reported = True
            if not reported:
                parsed_url = urlparse(self.url)
                filename = unquote(parsed_url.path).split("/")[-1]
                if len(filename) >= 200:
                    filename = filename[-1:-100:-1].strip()
                elif filename == "":
                    filename = parsed_url.netloc
                if "content-type" in self.response_headers and self.response_headers['content-type'] != 'application/octet-stream':
                    ext = mimetypes.guess_extension(self.response_headers['content-type'])
                    if ext and not mimetypes.guess_type(filename)[0] == self.response_headers['content-type'] and not filename.endswith(ext):
                        filename += ext
                self.filename = filename
            
            # Detect category
            if self.output_directory == "" and not self.custom_directory:
                _, extension = os.path.splitext(self.filename)
                categories = Settings.get().categories
                if extension:
                    for category, settings in categories.items():
                        if file_extension_match(self.filename, settings.get('extensions')):
                            directory = settings.get("path")
                            if os.path.exists(directory):
                                self.category = category
                                self.output_directory = directory
                            else:
                                self.output_directory = os.path.expanduser(Download.DOWNLOAD_FALLBACK_PATH)
                            break
                logging.debug(f"Detected output directory: {self.output_directory}")
                if self.output_directory == "":
                    self.output_directory = os.path.expanduser(Download.DOWNLOAD_FALLBACK_PATH)
            
            # Detect if download resumable
            if 'content-length' in self.response_headers:
                self.size = int(self.response_headers.get('content-length'))
                self.resumable = True
                # if 'accept-ranges' in self.response_headers:
                    # self.resumable = True

            # Flag info as parsed (In case of resume)
            self.info_parsed = True
            # from .controller import DownloadsController
            # GLib.idle_add(lambda: DownloadsController.get_instance().confirm_download(self))

    def _start_download(self):
        # Start data transfer
        logging.info("Starting download")
        self.worker.setopt(pycurl.NOPROGRESS, False)
        self.worker.setopt(pycurl.XFERINFOFUNCTION, self.report_progress)
        if not self.info_parsed:
            self.worker.setopt(pycurl.HEADERFUNCTION, self.header_function)
        self.status = Download.STATUS_STARTED
        self.date_started = GLib.DateTime.new_now_local().to_unix()
        try:
            if self.offset != self.size:
                with open(self.tmp, self.mode) as file:
                    self.worker.setopt(pycurl.WRITEDATA, file)
                    self.worker.perform()
        except pycurl.error as error:
            self._handle_error(error.args)
        else:
            self.date_finished = GLib.DateTime.new_now_local().to_unix()
            if self.size < 0:
                self.size = os.path.getsize(self.tmp)
            while self.edit_mode and not self.cancel:
                logging.debug("Waiting for edit mode...")
                time.sleep(1)
            if self.cancel:
                self.cancelled = True
                self.worker.close()
                return
            self.worker.close()
            self.status = Download.STATUS_MOVING
            self._move_file()
            self._finalize()

    def _move_file(self):
        output_path = self.get_output_file_path()
        if os.path.exists(output_path):
            count = 1
            while True:
                name, ext = os.path.splitext(self.filename)
                name += f" ({count})"
                dup_filename = name + ext
                if not os.path.exists(os.path.join(self.output_directory, dup_filename)):
                    self.filename = dup_filename
                    output_path = self.get_output_file_path()
                    break
                count += 1
        logging.debug(f"Moving file to: {output_path}")
        shutil.move(self.tmp, output_path)
        if self.open_on_finish:
            self.open_file()

    def _finalize(self):
        self.status = Download.STATUS_DONE
        from .controller import DownloadsController # To avoid circular import
        GLib.idle_add(lambda: DownloadsController.get_instance().download_finished(self.id))
        logging.info("Download finished")

    def _handle_error(self, args):
        logging.exception(f"Error while performing cURL: {args[1]}")
        match args[0]:
            case pycurl.E_ABORTED_BY_CALLBACK:
                logging.info("Download cancelled")
                self.cancelled = True
                self.cancel = False
            case pycurl.E_HTTP_RETURNED_ERROR:
                self.status = Download.STATUS_REQUEST_ERROR
            case pycurl.E_OPERATION_TIMEDOUT:
                self.status = Download.STATUS_TIMEOUT_ERROR
            case pycurl.E_RANGE_ERROR:
                self.status = Download.STATUS_RESUME_ERROR
                self.resumable = False
            case _:
                self.status = Download.STATUS_CONNECTION_ERROR
        # Notify user
        if args[0] != pycurl.E_ABORTED_BY_CALLBACK:
            Notifier.notify(self.id, _("Downlod error"), _("An error occured while downloading"), "folder-download-symbolic")

    def get_output_file_path(self):
        if self.output_directory:
            return os.path.join(self.output_directory, self.filename)
        else:
            logging.error("Could not get file path")

    def get_file(self):
        file_path = self.get_output_file_path()
        if file_path is not None and os.path.exists(file_path):
            return Gio.File.new_for_path(file_path)

    def report_progress(self, __, downloaded, *_):
        if self.cancel:
            return -1 # Non zero value to abort transfer
        self.progress = self.offset + downloaded

    def get_download_preferences(self):
        # Setup connection timeout
        timeout = Settings.get().timeout
        logging.debug(f"Preference timeout: {timeout}s")
        self.worker.setopt(pycurl.CONNECTTIMEOUT, timeout)
        self.worker.setopt(pycurl.LOW_SPEED_LIMIT, 1)
        self.worker.setopt(pycurl.LOW_SPEED_TIME, timeout)
        # Setup request user agent
        user_agent = Settings.get().user_agent
        if self.ua is not None:
            logging.debug(f"Header user agent: {self.ua}")
            self.worker.setopt(pycurl.USERAGENT, self.ua)
        elif user_agent:
            logging.debug(f"Preference user agent: {user_agent}")
            self.worker.setopt(pycurl.USERAGENT, user_agent)
        # Setup proxy settings
        use_proxy = Settings.get().use_proxy
        proxy_address = Settings.get().proxy_address
        logging.debug(f"Preference proxy enabled: {use_proxy}")
        if use_proxy and proxy_address and validators.url(proxy_address):
            logging.debug('Proxy: Using custom settings')
            self.worker.setopt(pycurl.PROXY, proxy_address)
            self.worker.setopt(pycurl.PROXYPORT, Settings.get().proxy_port)
        else:
            # Use GNOME proxy settings
            logging.debug('Proxy: Using GNOME settings')
            proxy_resolver = Gio.ProxyResolver.get_default()
            proxy = proxy_resolver.lookup(self.url)
            logging.debug(f'GNOME Proxy Resolver: {proxy[0]}')
            if not proxy[0].startswith('direct://'):
                self.worker.setopt(pycurl.PROXY, proxy[0])

    def open_file(self):
        if self.status == 'done':
            file_path = self.get_output_file_path()
            if os.path.exists(file_path):
                logging.debug(f"Launching file: {file_path}")
                Gio.AppInfo.launch_default_for_uri("file://" + file_path)
            else:
                Toaster.show(_("The file has been moved or deleted"))
        else:
            self.open_on_finish = True
            Toaster.show(_("The file will be automatically opened once download is finished"))

    def open_folder(self):
        if self.status == 'done':
            Gio.AppInfo.launch_default_for_uri("file://" + self.output_directory)
    
    def handle_property_change(self, _, prop):
        # Apparently, property names are incorrectly set. Underscores are considered
        # dashes. Why ? :/
        property = prop.name.replace("-", "_")
        value = getattr(self, property)
        if property not in Download.PROPERTIES_BLACKLIST:
            logging.debug(f"Property {property} changed to {value}")
            StatusManager.update_property(self.id, property, value)

    def delete(self, delete_file = False):
        if self.status == 'downloading':
            self.cancel = True
            while not self.cancelled:
                logging.debug("Waiting for cancellation...")
                time.sleep(0.5)
        try:
            StatusManager.remove_download(self.id, self.status == 'done', delete_file)
        except:
            logging.exception("Failed to delete download")
            return False
        else:
            return True