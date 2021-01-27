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
    def __init__(self, apis):
        self._apis = apis

    @classmethod
    def create_from_api(cls, api=None):  # remove api arg when tastypie onboarded
        """
        Create a schema from the DRF router instance.

        Can pass either the full python path of the API
        instance or an router instance itself.
        - Shouldnt need this now?
        """
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
                if view.__class__ not in [v.__class__ for v in views]:
                    # Don't add same view for both 'detail' and 'list'
                    # views.
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
        for api in self._apis:
            """
            Here api is a DRF viewset. The related fields might not necessarily
            correspond to views. For such fields, can we build an object type
            which is then *not* part of the Query? 
            These can be added via the optional 'types' argument to 
            graphene.Schema. Open questions:
             - How will we name them? {model}_type might interfere with
               how we name the viewsets?
             - Will the recursive nature of having to define types
               like this mean this gets too slow?
             - How can we actually build them? If the fields are
               NestedSerializer instances then we have something to
               go by. Maybe we can dynamically make them nested by
               adding a depth? Need to be careful to remove that, and
               might not be thread safe?
               See https://stackoverflow.com/questions/9541025/how-to-copy-a-python-class
            
            """
            api_transformer = ApiTransformer(api)
            root_type = api_transformer.root_type()
            query_attributes = QueryAttributes(api, root_type)
            query_class_attrs.update(**query_attributes.to_dict())
            non_root_types = api_transformer.non_root_types()
        Query = type(str('Query'), (graphene.ObjectType,), query_class_attrs)
        schema = graphene.Schema(query=Query, types=non_root_types)
        return schema


class QueryAttributes(object):
    """Create the graphene Query class attributes relevant to a resource."""

    def __init__(self, api, graphene_type):
        self._api = api
        self.graphene_type = graphene_type
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

