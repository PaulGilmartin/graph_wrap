from django.contrib import admin
from django.urls import path, include

from tests.tastypie_api.urls import api

urlpatterns = [
    path(r'tastypie/', include(api.urls)),
    path('admin/', admin.site.urls),
]

