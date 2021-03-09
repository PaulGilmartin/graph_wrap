from __future__ import unicode_literals

import datetime
import json

from django.test import TransactionTestCase
from django.contrib.auth.models import User
from graphene.types.definitions import GrapheneObjectType
from graphql import GraphQLScalarType, GraphQLNonNull, GraphQLList

from graph_wrap.django_rest_framework.schema_factory import SchemaFactory
from tests.models import Author, Post, Media


class TestGraphWrapBase(TransactionTestCase):
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
        profile_picture = Media.objects.create(
            name='paul.jpg')
        self.paul = Author.objects.create(
            name='Paul',
            age='30',
            user=paul_user,
            profile_picture=profile_picture,
        )
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

    def assertFieldType(
            self, graphql_type, field_name, expected_field_type):
        field = graphql_type.fields[field_name]
        self.assertEqual(
            expected_field_type, field.type.__class__)

    def assertFieldTypeOfType(
            self,
            graphql_type,
            field_name,
            expected_field_type_of_type,
    ):
        field = graphql_type.fields[field_name]
        self.assertEqual(
            expected_field_type_of_type, field.type.of_type.__class__)


class TestSchemaFactory(TestGraphWrapBase):
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
            {'name',
             'age',
             'active',
             'profile_picture',
             'user',
             'entries',
             'amount_of_entries',
             },
            set(author_type.fields),
        )
        self.assertFieldType(author_type, 'name', GraphQLNonNull)
        self.assertFieldTypeOfType(author_type, 'name', GraphQLScalarType)

        self.assertFieldType(author_type, 'age', GraphQLScalarType)
        self.assertFieldType(author_type, 'active', GraphQLNonNull)
        self.assertFieldTypeOfType(author_type, 'active', GraphQLScalarType)

        # On author_type, profile_picture is simply a (nullable)
        # resource uri of form /media/{id}. Thus, we expect
        # the profile_picture field type to be GraphQLScalarType.
        self.assertFieldType(
            author_type, 'profile_picture', GraphQLScalarType)
        self.assertFieldType(author_type, 'user', GraphQLNonNull)
        self.assertFieldTypeOfType(author_type, 'user', GrapheneObjectType)

    def test_post_type(self):
        post_type = self.type_map['post_type']
        self.assertEqual(
            {'content', 'date', 'written_by', 'rating', 'files', 'author'},
            set(post_type.fields),
        )
        self.assertFieldType(post_type, 'content', GraphQLNonNull)
        self.assertFieldType(post_type, 'date', GraphQLNonNull)

        self.assertFieldType(post_type, 'written_by', GraphQLNonNull)
        self.assertFieldTypeOfType(post_type, 'written_by', GrapheneObjectType)

        self.assertFieldType(post_type, 'rating', GraphQLScalarType)
        self.assertFieldType(post_type, 'files', GraphQLNonNull)
        self.assertFieldTypeOfType(post_type, 'files', GraphQLList)

        self.assertFieldType(post_type, 'author', GraphQLNonNull)
        self.assertFieldTypeOfType(post_type, 'author', GrapheneObjectType)


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
        self.assertEqual(response.status_code, 200)
        all_authors_data = json.loads(
            response.content)['data']['all_authors']
        self.assertEqual(
            [{'name': 'PAUL'}, {'name': 'SCOTT'}],
            all_authors_data,
        )

    def test_all_posts_query(self):
        query = '''
            query {
                all_posts {
                    content
                    written_by {
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

        self.assertEqual(response.status_code, 200)
        all_posts_data = json.loads(
            response.content)['data']['all_posts']
        self.assertEqual(
            [{'content':  self.pauls_first_post.content,
             'written_by': {'name': 'PAUL'}}],
            all_posts_data,
        )

    def test_all_authors_all_posts_query(self):
        query = '''
            query {
                all_authors {
                    name
                }
                all_posts {
                    content
                    author {
                        name
                        user {
                            username
                        }
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
        self.assertEqual(response.status_code, 200)
        all_authors_data = json.loads(
            response.content)['data']['all_authors']
        self.assertEqual(
            [{'name': 'PAUL'}, {'name': 'SCOTT'}],
            all_authors_data,
        )
        all_post_data = json.loads(
            response.content)['data']['all_posts']
        self.assertEqual(
            [{'content': 'My first post!',
              'author': {'name': 'PAUL', 'user': {'username': 'Paul'}}}],
            all_post_data,
        )

    def test_single_author_query(self):
        query = '''
            query {
                author(id: %d) {
                    name
                    amount_of_entries
                    age
                }
            }
            ''' % self.scott.pk
        body = {"query": query}
        request_json = json.dumps(body)
        response = self.client.post(
            self.graphql_endpoint,
            request_json,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        author_data = json.loads(response.content)['data']['author']
        self.assertEqual(
            {'name': 'SCOTT', 'age': 28, 'amount_of_entries': 0},
            author_data,
        )

    def test_single_author_query_with_m2m(self):
        query = '''
            query {
                post(id: %d) {
                    content
                    files {
                        name
                    }
                }
            }
            ''' % self.pauls_first_post.pk
        body = {"query": query}
        request_json = json.dumps(body)
        response = self.client.post(
            self.graphql_endpoint,
            request_json,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        post_data = json.loads(response.content)['data']['post']
        self.assertEqual(
            {'content': self.pauls_first_post.content,
             'files': [{'name': 'elephant'}, {'name': 'giraffe'}]},
            post_data,
        )

    def test_post_query_with_fragments(self):
        query = '''
            query {
                all_posts {
                    content
                    ...postFragment
                    written_by {
                        ...authorFragment
                    }
                }
            }
            fragment postFragment on post_type {
                content
            }
            fragment authorFragment on author_type_2 {
                name
            }
            '''
        body = {"query": query}
        request_json = json.dumps(body)

        response = self.client.post(
            self.graphql_endpoint,
            request_json,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        post_data = json.loads(
            response.content)['data']['all_posts'][0]
        self.assertEqual('My first post!', post_data['content'])
        self.assertEqual({'name': 'PAUL'}, post_data['written_by'])

    def test_single_post_no_files_query(self):
        pauls_second_post = Post.objects.create(
            content='My Second post!',
            author=self.paul,
            date=datetime.datetime.now(),
            rating=u'7.00',
        )
        query = '''
            query {
                post(id: %d) {
                    content
                    files {
                        content_type
                    }
                    
                }
            }
            ''' % pauls_second_post.pk
        body = {"query": query}
        request_json = json.dumps(body)
        response = self.client.post(
            self.graphql_endpoint,
            request_json,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        post_data = json.loads(response.content)['data']['post']
        self.assertEqual([], post_data['files'])

    def test_query_with_directive(self):
        pass

    def test_all_posts_query_with_search_filters_argument(self):
        Post.objects.create(
            content='Blah',
            author=self.scott,
            date=datetime.datetime.now(),
            rating=u'7.00',
        )
        query = '''
            query {
                all_posts(search: "Paul") {
                    content
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
        self.assertEqual(response.status_code, 200)
        all_authors_data = json.loads(
            response.content)['data']['all_posts']
        self.assertEqual(
            1,
            len(all_authors_data),
        )

    # Requires django_filter package to pass
    # def test_all_posts_query_with_django_filters_argument(self):
    #     Post.objects.create(
    #         content='Blah',
    #         author=self.scott,
    #         date=datetime.datetime.now(),
    #         rating=u'7.00',
    #     )
    #     query = '''
    #         query {
    #             all_posts(orm_filters: "author__name=Paul") {
    #                 content
    #             }
    #         }
    #         '''
    #     body = {"query": query}
    #     request_json = json.dumps(body)
    #     response = self.client.post(
    #         self.graphql_endpoint,
    #         request_json,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     all_authors_data = json.loads(
    #         response.content)['data']['all_posts']
    #     self.assertEqual(
    #         1,
    #         len(all_authors_data),
    #     )

    def test_get_rest_api_with_search_filter(self):
        Post.objects.create(
            content='Blah',
            author=self.scott,
            date=datetime.datetime.now(),
            rating=u'7.00',
        )
        response = self.client.get(
            '/django_rest/post/',
            content_type='application/json',
            data={'search': 'Paul'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()))

    # Requires django_filter package to pass
    # def test_get_rest_api_with_django_filter(self):
    #     Post.objects.create(
    #         content='Blah',
    #         author=self.scott,
    #         date=datetime.datetime.now(),
    #         rating=u'7.00',
    #     )
    #     response = self.client.get(
    #         '/django_rest/post/',
    #         content_type='application/json',
    #         data={'author__name': 'Paul'}
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(1, len(response.json()))

    def test_get_rest_api_detail(self):
        response = self.client.get(
            '/django_rest/writer/{}/'.format(self.paul.pk),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
