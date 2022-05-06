import logging
from gi.repository import Gio, GLib

class Settings(Gio.Settings):
    instance: 'Settings' = None

    def __init__(self):
        Gio.Settings.__init__(self)

    @staticmethod
    def new():
        g_settings = Gio.Settings.new('com.github.essmehdi.flow')
        g_settings.__class__ = Settings
        return g_settings

    @staticmethod
    def get():
        if Settings.instance is None:
            Settings.instance = Settings.new()
        return Settings.instance
    
    @property
    def categories(self):
        return dict(self.get_value("categories"))
    
    @categories.setter
    def categories(self, new_categories):
        self.set_value("categories", GLib.Variant('a{sa{ss}}', new_categories))

    def add_category(self, category, path, extensions):
        if category in self.categories:
            self.set_category_path(category, path)
        else:
            categories = self.categories
            categories[category] = { "path": path, "extensions": extensions }
            self.categories = categories

    def set_category_settings(self, category, path, extensions, old_category=None):
        categories = self.categories
        if old_category:
            categories[category] = {
                "path": path,
                "extensions": extensions
            }
            del categories[old_category]
            self.categories = categories
        elif category in categories:
            categories[category]["path"] = path
            categories[category]["extensions"] = extensions
            self.categories = categories
    
    def get_category_path(self, category):
        categories = self.categories
        if category in categories:
            return categories[category].get("path")

    def remove_category(self, category):
        categories = self.categories
        if category in categories:
            del categories[category]
            self.categories = categories

    @property
    def timeout(self):
        return self.get_uint('connection-timeout')

    @property
    def use_proxy(self):
        return self.get_boolean('connection-proxy')

    @property
    def proxy_address(self):
        return self.get_string('connection-proxy-address')
    
    @property
    def proxy_port(self):
        return self.get_uint('connection-proxy-port')

    @property
    def user_agent(self):
        return self.get_string('user-agent')

    @property
    def force_dark(self):
        return self.get_boolean('force-dark')

    @property
    def fallback_directory(self):
        return self.get_string('fallback-directory')