import gi
import logging

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw


"""
A Toaster service to show a notification from every component of the app
"""

class Toaster():

    overlay = None

    @staticmethod
    def register_overlay(overlay):
        if isinstance(overlay, Adw.ToastOverlay):
            Toaster.overlay = overlay
        else:
            logging.error("The object passed is not a valid overlay")

    @staticmethod
    def show(self, text, action = None, timeout = 3, priority = Adw.ToastPriority.NORMAL):
        if not Toaster.overlay:
            logging.error("No overlay registered")
        else:
            toast = Adw.Toast.new(text)
            if action is not None:
                toast.set_button_label(action.get('label', 'Action'))
                toast.set_button_action(action.get('name'))
            toast.set_timeout(timeout)
            toast.set_priority(priority)
            Toaster.overlay.add_toast(toast)