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
