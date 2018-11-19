# Copyright 2018 ML2Grow BVBA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pickle

import umongo
from umongo.exceptions import ValidationError
from umongo.data_objects import Reference
from marshmallow import fields as ma_fields


class ReferenceField(umongo.fields.ReferenceField):
    """
    umongo.fields.ReferenceField inherits the serialize/deserialize behaviour which creates bson.ObjectIDs

    In order to avoid this, we must override the _(de)serialize of the ReferenceField class.
    This involves some copy paste.
    """

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
        #collection = self.document_cls.collection
        #value = collection.key(value)
        # `value` is similar to data received from the database so we
        # can use `_deserialize_from_mongo` to finish the deserialization
        return self._deserialize_from_mongo(value)


class _MaBytesField(ma_fields.Field):
    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        return pickle.loads(value)

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        return pickle.dumps(value)


class BytesField(umongo.abstract.BaseField, _MaBytesField):
    pass


SUPPORTED_FIELD_TYPES = [
    umongo.fields.BooleanField,
    umongo.fields.DateTimeField,
    umongo.fields.ReferenceField,
    umongo.fields.StringField,
    umongo.fields.NumberField,
    umongo.fields.IntegerField,
    umongo.fields.UrlField,
    umongo.fields.EmailField,
    umongo.fields.EmbeddedField,
    umongo.fields.ListField,
    umongo.fields.DictField,
    umongo.fields.FormattedStringField,
    umongo.fields.FloatField,
    ReferenceField,
    BytesField
]