from __future__ import unicode_literals

import graphene
from django.conf import settings
from graphene_django.settings import perform_import
from tastypie.resources import ModelResource

from graph_wrap.shared.schema_factory import get_query_attributes
from .query_resolver import (
    AllItemsQueryResolver,
    SingleItemQueryResolver,
)
from .api_transformer import transform_api


class SchemaFactory(object):
    """Factory class for creating a graphene Schema object.

    Given a list of tastypie resources, this object
    has the functionality to produce a graphene Schema object.
    This is achieved by collecting, for each resource,
    the graphene ObjectType produced by transforming that resource
    and also the relevant root Query data for that ObjectType
    (mounted field and field resolver). This data is then used
    to dynamically build a graphene Query class, which is
    passed into a Schema as usual.

    Note: currently only resources which inherit from
    tastypie.resources.ModelResource can be used. Any
    resource which does not satisfy this condition will
    be silently filtered.
    """
    api_class_to_schema = dict()

    def __init__(self, apis):
        self._apis = apis

    @classmethod
    def create_from_api(cls):
        # change name. Maybe make this whole class into a function?
        """
        Create a schema from the tastypie API instance.

        Can pass either the full python path of the API
        instance or an Api instance itself.
        """
        api = perform_import(settings.TASTYPIE_API_PATH, '')
        resources = api._registry.values()
        return cls(resources).create()

    def create(self):
        query_class_attrs = dict()
        for resource in self._usable_apis():
            graphene_type = transform_api(resource)
            query_attributes = get_query_attributes(
                resource,
                resource._meta.resource_name,
                graphene_type,
                SingleItemQueryResolver,
                AllItemsQueryResolver,
                orm_filters=graphene.String(name='orm_filters'),
            )
            query_class_attrs.update(**query_attributes)
            self.api_class_to_schema[resource.__class__] = (
                graphene_type)
        Query = type(str('Query'), (graphene.ObjectType,), query_class_attrs)
        return graphene.Schema(query=Query)

    def _usable_apis(self):
        return [
            resource for resource in self._apis if
            issubclass(resource.__class__, ModelResource)
        ]

