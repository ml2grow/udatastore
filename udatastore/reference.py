from umongo.data_objects import Reference
from umongo.exceptions import ValidationError


class DataStoreReference(Reference):
    """ Reference representation """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._document = None

    def fetch(self, no_data=False, force_reload=False):
        if not self._document or force_reload:
            if self.pk is None:
                raise ReferenceError('Cannot retrieve a None Reference')
            self._document = self.document_cls.find_one({'_id': self.pk})
            if not self._document:
                raise ValidationError(self.error_messages['not_found'].format(document=self.document_cls.__name__))
        return self._document
