from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
]

try:
    from tests.tastypie_api.urls import api
    from graph_wrap.tastypie.graphql_view import graphql_view
except ImportError:
    pass
else:
    urlpatterns.append(path(r'tastypie/', include(api.urls)))
    urlpatterns.append(path(r'tastypie/v1/graphql/', view=graphql_view))
try:
    from tests.django_rest_framework_api.urls import router
    from graph_wrap.django_rest_framework.graphql_view import graphql_view
except ImportError:
    pass
else:
    urlpatterns.append(path(r'django_rest/', include(router.urls)))
    urlpatterns.append(path(r'django_rest/graphql/', view=graphql_view))
    urlpatterns.append(
        path('api-auth/',
             include('rest_framework.urls', namespace='rest_framework')))
