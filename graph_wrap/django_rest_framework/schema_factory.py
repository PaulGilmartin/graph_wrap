from __future__ import unicode_literals
from rest_framework.schemas.generators import EndpointEnumerator
from rest_framework.schemas.generators import BaseSchemaGenerator
import graphene
from graphene_django.settings import perform_import
from rest_framework import viewsets

from .field_resolvers import (
    AllItemsQueryResolver,
    SingleItemQueryResolver,
)
from .api_transformer import ApiTransformer


class SchemaFactory(object):
    def __init__(self, apis):
        self._apis = apis

    @classmethod
    def create_from_api(cls, api=None):  # remove api arg when tastypie onboarded
        api_endpoints = EndpointEnumerator().get_api_endpoints()
        generator = BaseSchemaGenerator()
        views = []
        for endpoint in api_endpoints:
            _, method, view_callback = endpoint
            view = generator.create_view(view_callback, method)

            if cls._usable_viewset(view):
                if view.__class__ not in [v.__class__ for v in views]:
                    for method, action in view.action_map.items():
                        # We might not need to bother setting actions?
                        if method == 'get':
                            handler = getattr(view, action)
                            setattr(view, method, handler)
                            if cls._usable_viewset(view):
                                views.append(view)
        return cls(views).create()

    @staticmethod
    def _usable_viewset(viewset):
        # Can we relax this condition at all?
        return isinstance(viewset, viewsets.ModelViewSet)

    def create(self):
        query_class_attrs = dict()
        type_mapping = dict()
        non_root_types = []
        for api in self._apis:
            api_transformer = ApiTransformer(api, type_mapping=type_mapping)
            root_type = api_transformer.root_type()
            query_attributes = get_query_attributes(api, root_type)
            query_class_attrs.update(**query_attributes)
            non_root_types.extend(api_transformer.non_root_types())
            type_mapping = api_transformer.type_mapping
        Query = type(str('Query'), (graphene.ObjectType,), query_class_attrs)
        schema = graphene.Schema(query=Query, types=non_root_types)
        return schema


def get_query_attributes(api, graphene_type):
    single_item_field_name = api.basename
    all_items_field_name = 'all_{}s'.format(single_item_field_name)
    single_item_resolver_name = 'resolve_{}'.format(single_item_field_name)
    all_items_resolver_name = 'resolve_{}'.format(all_items_field_name)
    return {
        single_item_field_name: graphene.Field(
            graphene_type,
            id=graphene.Int(required=True),
            name=single_item_field_name,
        ),
        all_items_field_name: graphene.List(
            graphene_type, name=all_items_field_name),
        single_item_resolver_name: SingleItemQueryResolver(
            field_name=single_item_field_name, api=api),
        all_items_resolver_name: AllItemsQueryResolver(
            field_name=all_items_field_name, api=api),
    }
