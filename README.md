# GraphWrap #

GraphWrap is a python library which, by adding only two lines of code to your django project, can extend an existing
[Django Rest Framework](https://www.django-rest-framework.org/) (or [Tastypie](https://django-tastypie.readthedocs.io/en/latest/))
API with a [GraphQL](https://graphql.org/learn/) interface.
This is achieved by leveraging [Graphene-Django](https://docs.graphene-python.org/projects/django/en/latest/) to dynamically 
build, at runtime, a GraphQL ObjectType for each Django REST (or tastypie) view in your API. These ObjectTypes are then glued together to
form a GraphQL schema which has the same "shape" as your existing REST API. 
Note that GraphWrap is **not** designed to build a GraphQL schema to replace your existing REST API,
but rather extend it to offer an additional [fully compliant](http://spec.graphql.org/June2018/#sec-Root-Operation-Types)
GraphQL-queryable interface.

## Highlights:

* The dynamic nature of the build of the GraphQL layer means that you can continue to develop your existing
REST based API and know that the graphql schema will be kept up-to-date automatically. 

* Since the graphql layer is using the REST API under-the-hood, you can be sure that important things
like **serialization**, **authentication**, **authorization** and **filtering** will be consistent between your REST view
and the corresponding GraphQL type.
 
* No longer need to worry about overexposing nested views - the client can simply
  make use of the GraphQL layer to retrieve data they want from nested views. This can lead to significant performance boosts
  in certain circumstances (One of the advantages of GraphQL queries is that they solve the [n+1 problem](
  https://itnext.io/what-is-the-n-1-problem-in-graphql-dd4921cb3c1a) which occurs with traditional REST-based APIs).
 


## Limitations

Here are a couple of limitations of the GraphQL API produced by GraphWrap:

* It can only accept GraphQL [queries](https://graphql.org/learn/queries/) - mutations and subscriptions
  are not (yet) supported.

* The schema is built only from Django REST Framework views which inherit from `ModelViewSet`
 (or `ReadOnlyModelViewSet`) and which are registered via a router which inherits from [SimpleRouter](
 https://www.django-rest-framework.org/api-guide/routers/#simplerouter). Alternatively, if you're
 using tastypie, the schema is only built from resources inheriting from `ModelResource`.
  
* Any custom serializer fields which don't inherit from one of the [standard DRF serializer fields](
https://www.django-rest-framework.org/api-guide/fields/) will be mapped to a graphene GenericScalar.

* Works only for JSON serialization.

# GraphWrap for the Django REST Framework

## Quick start

### Core Requirements
Before using this library, you must be using Python 3.6 (or later) and have the following installed:

1. `Django >=2.2`
2. `djangorestframework>=3.0.0`


### Installing

`pip install graph_wrap`


### Exposing the /graphql endpoint

GraphWrap exposes the GraphQL schema via a Django view `graphql_view`. This view builds and exposes a GraphQL
queryable schema via a POST request to a `/graphql` endpoint. The code snippet below demonstrates by example
how you can transform your DRF RES-API into a GraphQL schema by adding just two lines of code to your project:

```
from rest_framework import routers

from graph_wrap.django_rest_framework.graphql_view import graphql_view  # Addition 1: import the graphql_view
from tests.django_rest_framework_api.api import (
    AuthorViewSet, PostViewSet)


router = routers.SimpleRouter()
router.register(r'author', AuthorViewSet)
router.register(r'post', PostViewSet)


urlpatterns = [
    path(r'', include(api.urls)),
    path(r'/graphql/', view=graphql_view), # Addition 2: Register the view under the URL /graphl.
]

```


## Documentation (by Example)

In this section we give a brief overview of how to use GraphWrap via examining
a simple concrete example. 


### Set-up
Suppose we have the following basic django models and corresponding DRF serializers and viewsets (
a fully executable version of this example can be found in graph_wrap.tests):

```
from django.contrib.auth.models import User
from django.db import models


class Media(models.Model):
    name = models.TextField()
    content_type = models.TextField(null=True)
    size = models.BigIntegerField(null=True)


class Author(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    name = models.TextField()
    age = models.IntegerField(null=True)
    active = models.BooleanField(default=True)
    profile_picture = models.ForeignKey(
        Media, null=True, on_delete=models.PROTECT)

    def get_name(self):
        # Use to test custom additional serialization
        return self.name.upper()


class Post(models.Model):
    content = models.TextField()
    date = models.DateTimeField()
    author = models.ForeignKey(
        Author, null=True, on_delete=models.SET_NULL, related_name='entries')
    files = models.ManyToManyField('Media')
    rating = models.DecimalField(null=True, decimal_places=20, max_digits=40)


# api.py

from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets, filters

from tests.models import Author, Post


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('password',)


class AuthorSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    entries = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Post.objects.all())
    amount_of_entries = serializers.SerializerMethodField()
    name = serializers.CharField(source='get_name')

    class Meta:
        model = Author
        fields = ['name', 'age', 'active', 'profile_picture',
         'user', 'entries', 'amount_of_entries']

    def get_amount_of_entries(self, obj):
        return obj.entries.count()


class WrittenBySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='get_name')

    class Meta:
        model = Author
        fields = ['name']


class PostSerializer(serializers.ModelSerializer):
    written_by = WrittenBySerializer(source='author')

    class Meta:
        model = Post
        depth = 3
        fields = ['content', 'written_by', 'date', 'rating', 'files']
       

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['content', 'author__name']
    filterset_fields = ['author__name', 'content']

```

If we wish to layer our REST resources with a GraphQL interface, we can follow the instructions above in the
"Quickstart" guide where we import the `graphql_view` and expose it via the `/graphql` url:


### Understanding the Schema
With these simple changes, we can now query the  `/graphql` endpoint with GraphQL queries. The structure
queries can take, as with all GraphQL APIs, is dictated by the shape of the underlying schema (which, in this case, is
dictated by the shape of the tastypie API). To see what the schema looks like, run the following:

```
>>> from graph_wrap.django_rest_framework import schema
>>> schema = schema()
>>> print(schema)


schema {
  query: Query
}
type Query {
  author(id: Int!): author_type
  all_authors(orm_filters: String): [author_type]
  post(id: Int!): post_type
  all_posts(orm_filters: String): [post_type]
  media(id: Int!): media_type
  all_medias(orm_filters: String): [media_type]
}
type author_type {
  resource_uri: String!
  posts: [post_type]!
  id: Int!
  name: String!
  age: String!
}
type media_type {
  resource_uri: String!
  id: Int!
  name: String!
  content_type: String!
  size: Int!
}
type post_type {
  resource_uri: String!
  author: author_type
  files: [media_type]!
  date: String!
  id: Int!
  content: String!
}

```

Important points to note about the schema produced by GraphWrap:

* **snake_case**: As can be seen above, GraphWrap produces a schema in the `snake_case` convention. Whilst
  this is generally not favoured in GraphQL circles, it was chosen here as it would likely be more consistent with
  the field names on the underlying REST resources (which would use most often use the PEP8 recommended snake 
  case convention).
  
* **Root Query field names**: For each REST model-resource, GraphWrap adds to the Query type precisely
  two fields - one corresponding to the data accessible via a GET request to the 'list' endpoint of the
  resource, and one corresponding to the data accessible via a GET request to the 'detail' endpoint of the
  resource. If we take our AuthorResource as an example:
    * the 'list' endpoint corresponds to the url `/author`. This maps to the `all_authors` field on the Query type.
    * the 'detail' endpoint corresponds to urls of the form '/author/{author_pk}'. This maps to the `author(id: Int!)`
      field on the Query type (where, in the usual GraphQL schema syntax, `(id: Int!)` indicates that an integer author
      id must be supplied.)
      
* **ObjectType and ObjectType Field names**: 
    * GraphWrap maps each model-resource maps to a GraphQL
      ObjectType. The name of the resultant ObjectType can be found by appending `_type` to the name of the
      corresponding resource. For example, the `AuthorResource`, which has name `author`, maps to the `author_type`
      GraphQL ObjectType. 
    * The names of the fields on each ObjectType match those of the names of the fields on the corresponding
      resource.
      
* **Filtering (`orm_filters`)**: Notice in the schema above that each `all_` field can be queried with an optional 
    `orm_filters` argument. This is the GraphQL equivalent of the ORM filtering offered by tastypie on list endpoints.
    If we take our AuthorResource as an example (which has been defined with 
    `filtering = {'age': ('exact',), 'name': ('exact',)})`, then the REST GET query `/author/?name=Paul` can be achieved
    via a POST request to `/graphql` with the following query:
    
    ```
    {
      all_authors(orm_filters: "name=Paul") {
        name
      }
    }
    ```
   
   
### Authentication and Authorization of GraphQLResource

The authentication/authorization applied 
when querying `/graphql` is the authentication/authorization defined on the resource corresponding to the root field 
of the query applied. This is consistent with the way tastypie handles authenticaiton/authorization.
So, for example, the following query would invoke whatever authentication/authorization
was defined on the `AuthorResource`:

``` 
    {
      all_authors(orm_filters: "name=Paul") {
        name
      }
    }
```


  
   
## Making Queries: REST vs GraphQL

In this section we'll look at how various REST GET requests can be mapped to queries for the ``/graphql``
endpoint. Again, we'll do this via examining our explicit concrete example (note that the queries
and requests pictured in this section were produced on the [Insomnia](https://insomnia.rest/)
HTTP client, which has a integration with GraphQL):



### 'list' endpoint requests

* REST:

![](https://raw.githubusercontent.com/PaulGilmartin/graph_wrap/master/tests/images/rest_author_list.png)


* GraphQL

![](https://raw.githubusercontent.com/PaulGilmartin/graph_wrap/master/tests/images/graphql_all_authors.png)



### 'detail' endpoint requests

* REST

![](https://raw.githubusercontent.com/PaulGilmartin/graph_wrap/master/tests/images/rest_author_detail.png)


* GraphQL

![](https://raw.githubusercontent.com/PaulGilmartin/graph_wrap/master/tests/images/graphql_author_single.png)



### Filtering

* REST

![](https://raw.githubusercontent.com/PaulGilmartin/graph_wrap/master/tests/images/rest_author_orm.png)


* GraphQL

![](https://raw.githubusercontent.com/PaulGilmartin/graph_wrap/master/tests/images/test_img.png)


### Some fancier GraphQL query examples - see GraphQL [queries](https://graphql.org/learn/queries/) for more

* Nesting

![](https://raw.githubusercontent.com/PaulGilmartin/graph_wrap/master/tests/images/graphql_all_authors_nested.png)


* Fragments

![](https://raw.githubusercontent.com/PaulGilmartin/graph_wrap/master/tests/images/graphql_fragments.png)




## Quick start


### Core Requirements
Before using this library, the following requirements must be met:

1. Your project is using `Python >= 3.6` and ` Django >=2.2`.
2. Either one of the following packages already installed: `djangorestframework>=3.0.0` or `django-tastypie>=0.14.0`.


### Installing

`pip install graph_wrap`


### Registering the GraphQL resource

GraphWrap exposes the GraphQL schema via a tastypie resource `GraphQLResource` (which is effectively a Django class-based view).
As with all resources, we are required to register `GraphQLResource` with the tastypie Api instance
before we can interact with it via HTTP requests. Once registered, `GraphQLResource` builds and exposes a GraphQL
queryable schema via the `/graphql` endpoint.

```
# tests.urls.py
from graph_wrap import GraphQLResource  # add this line to your project

api = Api('v1')
api.register(GraphQLResource()) # add this line to your project

urlpatterns = [
    path(r'', include(api.urls)),
    ...
]

```

### Querying the GraphQL resource

As mentioned above, GraphWrap exposes the GraphQL API via the `/graphql` URL. 

### Settings

In order for GraphQL to be able to build the GraphQL schema from the tastypie Api instance, it needs
to know where that instance lives in your project. To allow GraphWrap to locate the Api instance, we can simply
add the full path of the instance to our django settings module. For example:

```
# tests.settings.py

TASTYPIE_API_PATH = 'tests.urls.api'
```


## Documentation (by Example)

In this section we give a brief overview of how to use GraphWrap via examining
a simple concrete example. 


### Set-up
Suppose we have the following basic django models and corresponding tastypie resources (
a fully executable version of this example can be found in graph_wrap.tests):

```
# models.py

class Author(models.Model):
    name = models.TextField()
    age = models.TextField()


class Post(models.Model):
    content = models.TextField()
    date = models.DateTimeField()
    author = models.ForeignKey(Author, null=True, on_delete=models.SET_NULL)
    files = models.ManyToManyField('Media')


class Media(models.Model):
    name = models.TextField()
    content_type = models.TextField()
    size = models.BigIntegerField()


# api.py

class AuthorResource(ModelResource):
    posts = fields.ManyToManyField('tests.api.PostResource', attribute='post_set')

    class Meta:
        queryset = Author.objects.all()
        resource_name = 'author'
        filtering = {
            'age': ('exact',),
            'name': ('exact',),
        }


class PostResource(ModelResource):
    author = fields.ForeignKey(AuthorResource, attribute='author', null=True)
    files = fields.ManyToManyField('tests.api.MediaResource', attribute='files')
    date = fields.DateTimeField('date')

    class Meta:
        queryset = Post.objects.all()
        resource_name = 'post'


class MediaResource(ModelResource):
    class Meta:
        queryset = Media.objects.all()
        resource_name = 'media'
```

If we wish to layer our REST resources with a GraphQL interface, we can follow the instructions above in the
"Quickstart" guide. Start by registering our GraphQLResource with the tastypie Api instance:

```
# urls.py

from django.contrib import admin
from django.urls import path, include
from tastypie.api import Api

from graph_wrap import GraphQLResource
from tests.api import AuthorResource, PostResource, MediaResource


api = Api('v1')
api.register(AuthorResource())
api.register(PostResource())
api.register(MediaResource())
api.register(GraphQLResource())

urlpatterns = [
    path(r'', include(api.urls)),
    path('admin/', admin.site.urls),
]
```

Next, add the `TASTYPIE_API_PATH` to the django settings module so GraphWrap can locate the tastypie Api:

```
TASTYPIE_API_PATH = 'tests.urls.api'
```

### Understanding the Schema
With these simple changes, we can now query the  `/grahql` endpoint with GraphQL queries. The structure
queries can take, as with all GraphQL APIs, is dictated by the shape of the underlying schema (which, in this case, is
dictated by the shape of the tastypie API). To see what the schema looks like, run the following:

```
>>> from graph_wrap import schema
>>> schema = schema()
>>> print(schema)


schema {
  query: Query
}
type Query {
  author(id: Int!): author_type
  all_authors(orm_filters: String): [author_type]
  post(id: Int!): post_type
  all_posts(orm_filters: String): [post_type]
  media(id: Int!): media_type
  all_medias(orm_filters: String): [media_type]
}
type author_type {
  resource_uri: String!
  posts: [post_type]!
  id: Int!
  name: String!
  age: String!
}
type media_type {
  resource_uri: String!
  id: Int!
  name: String!
  content_type: String!
  size: Int!
}
type post_type {
  resource_uri: String!
  author: author_type
  files: [media_type]!
  date: String!
  id: Int!
  content: String!
}

```

Important points to note about the schema produced by GraphWrap:

* **snake_case**: As can be seen above, GraphWrap produces a schema in the `snake_case` convention. Whilst
  this is generally not favoured in GraphQL circles, it was chosen here as it would likely be more consistent with
  the field names on the underlying REST resources (which would use most often use the PEP8 recommended snake 
  case convention).
  
* **Root Query field names**: For each REST model-resource, GraphWrap adds to the Query type precisely
  two fields - one corresponding to the data accessible via a GET request to the 'list' endpoint of the
  resource, and one corresponding to the data accessible via a GET request to the 'detail' endpoint of the
  resource. If we take our AuthorResource as an example:
    * the 'list' endpoint corresponds to the url `/author`. This maps to the `all_authors` field on the Query type.
    * the 'detail' endpoint corresponds to urls of the form '/author/{author_pk}'. This maps to the `author(id: Int!)`
      field on the Query type (where, in the usual GraphQL schema syntax, `(id: Int!)` indicates that an integer author
      id must be supplied.)
      
* **ObjectType and ObjectType Field names**: 
    * GraphWrap maps each model-resource maps to a GraphQL
      ObjectType. The name of the resultant ObjectType can be found by appending `_type` to the name of the
      corresponding resource. For example, the `AuthorResource`, which has name `author`, maps to the `author_type`
      GraphQL ObjectType. 
    * The names of the fields on each ObjectType match those of the names of the fields on the corresponding
      resource.
      
* **Filtering (`orm_filters`)**: Notice in the schema above that each `all_` field can be queried with an optional 
    `orm_filters` argument. This is the GraphQL equivalent of the ORM filtering offered by tastypie on list endpoints.
    If we take our AuthorResource as an example (which has been defined with 
    `filtering = {'age': ('exact',), 'name': ('exact',)})`, then the REST GET query `/author/?name=Paul` can be achieved
    via a POST request to `/graphql` with the following query:
    
    ```
    {
      all_authors(orm_filters: "name=Paul") {
        name
      }
    }
    ```
   
   
### Authentication and Authorization of GraphQLResource

The authentication/authorization applied 
when querying `/graphql` is the authentication/authorization defined on the resource corresponding to the root field 
of the query applied. This is consistent with the way tastypie handles authenticaiton/authorization.
So, for example, the following query would invoke whatever authentication/authorization
was defined on the `AuthorResource`:

``` 
    {
      all_authors(orm_filters: "name=Paul") {
        name
      }
    }
```
