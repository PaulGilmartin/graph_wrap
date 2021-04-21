from __future__ import unicode_literals

from tests.models import User
#from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets, filters


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'last_name', 'first_name', 'father_name']


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

