from __future__ import unicode_literals

from rest_framework import serializers
from tests.models import Author, Post, Media


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Author
        

class PostSerializer(serializers.HyperlinkedModelSerializer):
    pass


class MediaSerializer(serializers.HyperlinkedModelSerializer):
    pass

