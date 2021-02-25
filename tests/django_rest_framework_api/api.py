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
    #amount_of_entries = serializers.SerializerMethodField()
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
        ]



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

    def dispatch(self, request, *args, **kwargs):
        return super(AuthorViewSet, self).dispatch(request, *args, **kwargs)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


"""
When we have a depth set, *depth does not apply to any custom serializers on nested representations*.
e.g. In below a GET to /post, which has depth 3, would only give an 'id' for profile_picture.
This is because the author = AuthorSerializer() stops the NestedSerializer. If we removed that,
we'd geet the full rep of profile_picture

class AuthorSerializer(serializers.ModelSerializer):
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



Expected:

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
  profile_picture: String  # since depth=0, this is only a pk (or a URI)
  user: user_type!  # since from custom serializer, don't use nested syntax
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

type post_type {
  content: String!
  written_by: author_type!
  date: String!
  rating: Decimal
  files: [post__files_type]  # only one not working as we have [post__files_type]!

}
type post__files_type {
  id: Int!
  name: String!
  content_type: String!
  size: Int!
}

"""