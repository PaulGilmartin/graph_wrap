from __future__ import unicode_literals

from rest_framework import serializers, viewsets


from tests.models import Author, Post


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Author
        fields = ['name']

"""
We mighht need to limit to objects which inherit from 
serializers.HyperlinkedModelSerializer. Otherwise we don't have a
view?
"""
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['content', 'author']
        depth=1


class AuthorViewSet(viewsets.ModelViewSet):

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
