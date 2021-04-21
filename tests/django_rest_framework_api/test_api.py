from __future__ import unicode_literals

import datetime
import json

from django.test import TransactionTestCase
from django.contrib.auth.models import User
from graphene.types.definitions import GrapheneObjectType
from graphql import GraphQLScalarType, GraphQLNonNull, GraphQLList

from graph_wrap.django_rest_framework.schema_factory import SchemaFactory
from tests.models import User


class TestGraphWrapBase(TransactionTestCase):
    def setUp(self):
        super(TestGraphWrapBase, self).setUp()
        self.graphql_endpoint = '/django_rest/graphql/'
        paul_user = User.objects.create(first_name='Paul', password='1234', username='Paul')
        scott_user = User.objects.create(first_name='Scott', password='1234', username='Scott')

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


class TestGraphWrapApi(TestGraphWrapBase):
    def test_all_users_query(self):
        query = '''
            query {
                all_users {
                    id,last_name,first_name,father_name
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
        all_users_data = json.loads(
            response.content)['data']['all_users']
        self.assertEqual('Paul', all_users_data[0]['first_name'])
        self.assertEqual('Scott', all_users_data[1]['first_name'])
