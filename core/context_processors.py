from .models import Message, Notification


def unread_count(request):
    """Dodaj broj nepročitanih poruka i notifikacija u sve template-e"""
    if request.user.is_authenticated:
        unread_messages = Message.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        return {
            'unread_count': unread_messages,
            'unread_notifications': unread_notifications,
        }

    return {
        'unread_count': 0,
        'unread_notifications': 0,
    }
