from umongo.data_proxy import BaseDataProxy, BaseNonStrictDataProxy
from google.cloud import datastore


class KeyTranslatingBaseDataProxy(BaseDataProxy):
    """
    Handles converting fields stored as datastore.Key (because attribute='_id' was set) back to their value
    Only for retrieving data, wrapping the keys here is difficult (the other key attributes are unknown in
    the DataProxy)
    """
    # pylint: disable=W0201
    def dump(self):
        data_old = self._data
        self._data = {}
        for key, value in data_old.items():
            if isinstance(value, datastore.Key):
                value = value.id_or_name
            self._data[key] = value
        result = super().dump()
        self._data = data_old
        return result

    def get(self, name, to_raise=KeyError):
        value = super().get(name, to_raise)
        if isinstance(value, datastore.Key):
            value = value.id_or_name
        return value


class KeyTranslatingBaseNonStrictDataProxy(BaseNonStrictDataProxy):
    # pylint: disable=W0201
    def dump(self):
        data_old = self._data
        self._data = {}
        for key, value in data_old.items():
            if isinstance(value, datastore.Key):
                value = value.id_or_name
            self._data[key] = value
        result = super().dump()
        self._data = data_old
        return result

    def get(self, name, to_raise=KeyError):
        value = super().get(name, to_raise)
        if isinstance(value, datastore.Key):
            value = value.id_or_name
        return value


def data_proxy_factory(basename, schema, strict=True):
    cls_name = "%sDataProxy" % basename

    nmspc = {
        '__slots__': (),
        'schema': schema,
        '_fields': schema.fields,
        '_fields_from_mongo_key': {v.attribute or k: v for k, v in schema.fields.items()}
    }

    data_proxy_cls = type(
        cls_name,
        (KeyTranslatingBaseDataProxy if strict else KeyTranslatingBaseNonStrictDataProxy, ),
        nmspc
    )
    return data_proxy_cls
