from django.contrib import admin
from .models import Wallpaper

@admin.register(Wallpaper)
class WallpaperAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "resolution_label", "downloads", "updated_at", "created_at")
    search_fields = ("title","category", "device","resolution_label")
    list_filter = ("category","resolution_label","created_at", "updated_at", "device")
    prepopulated_fields = {"slug": ("title",)}
