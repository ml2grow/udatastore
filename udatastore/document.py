from .helpers import cook_find_filter

from umongo.document import DocumentImplementation
from umongo.exceptions import NotCreatedError, ValidationError, DeleteError
from umongo.frameworks.pymongo import _io_validate_data_proxy


class DataStoreDocument(DocumentImplementation):

    """ The actual framework implementation class. """

    __slots__ = ()

    opts = DocumentImplementation.opts

    def reload(self):
        """
        Retrieve and replace document's data by the ones in database.
        """
        if not self.is_created:
            raise NotCreatedError("Document doesn't exists in database")
        ret = self.get(self.pk)
        if ret is None:
            raise NotCreatedError("Document doesn't exists in database")
        self._data = self.DataProxy()
        self._data.from_mongo(ret)

    def commit(self, io_validate_all=False):
        """
        Commit the document in database.
        If the document doesn't already exist it will be inserted, otherwise
        it will be updated.
       """
        return self.commit_multi([self], io_validate_all=io_validate_all)

    @classmethod
    def commit_multi(cls, docs, io_validate_all=False):
        payloads = []
        try:
            for doc in docs:
                if doc.is_modified():
                    doc.required_validate()
                    doc.io_validate(validate_all=io_validate_all)
                    payloads.append(doc._data.to_mongo(update=False))

            keys = cls.collection.put_multi(payloads)

            for key, doc in zip(keys, docs):
                if not doc.is_created:
                    doc._data.set_by_mongo_name('_id', key)

        except Exception as exc:
            # Need to dig into error message to find faulting index
            raise ValidationError(str(exc))

        for doc in docs:
            doc.is_created = True
            doc._data.clear_modified()
        return None

    def delete(self):
        """
        Remove the document from database.
        """
        if not self.is_created:
            raise NotCreatedError("Document doesn't exists in database")
        try:
            self.collection.delete(self.pk)
            self.is_created = False
        except Exception as e:
            raise DeleteError(str(e))

    def io_validate(self, validate_all=False):
        """
        Run the io_validators of the document's fields.
        """
        if validate_all:
            return _io_validate_data_proxy(self.schema, self._data)
        else:
            return _io_validate_data_proxy(
                self.schema, self._data, partial=self._data.get_modified_fields())

    @classmethod
    def find_one(cls, spec=None, *args, **kwargs):
        """
        Find a single document in database.
        """
        return next(cls.find(spec, limit=1, *args, **kwargs))

    @classmethod
    def find(cls, spec=None, *args, **kwargs):
        """
        Find a list document in database.

        Returns a cursor that provide Documents.
        """
        spec = cook_find_filter(cls, spec)

        for ret in cls.collection.query(spec, *args, **kwargs):
            yield cls.build_from_mongo(ret, use_cls=True)

    @classmethod
    def count(cls, spec=None, **kwargs):
        """
        Get the number of documents in this collection.
        """
        spec = cook_find_filter(cls, spec)
        return len(list(cls.find(spec)))

    @classmethod
    def ensure_indexes(cls):
        """
        No index support for datastore
        """
        return
        yield

    @classmethod
    def get(cls, pk):
        return cls.get_multi([pk])[0]

    @classmethod
    def get_multi(cls, pks):
        returned = cls.collection.get_multi(pks)
        return list(map(lambda r: cls.build_from_mongo(r, use_cls=True), returned))
