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

import copy
import itertools
from datetime import datetime

from google.cloud import datastore
from umongo.frameworks import tools


def cook_find_filter(doc_cls, filters):
    filters = tools.cook_find_filter(doc_cls, filters)
    key = filters.pop('_id', None)
    if key:
        filters['__key__'] = key
    return filters


def _apply_filter(query, *args, fresh=False):
    # pylint: disable=W0212
    if fresh:
        query = datastore.Query(
            client=query._client,
            kind=query._kind,
            project=query._project,
            namespace=query._namespace,
            ancestor=query._ancestor,
            filters=copy.deepcopy(query._filters),
            projection=query._projection,
            order=query._order,
            distinct_on=query._distinct_on
        )
    query.add_filter(*args)
    return query


class DataStoreClientWrapper:
    """ For compatibility with the collection property in umongo """
    def __init__(self, client):
        super().__init__()
        self.client = client

    def __getitem__(self, cname) -> 'CollectionAbstraction':
        return CollectionAbstraction(self.client, cname)


class CollectionAbstraction:
    """
    Represents a "collection", as a convention we interpret this as an Entity kind.

    Instances are returned by the collection property, has some methods to interact
    with datastore on this specific entity.
    """

    _filter_oper_lookup = {
        '$gt': lambda q, k, v: [_apply_filter(q, k, '>', v)],
        '$lt': lambda q, k, v: [_apply_filter(q, k, '<', v)],
        '$eq': lambda q, k, v: [_apply_filter(q, k, '=', v)],
        '$gte': lambda q, k, v: [_apply_filter(q, k, '>=', v)],
        '$lte': lambda q, k, v: [_apply_filter(q, k, '<=', v)],
        '$in': lambda q, k, v: [_apply_filter(q, k, '=', i, fresh=True) for i in v]
    }

    def __init__(self, client, cname):
        super(CollectionAbstraction, self).__init__()
        self.client = client
        self.cname = cname

    @staticmethod
    def _unpack(entity):
        if entity is None:
            return None

        payload = {
            '_id': entity.key.id_or_name,
        }

        for key, value in entity.items():
            if isinstance(value, datetime):
                value = value.replace(tzinfo=None)
            payload[key] = value

        return payload

    def _pack(self, payload):
        ref = payload.pop('_id', None)
        entity = datastore.Entity(key=self.key(ref))
        entity.update(payload)
        return entity

    def key(self, ref=None):
        if ref:
            return self.client.key(self.cname, ref)
        else:
            return self.client.key(self.cname)

    def get(self, key):
        return self.get_multi([key])[0]

    def get_multi(self, keys):
        keys_wrapped = list(map(self.key, keys))
        entities = self.client.get_multi(keys_wrapped)
        entity_map = {e.key.id_or_name: e for e in entities}
        return [self._unpack(entity_map.get(key, None)) for key in keys]

    def put(self, payload):
        keys = self.put_multi([payload])
        return keys[0]

    def put_multi(self, payloads):
        entities = list(map(self._pack, payloads))
        self.client.put_multi(entities)
        return list(map(lambda k: k.key.id_or_name, entities))

    def delete(self, key):
        self.client.delete(self.key(key))

    def query(self, filters, limit=None, order=()):
        queries = [self.client.query(kind=self.cname, order=order)]
        for attr, domain in filters.items():
            if isinstance(domain, dict):
                for oper, operand in domain.items():
                    query_groups = [self._filter_oper_lookup[oper](query, attr, operand) for query in queries]
                    queries = itertools.chain(*query_groups)
            else:
                for query in queries:
                    query.add_filter(attr, '=', domain)

        for query in queries:
            for ret in query.fetch(limit=limit):
                yield self._unpack(ret)
