from __future__ import unicode_literals

from rest_framework.filters import SearchFilter
from rest_framework.schemas.generators import EndpointEnumerator
from rest_framework.schemas.generators import BaseSchemaGenerator
import graphene
from rest_framework import viewsets
from rest_framework.settings import api_settings

from graph_wrap.shared.schema_factory import get_query_attributes
from .query_resolver import (
    AllItemsQueryResolver,
    SingleItemQueryResolver,
)
from .api_transformer import ApiTransformer


class SchemaFactory(object):
    def __init__(self, apis):
        self._apis = apis

    @classmethod
    def create_from_api(cls):
        api_endpoints = EndpointEnumerator().get_api_endpoints()
        generator = BaseSchemaGenerator()
        views = []
        for endpoint in api_endpoints:
            _, method, view_callback = endpoint
            view = generator.create_view(view_callback, method)
            if cls._usable_viewset(view):
                if view.__class__ not in [v.__class__ for v in views]:
                    views.append(view)
        return cls(views).create()

    @staticmethod
    def _usable_viewset(viewset):
        # Can we relax this condition at all?
        return isinstance(
            viewset, (viewsets.ModelViewSet, viewsets.ReadOnlyModelViewSet))

    def create(self):
        query_class_attrs = dict()
        type_mapping = dict()
        non_root_types = []
        for api in self._apis:
            api_transformer = ApiTransformer(api, type_mapping=type_mapping)
            root_type = api_transformer.root_type()
            filter_args = self._get_filter_args(api)
            query_attributes = get_query_attributes(
                api,
                api.basename,
                root_type,
                SingleItemQueryResolver,
                AllItemsQueryResolver,
                **filter_args
            )
            query_class_attrs.update(**query_attributes)
            non_root_types.extend(api_transformer.non_root_types())
            type_mapping = api_transformer.type_mapping
        Query = type(str('Query'), (graphene.ObjectType,), query_class_attrs)
        schema = graphene.Schema(query=Query, types=non_root_types)
        return schema

    def _get_filter_args(self, api):
        filter_args = {}
        filter_backends = api.filter_backends
        for filt in filter_backends:
            if issubclass(filt, SearchFilter):
                filter_args[api_settings.SEARCH_PARAM] = graphene.String(
                    name=api_settings.SEARCH_PARAM)
        return filter_args

