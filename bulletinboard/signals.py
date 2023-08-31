from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
import threading

from bulletinboard.models import Message

User = get_user_model()

# Use threading.local to store the request object
thread_locals = threading.local()


def get_current_request():
    return getattr(thread_locals, 'request', None)


@receiver(post_save, sender=Message)
def notify_author_when_message(sender, instance, **kwargs):
    request = get_current_request()

    if request and request.user.is_authenticated:
        author_email = request.user.email

        subject = f'Новый отклик на ваш пост "{instance.post}"!'
        message = f'Пользователь {instance.author} оставил новый отклик под вашим постом "{instance.post}"'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [author_email]

        send_mail(subject, message, from_email, recipient_list)


@receiver(pre_save, sender=Message)
def notify_message_author_when_approved(sender, instance, **kwargs):
    try:
        original_instance = Message.objects.get(pk=instance.pk)  # Get the original instance from the database
        if not original_instance.is_approved and instance.is_approved:
            subject = f'Ваш отклик под постом "{instance.post}" был подтвержден автором поста и опубликован!'
            message = f'Пользователь {instance.post.author} подтвердил ваш отклик под постом "{instance.post}"!\n' \
                      f'Ваш отклик: "{instance.text}"'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [instance.author.user.email]
            send_mail(subject, message, from_email, recipient_list)

    except Message.DoesNotExist:
        pass


# Middleware to set the request object in thread_locals
class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        thread_locals.request = request
        response = self.get_response(request)
        return response
