from __future__ import unicode_literals

import copy
from abc import abstractmethod

import json
from tastypie.exceptions import BadRequest

from graph_wrap.graphql_transformer import transform_graphql_resolve_info


class GrapheneFieldResolver(object):
    """Callable which acts as resolver for a graphene field.

    Note: Callable object, and not simply a function, for two
    reasons:
    - To bind field_name to the class namespace on instantiation,
      which is important when dynamically building ObjectType
      resolver methods.
    - More easily extendable.
    """
    def __init__(self, field_name):
        self._field_name = field_name

    @abstractmethod
    def __call__(self, parent, info, **kwargs):
        """Resolves the appropriate field.

        The signature here matches that of a resolver method
        on a graphene ObjectType class.
        """
        pass


class JSONResolver(GrapheneFieldResolver):
    def __call__(self, parent, info, **kwargs):
        """Resolves the appropriate field from the parent JSON.

        Here we can assume that 'parent' is the JSON response
        from a tastypie resource.
        """
        if parent:
            return parent[self._field_name]


class QueryResolver(GrapheneFieldResolver):
    """Callable which acts as resolver for a field on the root Query."""
    def __init__(self, field_name, api):
        super(QueryResolver, self).__init__(field_name)
        self._api = api

    @classmethod
    def rest_api_resolver_method(cls, resource_adapter, **kwargs):
        pass

    def __call__(self, root, info, **kwargs):
        get_request = transform_graphql_resolve_info(
            self._field_name, info, **kwargs)
        selectable_fields_api = _selectable_fields_mutator(
            self._api)
        rest_resolver_method = self.rest_api_resolver_method(
            selectable_fields_api,
            **kwargs
        )
        # consider using threads to dynamically update the class,
        # e.g. simple history?
        """
        What we need:
         - To ensure that we fire get_request at self._api
           such that only the fields defined by selected_fields
           are serialized. This needs to be done recursively,
           ensuring that nested related resources only
           serialize the corresponding nested selected fields.
         - We need to "fire the request" in as close a way as
           possible to traditional DRF - seems like using the
           callback returned by as_view might be the best option.
           
         - We need a way to edit the fields coming from the
           serializer on the viewset. Some options:
           
           1. Dynamically build a super class, S, of self._api.__class__
              which pops the appropriate fields in the __init__ 
              method (using the input request). Then set self._api.serializer_class = S. 
              Pros: 
                - Should be thread safe as setting on self._api (the instance)
                - Code a bit more readable than mutating a method.
              Cons: 
                - Overrides the class so could fail type checks
           2. Mutate _selectable_fields_mutator as below
              
        
        """
        resource_response = rest_resolver_method(get_request)
        if resource_response.status_code in (
                300, 307, 400, 401, 403, 404, 405, 500):
            raise BadRequest(resource_response.content)
        response_json = json.loads(
            resource_response.content or '{}')
        return response_json


class AllItemsQueryResolver(QueryResolver):
    """Callable which acts as resolver for an 'all_items' field' on the Query.

    For example, if we had a ProfileAPI with underlying
    Django model 'Profile', an instance of this class provides
    functionality for the 'resolve_all_profiles' resolver
    on the root Query (analogous to a GET request to the /profile
    list endpoint in REST terms).
    """
    def __call__(self, root, info, **kwargs):
        response_json = super(AllItemsQueryResolver, self).__call__(
            root, info, **kwargs)
        response_json

    @classmethod
    def rest_api_resolver_method(cls, api, **kwargs):
        return getattr(api, 'dispatch')


class SingleItemQueryResolver(QueryResolver):
    """Callable which acts as resolver for an 'single item' field' on the Query.

    For example, if we had a tastypie ProfileResource with underlying
    Django model 'Profile', an instance of this class provides
    functionality for the 'resolve_profile' resolver
    on the root Query. Note in this case, we are required to
    supply an 'id' argument in the kwargs passed to __call__.
    (This  to a GET request to the /profile/{id} detail endpoint
     in REST terms)
    """

    @classmethod
    def rest_api_resolver_method(cls, api, **kwargs):
        pass


def _selectable_fields_mutator(api):
    """Mutate resource so that only selected fields are serialized.

     This function dynamically binds a customised version of the
     standard DRF view get_serializer method to the input
     method. This customised version ensures we only iterate over
     and hence serialize the fields as dictated by the appropriate
     key in the 'selected_fields' dictionary.

     Whilst this approach of dynamically binding a custom method
     at run time may seem strange, it has been chosen for two
     primary reasons:

     1. It minimizes the amount of source code we need to touch
        in order to be able to use this library (e.g. if we had
        used mixins instead, clients would need to then add these
        mixins to the tastypie source code. If we'd subclassed the
        view to override get_serializer, it may cause later issues
        in client code (e.g. if there was any type checking))
     2. It makes few assumptions about client codes resource/
        field implementation (e.g. should work with custom
        field types/ custom views).
     """
    api = copy.deepcopy(api)
    api.get_serializer = _selectable_fields_get_serializer.__get__(api)
    return api


def _selectable_fields_get_serializer(api, *args, **kwargs):
    serializer = api.get_serializer(*args, **kwargs)
    selected_fields = api.request.environ.get('selected_fields', [])
    all_fields = copy.deepcopy(selected_fields.fields.items())
    for field_name, field in all_fields:
        # if field is related:
        #     pass
        if field_name not in selected_fields:
            serializer.fields.pop(field_name)
    return serializer
