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

        Raises :class:`umongo.exceptions.NotCreatedError` if the document
        doesn't exist in database.
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

        :param io_validate_all:
        :param conditions: only perform commit if matching record in db
            satisfies condition(s) (e.g. version number).
            Raises :class:`umongo.exceptions.UpdateError` if the
            conditions are not satisfied.
         :return: A :class:`pymongo.results.UpdateResult` or
            :class:`pymongo.results.InsertOneResult` depending of the operation.
       """
        try:
            was_created = self.is_created
            if self.is_modified():
                self.required_validate()
                self.io_validate(validate_all=io_validate_all)
                payload = self._data.to_mongo(update=False)
                key = self.collection.put(payload)

            if not was_created:
                self._data.set_by_mongo_name('_id', key)

        except Exception as exc:
            # Need to dig into error message to find faulting index
            raise ValidationError(str(exc))
        self.is_created = True
        self._data.clear_modified()
        return None

    def delete(self):
        """
        Remove the document from database.

        :param conditions: Only perform delete if matching record in db
            satisfies condition(s) (e.g. version number).
            Raises :class:`umongo.exceptions.DeleteError` if the
            conditions are not satisfied.
        Raises :class:`umongo.exceptions.NotCreatedError` if the document
        is not created (i.e. ``doc.is_created`` is False)
        Raises :class:`umongo.exceptions.DeleteError` if the document
        doesn't exist in database.

        :return: A :class:`pymongo.results.DeleteResult`
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

        :param validate_all: If False only run the io_validators of the
            fields that have been modified.
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
        # In txmongo, `spec` is for filtering and `filter` is for sorting
        spec = cook_find_filter(cls, spec)

        for ret in cls.collection.query(spec, *args, **kwargs):
            yield cls.build_from_mongo(ret, use_cls=True)

    @classmethod
    def count(cls, spec=None, **kwargs):
        """
        Get the number of documents in this collection.
        """
        # In txmongo, `spec` is for filtering and `filter` is for sorting
        spec = cook_find_filter(cls, spec)
        return len(list(cls.find(spec)))

    @classmethod
    def ensure_indexes(cls):
        """
        Check&create if needed the Document's indexes in database
        """
        return
        yield

    @classmethod
    def get(cls, pk):
        return cls.collection.get(pk)
