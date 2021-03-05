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


"""
print(schema)
schema {
  query: Query
}
type Query {
  author(id: Int!): author_type
  all_authors: [author_type]
  post(id: Int!): post_type
  all_posts: [post_type]
}

type post_type {
  content: String!
  written_by: author_type!
  date: String!
  rating: String
  files: [post__files_type]!  # should be nullable
}

type post__files_type {
  id: Int!
  name: String!
  content_type: String
  size: Int
}
type author_type {
  name: String!
  age: Int
  active: Boolean!
  profile_picture: String
  user: user_type!
  entries: [String]! # should this be null?
  amount_of_entries: GenericScalar!
}
type user_type {
  id: Int!
  last_login: String
  is_superuser: Boolean!
  username: String!
  first_name: String!
  last_name: String!
  email: String!
  is_staff: Boolean!
  is_active: Boolean!
  date_joined: String!
  groups: [String]!
  user_permissions: [String]!
}

scalar GenericScalar




"""