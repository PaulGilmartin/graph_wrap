from django.contrib import admin
from django.urls import path, include

from graph_wrap.django_rest_framework.graphql_view import graphql_view
from tests.django_rest_framework_api.urls import router
from tests.tastypie_api.urls import api

urlpatterns = [
    path(r'tastypie/', include(api.urls)),
    path(r'django_rest/', include(router.urls)),
    path(r'django_rest/graphql/', view=graphql_view),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

