from gi.repository import GObject
from gettext import gettext as _

class Download(GObject.Object):
    __gtype_name__ = "Download"

    # Download properties
    id                      = GObject.Property(type=GObject.GType.from_name('gulong'), default=0, flags=GObject.ParamFlags.READWRITE)
    status                  = GObject.Property(type=int, default=0, flags=GObject.ParamFlags.READWRITE)
    url                     = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    temp_file               = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    output_file             = GObject.Property(type=str, default=None, flags=GObject.ParamFlags.READWRITE)
    detected_output_file    = GObject.Property(type=str, default=None, flags=GObject.ParamFlags.READWRITE)
    date_added              = GObject.Property(type=int, default=0, flags=GObject.ParamFlags.READWRITE)
    date_completed          = GObject.Property(type=int, default=None, flags=GObject.ParamFlags.READWRITE)
    # category                = GObject.Property(type=str, default="", flags=GObject.ParamFlags.READWRITE)
    size                    = GObject.Property(type=GObject.GType.from_name('gulong'), default=None, flags=GObject.ParamFlags.READWRITE)
    resumable               = GObject.Property(type=bool, default=False, flags=GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
