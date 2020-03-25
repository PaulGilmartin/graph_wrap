from django.contrib import admin
from django.urls import path, include
from tastypie.api import Api

from graph_wrap import GraphQLResource
from tests.api import AuthorResource, PostResource, MediaResource


api = Api('v1')
api.register(AuthorResource())
api.register(PostResource())
api.register(MediaResource())
api.register(GraphQLResource())

urlpatterns = [
    path(r'', include(api.urls)),
    path('admin/', admin.site.urls),
]
