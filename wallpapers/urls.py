from django.urls import path
from . import views

app_name = "wallpapers"

urlpatterns = [
    path("", views.home, name="home"),
    path("logout/", views.logout_view, name="logout"),
    path("upload/", views.upload, name="upload"),
    path("w/<slug:slug>/", views.detail, name="detail"),
    path("<slug:slug>/delete/", views.delete_wallpaper, name="delete"),
    path("w/<slug:slug>/download/", views.download, name="download"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
]
