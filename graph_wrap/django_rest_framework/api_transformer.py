import json
from abc import abstractmethod
from decimal import Decimal

import graphene
import six
from graphene import ObjectType
from graphene.types.generic import GenericScalar
from rest_framework import serializers

from graph_wrap.django_rest_framework.field_resolvers import JSONResolver


def transform_api(api):
    class_attrs = dict()
    graphene_type_name = api.basename + '_type'  # Does basename limit the view type?
    serializer = api.get_serializer()
    for field_name, field in serializer.fields.items():# .fields limits to views or viewsets?
        transformer = field_transformer(field)
        class_attrs[field_name] = transformer.graphene_field()
        resolver_method_name = 'resolve_{}'.format(field_name)
        class_attrs[resolver_method_name] = (
            transformer.graphene_field_resolver_method())
    graphene_type = type(
        str(graphene_type_name),
        (ObjectType,),
        class_attrs,
    )
    return graphene_type


def field_transformer(field):
    """Instantiate the appropriate FieldTransformer class.

    This acts as a factory-type function, which, given
    a tastypie field as input, instantiates the appropriate
    concrete FieldTransformer class for that field.
    """
    serializer_field_to_transformer = {
        serializers.CharField: StringValuedFieldTransformer}
    try:
        transformer_class = serializer_field_to_transformer[
            field.__class__]
    except KeyError:
        raise KeyError('Field type not recognized')
    return transformer_class(field)

#
# class FieldTransformerMeta(type):
#     registry = dict()
#
#     def __new__(mcs, name, bases, attrs):
#         """Automatically adds each FieldTransformer class into a registry.
#
#         Upon class definition/compilation of a FieldTransformer subclass,
#         transform_cls, the registry dictionary is populated with a key:value
#         pair of the form transform_cls.identifier(): transform_cls.
#         """
#         converter_class = super(FieldTransformerMeta, mcs).__new__(
#             mcs, name, bases, attrs)
#         identifier = converter_class.identifier()
#         if identifier:
#             mcs.registry[identifier] = converter_class
#         return converter_class


class FieldTransformer(object):
    _graphene_type = None

    def __init__(self, field):
        self._field = field

    @abstractmethod
    def graphene_field(self):
        pass

    def graphene_field_resolver_method(self):
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

    def graphene_field(self):
        return self._graphene_type(
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
        )


class RelatedValuedFieldTransformer(FieldTransformer):
    """Functionality for transforming a 'related' valued tastypie field."""
    _tastypie_field_dehydrated_type = 'related'

    def __init__(self, tastypie_field):
        super(RelatedValuedFieldTransformer, self).__init__(tastypie_field)
        self._resource_class = tastypie_field.to_class

    def graphene_field(self):
        wrapper = graphene.List if self._tastypie_field_is_m2m else graphene.Field
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
        return lambda: SchemaFactory.api_class_to_schema[
            self._resource_class]


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

    def graphene_field(self):
        return graphene.List(
            self._graphene_type,
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
        )


class ToOneRelatedValuedFieldTransformer(RelatedValuedFieldTransformer):
    pass


class ToManyRelatedValuedFieldTransformer(RelatedValuedFieldTransformer):
    _tastypie_field_is_m2m = True