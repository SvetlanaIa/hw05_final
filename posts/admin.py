from django.contrib import admin
from .models import Post, Group


class GroupAdmin(admin.ModelAdmin):
    # перечисляем поля, которые должны отображаться в админке
    list_display = ("pk", "title", "slug", "description")
    empty_value_display = "-пусто-"


class PostAdmin(admin.ModelAdmin):
    # перечисляем поля, которые должны отображаться в админке
    list_display = ("pk", "text", "pub_date", "author", "group")
    # добавляем интерфейс для поиска по тексту постов
    search_fields = ("text",)
    # добавляем возможность фильтрации по дате
    list_filter = ("pub_date", "group")
    empty_value_display = "-пусто-"


admin.site.register(Group, GroupAdmin)
admin.site.register(Post, PostAdmin)
