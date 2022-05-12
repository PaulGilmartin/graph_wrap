from __future__ import unicode_literals

from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets, filters

from tests.models import Author, Post, Media


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password',)


class WrittenBySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='get_name')

    class Meta:
        model = Author
        fields = ['name']


class PostSerializer(serializers.ModelSerializer):
    written_by = WrittenBySerializer(source='author')
    author = serializers.HyperlinkedRelatedField(
        view_name='author-detail',
        read_only=True
    )
    files = MediaSerializer(allow_null=True, many=True)

    class Meta:
        model = Post
        depth = 3
        fields = [
            'written_by',
            'author',
            'content',
            'author',
            'date',
            'rating',
            'files',
        ]


class AuthorSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    entries = serializers.ListSerializer(
         child=PostSerializer(source='entries'))
    amount_of_entries = serializers.SerializerMethodField()
    name = serializers.CharField(source='get_name')
    colours = serializers.ListField(
        child=serializers.CharField(), default=['blue', 'green'])

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
            'colours',
            'id',
        ]

    def get_amount_of_entries(self, obj):
        return obj.entries.count()


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'age', 'entries__content']
    filterset_fields = ['name', 'entries__content', 'entries__files__size']


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['author__name', 'content']
    filterset_fields = ['author__name', 'content']


class MediaViewSet(viewsets.ModelViewSet):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'content_type', 'size']
    filterset_fields = ['name', 'content_type', 'size']
