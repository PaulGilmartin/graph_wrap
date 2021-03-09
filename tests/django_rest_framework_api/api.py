from __future__ import unicode_literals

from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets, filters

from tests.models import Author, Post


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'is_staff']


class AuthorSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    entries = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Post.objects.all())

    class Meta:
        model = Author
        fields = ['name', 'age', 'active', 'profile_picture', 'user', 'entries']


class PostSerializer(serializers.ModelSerializer):
    written_by = serializers.HyperlinkedRelatedField(
        view_name='author-detail', read_only=True)

    class Meta:
        model = Post
        depth = 3
        fields = ['written_by', 'content', 'date', 'files', 'rating']


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['content', 'author__name']
    filterset_fields = ['author__name', 'content']
