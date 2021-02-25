from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework import serializers, viewsets

from tests.models import Author, Post


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password',)


class AuthorSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    # Depth does not apply to reverse fields
    entries = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Post.objects.all())
    amount_of_entries = serializers.SerializerMethodField()
    name = serializers.CharField(source='get_name')

    class Meta:
        model = Author
        fields = [
            'name',
            'age',
            'active',
            'profile_picture',
            'user',
            'entries',
            'amount_of_entries',
        ]

    def get_amount_of_entries(self, obj):
        return obj.entries.count()


class PostSerializer(serializers.ModelSerializer):
    written_by = AuthorSerializer(source='author')

    class Meta:
        model = Post
        depth = 3
        fields = [
            'content',
            'written_by',
            'date',
            'rating',
            'files',
        ]


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
