from django.contrib import admin
from .models import *


class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'category', 'creation_time')
    list_display_links = ('id', 'title', 'author')
    search_fields = ('title', 'author', 'body')
    list_filter = ('creation_time', 'author')


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'author', 'post', 'creation_time', 'is_approved')
    list_display_links = ('id', 'author', 'post')
    search_fields = ('author', 'post')
    list_filter = ('creation_time', 'author', 'post')
    list_editable = ('is_approved',)


admin.site.register(Author)
admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Message, MessageAdmin)
