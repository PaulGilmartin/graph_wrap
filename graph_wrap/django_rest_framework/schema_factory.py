from __future__ import unicode_literals

import graphene
from graphene_django.settings import perform_import
from rest_framework import viewsets

from .field_resolvers import (
    AllItemsQueryResolver,
    SingleItemQueryResolver,
)
from .api_transformer import transform_api


class SchemaFactory(object):
    """Factory class for creating a graphene Schema object.

    Given a list of DRF view sets, this object
    has the functionality to produce a graphene Schema object.
    This is achieved by collecting, for each viewset,
    the graphene ObjectType produced by transforming that view set
    and also the relevant root Query data for that ObjectType
    (mounted field and field resolver). This data is then used
    to dynamically build a graphene Query class, which is
    passed into a Schema as usual.

    Note: currently only resources which inherit from
    rest_framework.viewsets.ModelViewSet can be used. Any
    resource which does not satisfy this condition will
    be silently filtered.
    """
    api_class_to_schema = dict()

    def __init__(self, apis):
        self._apis = apis

    @classmethod
    def create_from_api(cls, api):
        """
        Create a schema from the DRF viewset instance.

        Can pass either the full python path of the API
        instance or an Api instance itself.
        """
        from rest_framework.schemas.generators import EndpointEnumerator
        from rest_framework.schemas.generators import BaseSchemaGenerator

        # This should actually eliminate the need to pass
        # in a router at all (and hence define any
        # extra config). Works in background
        # by inspecting the ROOT_URL_CONF setting.
        # We can probably do something similar for tastypie?
        api_endpoints = EndpointEnumerator().get_api_endpoints()
        generator = BaseSchemaGenerator()
        views = []
        for endpoint in api_endpoints:
            _, method, view_callback = endpoint
            view = generator.create_view(view_callback, method)
            if cls._usable_viewset(view):
                views.append(view)
        return cls(views).create()

    @staticmethod
    def _usable_viewset(viewset):
        # Can we relax this condition at all?
        return isinstance(viewset, viewsets.ModelViewSet)

    def create(self):
        query_class_attrs = dict()
        for api in self._apis:
            query_attributes = QueryAttributes(api)
            query_class_attrs.update(**query_attributes.to_dict())
            self.api_class_to_schema[api.__class__] = (
                query_attributes.graphene_type)
        Query = type(str('Query'), (graphene.ObjectType,), query_class_attrs)
        return graphene.Schema(query=Query)


class QueryAttributes(object):
    """Create the graphene Query class attributes relevant to a resource."""

    def __init__(self, api):
        self._api = api
        self.graphene_type = transform_api(api)
        self._single_item_field_name = api.basename
        self._all_items_field_name = 'all_{}s'.format(
            self._single_item_field_name)
        self._single_item_resolver_name = 'resolve_{}'.format(
            self._single_item_field_name)
        self._all_items_resolver_name = 'resolve_{}'.format(
            self._all_items_field_name)

    def to_dict(self):
        return {
            self._single_item_field_name: self._single_item_query_field(),
            self._all_items_field_name: self._all_items_query_field(),
            self._single_item_resolver_name: self._single_item_query_resolver(),
            self._all_items_resolver_name: self._all_items_query_resolver(),
        }

    def _all_items_query_field(self):
        return graphene.List(
            self.graphene_type,
            #orm_filters=graphene.String(name='orm_filters'),
            name=self._all_items_field_name,
        )

    def _all_items_query_resolver(self):
        return AllItemsQueryResolver(
            field_name=self._all_items_field_name,
            api=self._api,
        )

    def _single_item_query_field(self):
        return graphene.Field(
            self.graphene_type,
            id=graphene.Int(required=True),
            name=self._single_item_field_name,
        )

    def _single_item_query_resolver(self):
        return SingleItemQueryResolver(
            field_name=self._single_item_field_name,
            api=self._api,
        )

