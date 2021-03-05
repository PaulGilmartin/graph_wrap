from __future__ import unicode_literals

import copy
from functools import partial

from tastypie.exceptions import BadRequest

from graph_wrap.shared.query_resolver import QueryResolverBase


class QueryResolver(QueryResolverBase):

    def _get_response(self, request, **kwargs):
        resolver = self.rest_api_resolver_method(**kwargs)
        response = resolver(request)
        return response

    def _build_selected_fields_api(self):
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
         Explored alternatives were:
          * Dynamically create a subclass of our api which overrides
            the dehydrate method in the way we wish. This however has
            the immediate disadvantage that any type checking of the
            api in the client code would then fail.
         """
        self._api.full_dehydrate = _selectable_fields_full_dehydrate.__get__(
            self._api)
        return self._api


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

    def rest_api_resolver_method(self, **kwargs):
        selectable_fields_resource = self._build_selected_fields_api()
        return getattr(selectable_fields_resource, 'dispatch_list')


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

    def rest_api_resolver_method(self, **kwargs):
        selectable_fields_resource = self._build_selected_fields_api()
        return partial(
            getattr(selectable_fields_resource, 'dispatch_detail'),
            pk=kwargs['id'],
        )


def _selectable_fields_full_dehydrate(api, bundle, for_list=False):
    fields = {}
    selected_fields = bundle.request.environ.get('selected_fields', [])
    for field_name, field in api.fields.items():
        if field_name in selected_fields:
            if field.dehydrated_type == 'related':
                field.dehydrate = _selectable_fields_dehydrate.__get__(field)
            fields[field_name] = field
    api.fields = fields
    return api.__class__.full_dehydrate(api, bundle, for_list)


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

