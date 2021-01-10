from __future__ import unicode_literals

import datetime
import json

from tastypie.test import ResourceTestCaseMixin

from django.test import TransactionTestCase

from tests.models import Author, Post, Media


class TestApi(ResourceTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super(TestApi, self).setUp()
        self.graphql_endpoint = '/graphql/'
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