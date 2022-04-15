from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework import serializers, viewsets, filters

from tests.models import Author, Post


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


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = [filters.SearchFilter]  #, DjangoFilterBackend]
    search_fields = ['content', 'author__name']
    filterset_fields = ['author__name', 'content']
