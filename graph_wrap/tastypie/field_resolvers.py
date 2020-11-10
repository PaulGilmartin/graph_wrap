from __future__ import unicode_literals

import copy
from abc import abstractmethod
from functools import partial

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
    def __init__(self, field_name, resource):
        super(QueryResolver, self).__init__(field_name)
        self._resource = resource

    @classmethod
    def rest_resource_resolver_method(cls, resource_adapter, **kwargs):
        pass

    def __call__(self, root, info, **kwargs):
        get_request = transform_graphql_resolve_info(
            self._field_name, info, **kwargs)
        selectable_fields_resource = _selectable_fields_mutator(
            self._resource)
        rest_resolver_method = self.rest_resource_resolver_method(
            selectable_fields_resource,
            **kwargs
        )
        resource_response = rest_resolver_method(get_request)
        if resource_response.status_code in (
                300, 307, 400, 401, 403, 404, 405, 500):
            raise BadRequest(resource_response.content)
        response_json = json.loads(
            resource_response.content or '{}')
        return response_json


class AllItemsQueryResolver(QueryResolver):
    """Callable which acts as resolver for an 'all_items' field' on the Query.

    For example, if we had a tastypie ProfileResource with underlying
    Django model 'Profile', an instance of this class provides
    functionality for the 'resolve_all_profiles' resolver
    on the root Query (analogous to a GET request to the /profile
    list endpoint in REST terms).
    """
    def __call__(self, root, info, **kwargs):
        response_json = super(AllItemsQueryResolver, self).__call__(
            root, info, **kwargs)
        try:
            return response_json['objects']
        except KeyError:
            try:
                raise BadRequest(response_json['error'])
            except KeyError:
                return response_json

    @classmethod
    def rest_resource_resolver_method(cls, resource_adapter, **kwargs):
        return getattr(resource_adapter, 'dispatch_list')


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
    def rest_resource_resolver_method(cls, resource_adapter, **kwargs):
        return partial(
            getattr(resource_adapter, 'dispatch_detail'),
            pk=kwargs['id'],
        )


def _selectable_fields_mutator(resource):
    """Mutate resource so that only selected fields are dehydrated.

     This function dynamically binds a customised version of the
     standard tastypie full_dehydrate resource method to the input
     method. This customised version ensures we only iterate over
     and hence dehydrate the fields as dictated by the appropriate
     key in the 'selected_fields' dictionary.

     Whilst this approach of dynamically binding a custom method
     at run time may seem strange, it has been chosen for two
     primary reasons:

     1. It minimizes the amount of source code we need to touch
        in order to be able to use this library (e.g. if we had
        used mixins instead, clients would need to then add these
        mixins to the tastypie source code.)
     2. It makes few assumptions about client codes resource/
        field implementation (e.g. will work with custom
        field types/ custom resources).
     """
    resource = copy.deepcopy(resource)
    resource.full_dehydrate = _selectable_fields_full_dehydrate.__get__(
        resource)
    return resource


def _selectable_fields_full_dehydrate(resource, bundle, for_list=False):
    fields = {}
    selected_fields = bundle.request.environ.get('selected_fields', [])
    for field_name, field in resource.fields.items():
        if field_name in selected_fields:
            if field.dehydrated_type == 'related':
                field.dehydrate = _selectable_fields_dehydrate.__get__(field)
            fields[field_name] = field
    resource.fields = fields
    return resource.__class__.full_dehydrate(resource, bundle, for_list)


def _selectable_fields_dehydrate(field, bundle, for_list=True):
    field.full = True
    field.full_list = lambda x: True
    field.full_detail = lambda x: True
    field.get_related_resource = _selectable_fields_get_related.__get__(field)
    selection = bundle.request.environ['selected_fields']
    bundle.request.environ['selected_fields'] = selection[field.instance_name]
    result = field.__class__.dehydrate(field, bundle, for_list)
    bundle.request.environ['selected_fields'] = selection
    return result


def _selectable_fields_get_related(field, related_instance):
    related_resource = copy.deepcopy(field.__class__.get_related_resource(
        field, related_instance))
    related_resource.full_dehydrate = _selectable_fields_full_dehydrate.__get__(
        related_resource)
    return related_resource


