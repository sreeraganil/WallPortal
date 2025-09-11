from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from wallpapers import views
from core.views import robots_txt

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("wallpapers.urls", namespace="wallpapers")),
    path('about/', views.about_view, name='about'),
    path('privacy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms/', views.terms_of_service_view, name='terms_of_service'),
    path('contact/', views.contact_view, name='contact'),
    path("robots.txt", robots_txt),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path("_debug_/", include(debug_toolbar.urls))]
