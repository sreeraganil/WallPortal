from django.contrib import admin
from .models import Wallpaper

@admin.register(Wallpaper)
class WallpaperAdmin(admin.ModelAdmin):
    list_display = ("title","category","resolution_label","downloads","created_at")
    search_fields = ("title","category","resolution_label")
    list_filter = ("category","resolution_label","created_at")
    prepopulated_fields = {"slug": ("title",)}
