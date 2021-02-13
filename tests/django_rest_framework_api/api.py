from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework import serializers, viewsets

from tests.models import Author, Post


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password',)


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Author
        fields = [
            'name',
            'age',
            'active',
            'profile_picture',
            'user',
        ]


class PostSerializer(serializers.ModelSerializer):
    author = AuthorSerializer()

    class Meta:
        model = Post
        depth = 3
        fields = [
            'content',
            'author',
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
schema {
  query: Query
}
scalar Decimal
type Query {
  author(id: Int!): author_type
  all_authors: [author_type]
  post(id: Int!): post_type
  all_posts: [post_type]
}
type author_type {
  name: String!
  age: Int
  active: Boolean!
  profile_picture: String
  # this is wrong. DRF gives the whole representation when we use a custom serializer.
  user: String!
}
type post_type {
  content: String!
  author: String!
  date: String!
  rating: Decimal
  files: [post__files_type]!
}
type post__files_type {
  id: Int!
  name: String!
  content_type: String!
  size: Int!
}

type author__user_type {
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

type post__author_type {
  name: String!
  age: Int
  active: Boolean!
  profile_picture: String
  user: String!
}


"""