import gi
import logging

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib


"""
A Toaster service to show a notification from every component of the app
"""

overlay = None
def register_overlay(new_overlay):
    global overlay
    if isinstance(new_overlay, Adw.ToastOverlay):
        overlay = new_overlay
    else:
        logging.error("The object passed is not a valid overlay")

def show(text, action = None, timeout = 3, priority = Adw.ToastPriority.NORMAL):
    global overlay
    if not overlay:
        logging.error("No overlay registered")
    else:
        toast = Adw.Toast.new(text)
        if action is not None:
            toast.set_button_label(action.get('label', 'Action'))
            toast.set_button_action(action.get('name'))
        toast.set_timeout(timeout)
        toast.set_priority(priority)
        overlay.add_toast(toast)