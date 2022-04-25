from gi.repository import Notify

class Notifier():
    
    @staticmethod
    def notify(summary = "", body = "", icon = None, urgency = Notify.Urgency.NORMAL):
        if not Notify.is_initted():
            Notify.init('com.github.essmehdi.flow')
        notification = Notify.Notification.new(summary, body, icon)
        notification.set_urgency(urgency)
        notification.show()
