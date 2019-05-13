# Copyright 2019 ML2Grow NV
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
from umongo.data_objects import Reference, Dict
from marshmallow import fields as ma_fields
from marshmallow import missing


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
        # `value` is similar to data received from the database so we
        # can use `_deserialize_from_mongo` to finish the deserialization
        return self._deserialize_from_mongo(value)


class _MaBytesField(ma_fields.Field):
    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        return pickle.dumps(value)

    def _deserialize(self, value, attr, data):
        if isinstance(value, bytes):
            return pickle.loads(value)
        return value


class BytesField(umongo.abstract.BaseField, _MaBytesField):
    def __init__(self, *args, encoding='ASCII', **kwargs):
        super(BytesField, self).__init__(*args, **kwargs)
        self._encoding = encoding

    def _serialize_to_mongo(self, obj):
        if obj is None:
            return missing
        return pickle.dumps(obj)

    def _deserialize_from_mongo(self, value):
        if value is None:
            return None
        return pickle.loads(value, encoding=self._encoding)


class DictField(umongo.fields.DictField):
    def _deserialize(self, value, attr, data):
        value = super()._deserialize(value, attr, data)
        if isinstance(value, dict):
            altered_val = {self._reverse_replace_dot(k): v for k, v in value.items()}
            return Dict(altered_val)
        else:
            return Dict(value)

    def _serialize_to_mongo(self, obj):
        if not obj:
            return missing
        if isinstance(obj, dict):
            altered_obj = {self._replace_dot(k): v for k, v in obj.items()}
            return dict(altered_obj)

        return dict(obj)

    @staticmethod
    def _replace_dot(obj):
        if isinstance(obj, str):
            return obj.replace(".", "[dot]")
        else:
            return obj

    @staticmethod
    def _reverse_replace_dot(obj):
        if isinstance(obj, str):
            return obj.replace("[dot]", ".")
        else:
            return obj

    def _deserialize_from_mongo(self, value):
        if value:
            val_dict = Dict(value)
            altered_val = {self._reverse_replace_dot(k): v for k, v in val_dict.items()}
            return altered_val
        else:
            return Dict()



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
    DictField,
    umongo.fields.FormattedStringField,
    umongo.fields.FloatField,
    ReferenceField,
    BytesField
]
