from rest_framework import routers

from tests.django_rest_framework_api.api import (
    AuthorViewSet, PostViewSet)

router = routers.DefaultRouter()
router.register(r'author', AuthorViewSet)
router.register(r'post', PostViewSet)
