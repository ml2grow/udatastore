import umongo
from umongo.exceptions import ValidationError
from umongo.data_objects import Reference


class ReferenceField(umongo.fields.ReferenceField):
    """
    The default referencefield inherits the serialize/deserialize behavour from marshmallow_bonus which creates
    bson.ObjectIDs

    In order to avoid this, we must override the _(de)serialize of the referencefield class.
    This involves some copy paste. The DataStoreBuilder then overrides all ReferenceFields with this version.
    """
    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        return value.id_or_name

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        elif isinstance(value, Reference):
            if value.document_cls != self.document_cls:
                raise ValidationError("`{document}` reference expected.".format(document=self.document_cls.__name__))
            if not isinstance(value, self.reference_cls):
                value = self.reference_cls(value.document_cls, value.pk)
            return value
        elif isinstance(value, self.document_cls):
            if not value.is_created:
                raise ValidationError("Cannot reference a document that has not been created yet.")
            value = value.pk
        elif isinstance(value, self._document_implementation_cls):
            raise ValidationError("`{document}` reference expected.".format(document=self.document_cls.__name__))
        collection = self.document_cls.collection
        value = collection.key(value)
        # `value` is similar to data received from the database so we
        # can use `_deserialize_from_mongo` to finish the deserialization
        return self._deserialize_from_mongo(value)
