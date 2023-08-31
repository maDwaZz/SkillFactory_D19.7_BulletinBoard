from django_filters import FilterSet, ModelChoiceFilter
from .models import Post


class MessageFilter(FilterSet):
    post = ModelChoiceFilter(
        field_name='post',
        queryset=Post.objects.none()  # Initialize with an empty queryset
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.filters['post'].queryset = Post.objects.filter(author=user.author)
