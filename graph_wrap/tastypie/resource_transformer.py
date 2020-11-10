from __future__ import unicode_literals

import json
from abc import abstractmethod
from decimal import Decimal as _Decimal

import six
from graphene import (
    String,
    Int,
    Float,
    Boolean,
    Decimal,
    List,
    Field,
    Scalar,
    ObjectType,
)
from graphene.types.generic import GenericScalar

from .field_resolvers import JSONResolver


def transform_resource(tastypie_resource):
    """Transform a tastypie resource into a graphene ObjectType."""
    class_attrs = dict()
    graphene_type_name = tastypie_resource._meta.resource_name + '_type'
    for field_name, field in tastypie_resource.fields.items():
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


def field_transformer(tastypie_field):
    """Instantiate the appropriate FieldTransformer class.

    This acts as a factory-type function, which, given
    a tastypie field as input, instantiates the appropriate
    concrete FieldTransformer class for that field.
    """
    try:
        transformer_class = FieldTransformerMeta.registry[
            (tastypie_field.dehydrated_type, tastypie_field.is_m2m)]
    except KeyError:
        raise KeyError('Dehydrated type not recognized')
    return transformer_class(tastypie_field)


class FieldTransformerMeta(type):
    """Metaclass for FieldTransformers.

    Provides functionality to track the names of all
    concrete subclasses of FieldTransformer. This data
    can then be used in the factory function 'field_transformer'
    when choosing the appropriate transformer class. This
    avoids having to hard code (and hence continually update)
    the list of concrete subclasses in the field_transformer
    function.
    """
    registry = dict()

    def __new__(mcs, name, bases, attrs):
        """Automatically adds each FieldTransformer class into a registry.

        Upon class definition/compilation of a FieldTransformer subclass,
        transform_cls, the registry dictionary is populated with a key:value
        pair of the form transform_cls.identifier(): transform_cls.
        """
        converter_class = super(FieldTransformerMeta, mcs).__new__(
            mcs, name, bases, attrs)
        identifier = converter_class.identifier()
        if identifier:
            mcs.registry[identifier] = converter_class
        return converter_class


class FieldTransformer(six.with_metaclass(FieldTransformerMeta, object)):
    """Functionality for transforming tastypie ApiField to a graphene field."""

    _tastypie_field_dehydrated_type = None
    _tastypie_field_is_m2m = False
    _graphene_type = None

    def __init__(self, tastypie_field):
        self._tastypie_field = tastypie_field

    @classmethod
    def identifier(cls):
        if cls._tastypie_field_dehydrated_type:
            return (
                cls._tastypie_field_dehydrated_type,
                cls._tastypie_field_is_m2m,
            )

    @abstractmethod
    def graphene_field(self):
        pass

    def graphene_field_resolver_method(self):
        return JSONResolver(self._graphene_field_name())

    def _graphene_field_name(self):
        return self._tastypie_field.instance_name

    def _graphene_field_required(self):
        return not self._tastypie_field.null


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
        wrapper = List if self._tastypie_field_is_m2m else Field
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
        return lambda: SchemaFactory.resource_class_to_schema[
            self._resource_class]


class StringValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = String
    _tastypie_field_dehydrated_type = 'string'


class IntegerValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = Int
    _tastypie_field_dehydrated_type = 'integer'


class FloatValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = Float
    _tastypie_field_dehydrated_type = 'float'


class BooleanValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = Boolean
    _tastypie_field_dehydrated_type = 'boolean'


class DateValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = String
    _tastypie_field_dehydrated_type = 'date'


class DatetimeValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = String
    _tastypie_field_dehydrated_type = 'datetime'


class TimeValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = String
    _tastypie_field_dehydrated_type = 'time'


class UnicodeCompatibleDecimal(Decimal):
    """
    The `Decimal` scalar type represents a python Decimal.
    """

    @staticmethod
    def serialize(dec):
        if isinstance(dec, six.string_types):
            dec = _Decimal(dec)
        assert isinstance(
            dec, _Decimal), 'Received not compatible Decimal "{}"'.format(
            repr(dec)
        )
        return str(dec)


class DecimalValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = UnicodeCompatibleDecimal
    _tastypie_field_dehydrated_type = 'decimal'


class Dict(Scalar):
    """Custom scalar to transform 'dict' type tastypie fields."""
    @staticmethod
    def serialize(dt):
        if isinstance(dt, six.string_types):
            return json.loads(dt)
        return dt


class DictValuedFieldTransformer(ScalarValuedFieldTransformer):
    _graphene_type = Dict
    _tastypie_field_dehydrated_type = 'dict'


class ListValuedFieldTransformer(FieldTransformer):
    _graphene_type = GenericScalar
    _tastypie_field_dehydrated_type = 'list'

    def graphene_field(self):
        return List(
            self._graphene_type,
            name=self._graphene_field_name(),
            required=self._graphene_field_required(),
        )


class ToOneRelatedValuedFieldTransformer(RelatedValuedFieldTransformer):
    pass


class ToManyRelatedValuedFieldTransformer(RelatedValuedFieldTransformer):
    _tastypie_field_is_m2m = True