import logging
from gi.repository import Gio

class Notifier():
    
    app = None

    @staticmethod
    def init(app):
        Notifier.app = app

    @staticmethod
    def notify(id, title = "", body = "", icon = None, urgency = Gio.NotificationPriority.NORMAL):
        logging.debug(f"Sending notification: {id} - {title} - {body}")
        if Notifier.app is None:
            logging.error("Application not launched")
            return
        notification = Gio.Notification()
        notification.set_title(title)
        notification.set_body(body)
        notification.set_icon(Gio.ThemedIcon.new(icon))
        notification.set_priority(urgency)
        notification.set_default_action('app.raise')
        Notifier.app.send_notification(id, notification)
