from django.db.models import Count

from .models import *

menu = [{'title': 'О сайте', 'url_name': 'about'},
        {'title': 'Обратная связь', 'url_name': 'contact'},
        {'title': 'Добавить статью', 'url_name': 'add_post'},
        {'title': 'Просмотреть отклики', 'url_name': 'messages'},
        ]


class DataMixin:
    def get_user_context(self, **kwargs):
        context = kwargs
        cats = Category.objects.annotate(Count('post'))
        user_menu = menu.copy()
        if not self.request.user.is_authenticated:
            user_menu.pop(2)
            user_menu.pop(2)
        context['menu'] = user_menu
        context['cats'] = cats
        if 'cat_selected' not in context:
            context['cat_selected'] = 0
        return context
