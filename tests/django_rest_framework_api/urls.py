from rest_framework import routers

from tests.django_rest_framework_api.api import (
    AuthorViewSet, PostViewSet, MediaViewSet)

router = routers.SimpleRouter()
router.register(r'post', PostViewSet)
router.register(r'media', MediaViewSet)
router.register(r'writer', AuthorViewSet)
