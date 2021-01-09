from __future__ import unicode_literals

from rest_framework import serializers, viewsets, views
from tests.models import Author, Post


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Author
        fields = ['name']


class PostSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'date', 'rating', 'author']


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


class GraphQLViewSet(viewsets.ModelViewSet):
    # Probably best just to do this as a regular function view?
    def get_serializer_class(self):
        return None

