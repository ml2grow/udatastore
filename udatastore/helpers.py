from google.cloud import datastore
from umongo.frameworks import tools
import copy
import itertools
from datetime import datetime


def cook_find_filter(doc_cls, filter):
    filter = tools.cook_find_filter(doc_cls, filter)
    pk = filter.pop('_id', None)
    if pk:
        filter['__key__'] = pk
    return filter


def _apply_filter(q, *args, fresh=False):
    if fresh:
        q = datastore.Query(
            client=q._client,
            kind=q._kind,
            project=q._project,
            namespace=q._namespace,
            ancestor=q._ancestor,
            filters=copy.deepcopy(q._filters),
            projection=q._projection,
            order=q._order,
            distinct_on=q._distinct_on
        )
    q.add_filter(*args)
    return q


class DataStoreClientWrapper(object):
    """ For compatibility with the collection property in umongo """
    def __init__(self, client):
        self.client = client

    def __getitem__(self, cname):
        return CollectionAbstraction(self.client, cname)


class CollectionAbstraction(object):
    """
    Represents a "collection", as a convention we interpret this as an Entity kind.

    Instances are returned by the collection property, has some methods to interact with datastore on this specific entity.
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

        for k, v in entity.items():
            if isinstance(v, datetime):
                v = v.replace(tzinfo=None)
            payload[k] = v

        return payload

    def _pack(self, payload):
        pk = payload.pop('_id', None)
        entity = datastore.Entity(key=self.key(pk))
        entity.update(payload)
        return entity

    def key(self, pk=None):
        if pk:
            return self.client.key(self.cname, pk)
        else:
            return self.client.key(self.cname)

    def get(self, pk):
        return self.get_multi([pk])[0]

    def get_multi(self, pks):
        keys = list(map(self.key, pks))
        entities = self.client.get_multi(keys)
        entity_map = {e.key.id_or_name: e for e in entities}
        return [self._unpack(entity_map.get(k, None)) for k in pks]

    def put(self, payload):
        keys = self.put_multi([payload])
        return keys[0]

    def put_multi(self, payloads):
        entities = list(map(self._pack, payloads))
        self.client.put_multi(entities)
        return list(map(lambda k: k.key.id_or_name, entities))

    def delete(self, pk):
        self.client.delete(self.key(pk))

    def query(self, filters, *args, **kwargs):
        qs = [self.client.query(kind=self.cname)]
        for k, v in filters.items():
            if isinstance(v, dict):
                for o1, o2 in v.items():
                    qs = itertools.chain(*[self._filter_oper_lookup[o1](q, k, o2) for q in qs])
            else:
                for q in qs:
                    q.add_filter(k, '=', v)

        for q in qs:
            for ret in q.fetch(*args, **kwargs):
                yield self._unpack(ret)