from rest_framework import routers

from tests.django_rest_framework_api.api import (
    UserViewSet)

router = routers.SimpleRouter()
router.register(r'user', UserViewSet)
