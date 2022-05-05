from __future__ import unicode_literals

from rest_framework.schemas.generators import EndpointEnumerator
from rest_framework.schemas.generators import BaseSchemaGenerator
import graphene
from rest_framework import viewsets

from graph_wrap.shared.schema_factory import get_query_attributes
from .query_resolver import (
    AllItemsQueryResolver,
    SingleItemQueryResolver,
)
from .api_transformer import ApiTransformer


class SchemaFactory:
    def __init__(self, apis):
        self._apis = apis

    @classmethod
    def create_from_api(cls):
        views = cls.usable_views()
        return cls(views).create()

    @classmethod
    def usable_views(cls):
        api_endpoints = EndpointEnumerator().get_api_endpoints()
        generator = BaseSchemaGenerator()
        views = []
        for endpoint in api_endpoints:
            _, method, view_callback = endpoint
            view = generator.create_view(view_callback, method)
            if cls._usable_viewset(view):
                if view.__class__ not in [v.__class__ for v in views]:
                    views.append(view)
        return views

    @staticmethod
    def _usable_viewset(viewset):
        # Can we relax this condition at all?
        return isinstance(
            viewset, (viewsets.ModelViewSet, viewsets.ReadOnlyModelViewSet))

    def create(self):
        query_class_attrs = dict()
        type_mapping = dict()
        non_root_types = []
        seen_nested_serializers = dict()
        for api in self._apis:
            api_transformer = ApiTransformer(
                api,
                type_mapping=type_mapping,
                seen_nested_serializers=seen_nested_serializers,
            )
            root_type = api_transformer.root_type()
            query_attributes = get_query_attributes(
                api,
                api.basename,
                root_type,
                SingleItemQueryResolver,
                AllItemsQueryResolver,
                **api_transformer.api_filters
            )
            query_class_attrs.update(**query_attributes)
            non_root_types.extend(api_transformer.non_root_types())
            type_mapping = api_transformer.type_mapping
            seen_nested_serializers = api_transformer.seen_nested_serializers
        Query = type(str('Query'), (graphene.ObjectType,), query_class_attrs)
        schema = graphene.Schema(query=Query, types=non_root_types)
        return schema

