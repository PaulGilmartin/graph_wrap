from __future__ import unicode_literals

from rest_framework import serializers, viewsets


from tests.models import Author, Post


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Author
        fields = ['name']
        depth = 1


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['content', 'author']

"""
PostSerializer(context={'request': None, 'format': None, 'view': <tests.django_rest_framework_api.api.PostViewSet object>}):
    content = CharField(style={'base_template': 'textarea.html'})
    author = NestedSerializer(read_only=True):
        id = IntegerField(label='ID', read_only=True)
        name = CharField(style={'base_template': 'textarea.html'})
        age = CharField(style={'base_template': 'textarea.html'})


"""


class AuthorViewSet(viewsets.ModelViewSet):

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


"""
>>> from graph_wrap import schema
>>> schema = schema()
>>> print(schema)


schema {
  query: Query
}
type Query {
  author(id: Int!): author_type
  all_authors: [author_type]   # still to add filters
  post(id: Int!): post_type
  all_posts: [post_type]  # still to add filters
}
type author_type {
  name: String!
}
type post_type {
  author: from_author_model_type   
  #files: [media_type]! - still to add
  date: String!
  id: Int!
  content: String!
}


# This object type is not available directly on the 
# root Query (i.e. there is no REST endpoint
# maps directly to this type). Instead, this object type
# corresponds to the nested serializer DRF would create dynamically
# from the Author model if we had specified a depth >=1 
# on the the parent serializer (PostSerializer in this case).
type from_author_model_type{
  name: String!
  age: String!

}
"""