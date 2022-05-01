from rest_framework import routers

from tests.django_rest_framework_api.api import (
    AuthorViewSet, PostViewSet)

router = routers.SimpleRouter()
router.register(r'post', PostViewSet)
router.register(r'writer', AuthorViewSet)
