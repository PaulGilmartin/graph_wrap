from __future__ import unicode_literals


import json
from decimal import Decimal

import graphene
import six
from graphene import ObjectType
from graphene.types.generic import GenericScalar
from rest_framework import serializers

from graph_wrap.django_rest_framework.field_resolvers import JSONResolver


class ApiTransformer(object):
    def __init__(self, api):
        self._api = api
        self._root_serializer = api.get_serializer()
        # This will exist as a type referenced on the root Query
        self._root_graphene_type_name = u'{}_type'.format(self._api.basename)
        self._all_serializers = []

    def transform(self):
        graphene_type_data = []
        self._collect_nested_serializers(self._root_serializer)
        root_serializer, *nested_serializers = self._all_serializers
        root_transformed = SerializerTransformer(
            root_serializer,
            self._root_graphene_type_name,
            root_query_type=True,
        ).transform()
        graphene_type_data.append(root_transformed)
        for nested in nested_serializers:
            nested_transformed = SerializerTransformer(nested).transform()
            graphene_type_data.append(nested_transformed)
        return graphene_type_data

    def _collect_nested_serializers(self, serializer):
        for _field_name, field in serializer.fields.items():
            if hasattr(field, 'fields'):
                nested_serializer = field
                self._collect_nested_serializers(
                    nested_serializer)
        self._all_serializers.insert(0, serializer)


class SerializerTransformer(object):
    def __init__(
            self,
            serializer,
            graphene_type_name='',
            root_query_type=False,
    ):
        self._serializer = serializer
        self._model_name = self._serializer.Meta.model.__name__.lower()
        # If not graphene_type_name not passed in explicitly, we assume
        # the serializer comes from the 'NestedSerializer' DRF class
        # (which is built dynamically from a nested related model field).
        # Will this always be the case? What if we have a nested custom
        # serializer which doesn't come from the root query? How
        # would we name that?
        self._graphene_type_name = graphene_type_name or (
            'from_{}_model_type'.format(self._model_name))
        self._root_query_type = root_query_type
        self._graphene_object_type_class_attrs = dict()

    def transform(self):
        for field in self._serializer.fields.values():
            self._add_field_data(field)
        graphene_type = type(
            str(self._graphene_type_name),
            (ObjectType,),
            self._graphene_object_type_class_attrs,
        )

        return {
            'graphene_object_type': graphene_type,
            'root_query_type': self._root_query_type,
        }

    def _add_field_data(self, field):
        field_transformer = FieldTransformer.get_transformer(field)
        graphene_field, resolver_method = list(
            field_transformer.transform().items())[0]
        resolver_method_name = 'resolve_{}'.format(field.field_name)
        self._graphene_object_type_class_attrs[resolver_method_name] = (
            resolver_method)


class FieldTransformer(object):
    _graphene_type = None

    def __init__(self, field):
        self._field = field

    @classmethod
    def get_transformer(cls, field):
        serializer_field_to_transformer = {
            'CharField': StringValuedFieldTransformer,
            'IntegerField': IntegerValuedFieldTransformer,
            'HyperlinkedRelatedField': RelatedValuedFieldTransformer, # shouldn't need this if we have full depth?
            'NestedSerializer': RelatedValuedFieldTransformer,
        }
        try:
            transformer_class = serializer_field_to_transformer[
                field.__class__.__name__]
        except KeyError:

            raise KeyError('Field type not recognized')
        return transformer_class(field)

    def transform(self):
        return {
            'graphene_field': self._graphene_field(),
            'graphene_field_resolver_method': (
                self._graphene_field_resolver_method()),
        }

    def _graphene_field(self):
        pass

    def _graphene_field_resolver_method(self):
        return JSONResolver(self._graphene_field_name())

    def _graphene_field_name(self):
        return self._field.field_name

    def _graphene_field_required(self):
        return not self._field.allow_null


class ScalarValuedFieldTransformer(FieldTransformer):
    """Functionality for transforming a 'scalar' valued tastypie field.

    Base transformer for converting any tastypie field which is not a
    subclass of RelatedField.
    """

    def _graphene_field(self):
        return self._graphene_type(
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
        )


class RelatedValuedFieldTransformer(FieldTransformer):
    """Functionality for transforming a 'related' field."""
    def __init__(self, field):
        super(RelatedValuedFieldTransformer, self).__init__(field)
        self._field_class = field.__class__
        self._is_to_many = False  # how to determine?

    def _graphene_field(self):
        wrapper = graphene.List if self._is_to_many else graphene.Field
        return wrapper(
            self._graphene_type,
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
        )

    @property
    def _graphene_type(self):
        from .schema_factory import SchemaFactory
        # Needs to be lazy since at this point the related
        # type may not yet have been created
        # This isn't thread safe. We can probably pass through
        # the SchemaFactory instance to this point
        # and have api_class_to_schema as a instance attr.
        return lambda: SchemaFactory.api_class_to_schema[
            (self._field.field_name, self._field.parent)]


class StringValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.String


class IntegerValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.Int


class FloatValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.Float


class BooleanValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.Boolean


class DateValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.String


class DatetimeValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.String


class TimeValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = graphene.String


class UnicodeCompatibleDecimal(Decimal):
    """
    The `Decimal` scalar type represents a python Decimal.
    """

    @staticmethod
    def serialize(dec):
        if isinstance(dec, six.string_types):
            dec = graphene.Decimal(dec)
        assert isinstance(
            dec, graphene.Decimal), 'Received not compatible Decimal "{}"'.format(
            repr(dec)
        )
        return str(dec)


class DecimalValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = UnicodeCompatibleDecimal


class Dict(graphene.Scalar):
    """Custom scalar to transform 'dict' type tastypie fields."""
    @staticmethod
    def serialize(dt):
        if isinstance(dt, six.string_types):
            return json.loads(dt)
        return dt


class DictValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = Dict


class ListValuedFieldTransformer(FieldTransformer):
    _graphene_type = GenericScalar

    def _graphene_field(self):
        return graphene.List(
            self._graphene_type,
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
        )


class ToOneRelatedValuedFieldTransformer(RelatedValuedFieldTransformer):
    pass


class ToManyRelatedValuedFieldTransformer(RelatedValuedFieldTransformer):
    _tastypie_field_is_m2m = True
