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
    __instance = None

    @staticmethod
    def get_instance():
        if Toaster.__instance is None:
            Toaster()
        return Toaster.__instance

    def __init__(self):
        if Toaster.__instance is not None:
            raise Exception("Cannot make another instance")
        else:
            Toaster.__instance = self

    def register_overlay(self, new_overlay):
        if isinstance(new_overlay, Adw.ToastOverlay):
            self.overlay = new_overlay
        else:
            logging.error("The object passed is not a valid overlay")

    def show(self, text, action = None, timeout = 3, priority = Adw.ToastPriority.NORMAL):
        if not self.overlay:
            logging.error("No overlay registered")
        else:
            toast = Adw.Toast.new(text)
            if action is not None:
                toast.set_button_label(action.get('label', 'Action'))
                toast.set_button_action(action.get('name'))
            toast.set_timeout(timeout)
            toast.set_priority(priority)
            self.overlay.add_toast(toast)