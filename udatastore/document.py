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

from umongo.document import DocumentImplementation
from umongo.exceptions import NotCreatedError, ValidationError, DeleteError
from umongo.frameworks.pymongo import _io_validate_data_proxy

from .helpers import cook_find_filter


class DataStoreDocument(DocumentImplementation):

    """ The actual framework implementation class. """

    __slots__ = ()

    opts = DocumentImplementation.opts

    @staticmethod
    def excluded_properties():
        return ()

    def reload(self):
        """
        Retrieve and replace document's data by the ones in database.
        """
        if not self.is_created:
            raise NotCreatedError("Document doesn't exists in database")
        ret = self.get(self.pk.id_or_name)
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
        # pylint: disable=W0212
        payloads = []
        try:
            for doc in docs:
                if doc.is_modified():
                    doc.required_validate()
                    doc.io_validate(validate_all=io_validate_all)
                    payloads.append(doc._data.to_mongo(update=False))

            keys = cls.collection.put_multi(  # pylint: disable=E1101
                payloads,
                exclude_from_indexes=cls.excluded_properties()
            )

            for key, doc in zip(keys, docs):
                if not doc.is_created:
                    doc._data.set_by_mongo_name('_id', key)

        except Exception as exc:
            # Need to dig into error message to find faulting index
            raise ValidationError(str(exc))

        for doc in docs:
            doc.is_created = True
            doc._data.clear_modified()

    def delete(self):
        """
        Remove the document from database.
        """
        if not self.is_created:
            raise NotCreatedError("Document doesn't exists in database")
        try:
            self.collection.delete(self.pk)  # pylint: disable=E1101
            self.is_created = False
        except Exception as exc:
            raise DeleteError(str(exc))

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
    def find_one(cls, filters=None, order=()):
        """
        Find a single document in database.
        """
        try:
            doc = next(cls.find(filters, limit=1, order=order))
        except StopIteration:
            doc = None
        return doc

    @classmethod
    def find(cls, filters=None, order=(), limit=None):
        """
        Find a list document in database.

        Returns a cursor that provide Documents.
        """
        filters = cook_find_filter(cls, filters or {})

        for ret in cls.collection.query(filters, order=order, limit=limit):  # pylint: disable=E1101
            yield cls.build_from_mongo(ret, use_cls=True)

    @classmethod
    def count(cls, filters=None):
        """
        Get the number of documents in this collection.
        """
        filters = cook_find_filter(cls, filters or {})
        return len(list(cls.find(filters)))

    @classmethod
    def ensure_indexes(cls):
        """
        No index support for datastore
        """
        return
        yield  # pylint: disable=W0101

    @classmethod
    def get(cls, key):
        return cls.get_multi([key])[0]

    @classmethod
    def get_multi(cls, pks):
        returned = cls.collection.get_multi(pks)  # pylint: disable=E1101
        return list(map(lambda r: cls.build_from_mongo(r, use_cls=True), returned))
