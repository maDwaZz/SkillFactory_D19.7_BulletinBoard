from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'
        ordering = ['id']


class Post(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name='Автор')
    category = models.ForeignKey('Category', models.CASCADE, verbose_name='Категория')
    creation_time = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    title = models.CharField(max_length=255, blank=False, verbose_name='Заголовок')
    body = RichTextUploadingField(verbose_name='Содержание')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post', kwargs={'post_id': self.pk})

    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        ordering = ['-creation_time', 'title']


class Message(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name='Связанный пост')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name='Автор')
    creation_time = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    text = models.TextField(blank=False, verbose_name='Содержание')
    is_approved = models.BooleanField(default=False, verbose_name='Подтверждение')

    def __str__(self):
        return self.text[:20]

    class Meta:
        verbose_name = 'Отклик'
        verbose_name_plural = 'Отклики'
        ordering = ['-creation_time']


class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True, verbose_name='Категория')
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name='URL')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category', kwargs={'cat_slug': self.slug})

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['id']


class OneTimeCode(models.Model):
    one_time_code = models.CharField(max_length=10, unique=True, verbose_name='Одноразовый код подтверждения')

    def __str__(self):
        return self.one_time_code
