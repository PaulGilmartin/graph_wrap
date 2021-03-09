from __future__ import unicode_literals

import datetime
import json

from tastypie.test import ResourceTestCaseMixin

from django.test import TransactionTestCase

from tests.models import Author, Post, Media


class TestApi(ResourceTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestApi, self).setUp()
        self.graphql_endpoint = '/tastypie/v1/graphql/'
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
        self.paul = Author.objects.create(name='Paul', age='30')
        self.pauls_first_post = Post.objects.create(
            content='My first post!',
            author=self.paul,
            date=datetime.datetime.now(),
            rating=u'7.00',
        )
        self.pauls_first_post.files.add(self.picture)
        self.pauls_first_post.files.add(self.second_picture)
        self.pauls_first_post.save()

        self.scott = Author.objects.create(name='Scott', age='28')

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

    def test_all_authors_all_posts_query(self):
        query = '''
            query {
                all_authors {
                    name
                }
                all_posts {
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
        self.assertHttpOK(response)
        all_authors_data = json.loads(
            response.content)['data']['all_authors']
        self.assertEqual(
            [{'name': 'Paul'}, {'name': 'Scott'}],
            all_authors_data,
        )
        all_post_data = json.loads(
            response.content)['data']['all_posts']
        self.assertEqual(
            [{'content': 'My first post!'}],
            all_post_data,
        )

    def test_all_authors_query_with_orm_filters_argument(self):
        query = '''
            query {
                all_authors(orm_filters: "age=28") {
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
            [{'name': 'Scott'}],
            all_authors_data,
        )

    def test_single_author_query(self):
        query = '''
            query {
                author(id: %d) {
                    name
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
        self.assertHttpOK(response)
        author_data = json.loads(response.content)['data']['author']
        self.assertEqual(
            {'name': 'Scott', 'age': 28},
            author_data,
        )

    def test_single_post_query(self):
        query = '''
            query {
                post(id: %d) {
                    date
                    author {
                        name
                    }
                    files {
                        name
                        content_type
                    }
                    rating
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
        self.assertHttpOK(response)
        post_data = json.loads(response.content)['data']['post']
        self.assertIn('date', post_data)
        self.assertEqual(
            {'name': 'Paul'},
            post_data['author'],
        )
        self.assertEqual(
            [{'name': 'elephant', 'content_type': 'jpg'},
             {'name': 'giraffe', 'content_type': 'jpg'}],
            post_data['files'],
        )

    def test_nesting_query(self):
        query = '''
            query {
                author(id: %d) {
                    name
                    posts {
                        content
                        files {
                            content_type
                        }
                    }
                }
            }
            ''' % self.paul.pk
        body = {"query": query}
        request_json = json.dumps(body)
        response = self.client.post(
            self.graphql_endpoint,
            request_json,
            content_type="application/json",
        )
        self.assertHttpOK(response)
        author_data = json.loads(response.content)['data']['author']
        self.assertEqual('Paul', author_data['name'])
        post_data = author_data['posts']
        self.assertEqual(1, len(post_data))
        post = post_data[0]
        self.assertEqual('My first post!', post['content'])
        file_data = post['files']
        self.assertEqual(2, len(file_data))
        self.assertEqual(
            [{'content_type': 'jpg'}, {'content_type': 'jpg'}],
            file_data,
        )

    def test_post_query_with_fragments(self):
        query = '''
            query {
                all_posts {
                    content
                    ...postFragment
                    author {
                        ...authorFragment
                    }
                }
            }
            fragment postFragment on post_type {
                id
                content
            }
            fragment authorFragment on author_type {
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
        self.assertHttpOK(response)
        post_data = json.loads(
            response.content)['data']['all_posts'][0]
        self.assertEqual('My first post!', post_data['content'])
        self.assertEqual({'name': 'Paul'}, post_data['author'])

    def test_query_with_directive(self):
        pass

    def test_rest_endpoint_query(self):
        response = self.client.get(
            '/tastypie/v1/author/{}/'.format(self.paul.pk),
            {},
            content_type="application/json",
        )
        self.assertHttpOK(response)
        posts = json.loads(response.content)['posts']
        self.assertEqual(1, len(posts))
        self.assertEqual(
            '/tastypie/v1/post/{}/'.format(self.pauls_first_post.pk), posts[0])
