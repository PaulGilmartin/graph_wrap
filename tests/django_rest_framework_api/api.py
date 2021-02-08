from __future__ import unicode_literals

from rest_framework import serializers, viewsets

from tests.models import Author, Post


# Attach a user to this serializer with

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         exclude = ('password',)


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Author
        fields = ['name', 'age', 'active', 'profile_picture']


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        depth = 1  # set to depth =2 gives name collision on schema
        fields = [
            'content', 'author', 'date', 'rating', 'files']


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


"""

print(self.schema)
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
  profile_picture: String  # correct as author_type doesn't have a depth or use custom
}

type post_type {
  content: String!
  author: nested_author_type!
  date: String!
  rating: Decimal
  files: [nested_media_type]!  # correct to generate nested as depth has been set
}
type nested_author_type {
  id: Int!
  name: String!
  age: Int
  active: Boolean!
  profile_picture: String  # correct since this comes from the nested author in post, which only has depth 1
}
type nested_media_type {
  id: Int!
  name: String!
  content_type: String!
  size: Int!
}

"""