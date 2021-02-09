from __future__ import unicode_literals

import datetime
import json

from django.contrib.auth.models import User
from graphql import GraphQLScalarType, GraphQLNonNull
from tastypie.test import ResourceTestCaseMixin

from django.test import TransactionTestCase

from graph_wrap.django_rest_framework.schema_factory import SchemaFactory
from tests.models import Author, Post, Media


class TestGraphWrapBase(ResourceTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestGraphWrapBase, self).setUp()
        self.graphql_endpoint = '/django_rest/graphql/'
        self.picture = Media.objects.create(
            name='elephant',
            content_type='jpg',
            size=50,
        )
        self.second_picture = Media.objects.create(
            name='giraffe',
            content_type='jpg',
            size=60,
        )
        paul_user = User.objects.create(password='1234', username='Paul')
        self.paul = Author.objects.create(
            name='Paul', age='30', user=paul_user)
        self.pauls_first_post = Post.objects.create(
            content='My first post!',
            author=self.paul,
            date=datetime.datetime.now(),
            rating=u'7.00',
        )
        self.pauls_first_post.files.add(self.picture)
        self.pauls_first_post.files.add(self.second_picture)
        self.pauls_first_post.save()

        scott_user = User.objects.create(password='1234', username='Scott')
        self.scott = Author.objects.create(
            name='Scott', age='28', user=scott_user)


class TestSchemaFactory(TestGraphWrapBase):
    """
    Next things to consider:
    1. More assertions on the current API.
    2. More testing with custom serialiazers?
    3. Test using custom serializers as fields (both which are views and not)
    4. Get required/non-null correct
    5. Custom 'dehyration' methods
    6. Test all field types (scalar + non-scalar)
    7. Integration test on localhost
    """
    def setUp(self):
        super(TestSchemaFactory, self).setUp()
        self.schema = SchemaFactory.create_from_api()
        self.query = self.schema.get_query_type()
        self.type_map = self.schema.get_type_map()

    def test_query_fields(self):
        self.assertEqual(
            {'author', 'all_authors', 'post', 'all_posts'},
            set(self.query.fields),
        )

    def test_author_type(self):
        author_type = self.type_map['author_type']
        self.assertEqual(
            {'name', 'age', 'active', 'profile_picture', 'user'},
            set(author_type.fields),
        )
        age_field = author_type.fields['age']
        self.assertEqual(
            GraphQLScalarType, age_field.type.__class__)
        active_field = author_type.fields['active']
        self.assertEqual(
            GraphQLNonNull, active_field.type.__class__)

    def test_post_type(self):
        post_type = self.type_map['post_type']
        self.assertEqual(
            {'content', 'date', 'author', 'rating', 'files'},
            set(post_type.fields),
        )


class TestGraphWrapApi(TestGraphWrapBase):
    def test_all_authors_query(self):
        query = '''
            query {
                all_authors {
                    name
                }
            }
            '''
        body = {"query": query}
        request_json = json.dumps(body)
        response = self.client.post(
            self.graphql_endpoint,
            request_json,
            content_type="application/json",
        )
        self.assertHttpOK(response)
        all_authors_data = json.loads(
            response.content)['data']['all_authors']
        self.assertEqual(
            [{'name': 'Paul'}, {'name': 'Scott'}],
            all_authors_data,
        )

    def test_all_posts_query(self):
        query = '''
            query {
                all_posts {
                    content
                    author {
                        name
                    }
                }
            }
            '''
        body = {"query": query}
        request_json = json.dumps(body)
        response = self.client.post(
            self.graphql_endpoint,
            request_json,
            content_type="application/json",
        )
        self.assertHttpOK(response)
        all_authors_data = json.loads(
            response.content)['data']['all_authors']
        self.assertEqual(
            [{'name': 'Paul'}, {'name': 'Scott'}],
            all_authors_data,
        )

    def test_get_rest_api(self):
        response = self.client.get(
            '/django_rest/post/',
            content_type="application/json",
        )
        self.assertHttpOK(response)
