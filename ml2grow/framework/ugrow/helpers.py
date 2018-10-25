from google.cloud import datastore
from umongo.frameworks import tools


def cook_find_filter(doc_cls, filter):
    filter = tools.cook_find_filter(doc_cls, filter)
    pk = filter.pop('_id', None)
    if pk:
        filter['__key__'] = doc_cls.collection.key(pk)
    return filter


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
    def __init__(self, client, cname):
        super(CollectionAbstraction, self).__init__()
        self.client = client
        self.cname = cname

    @staticmethod
    def _unpack(entity):
        return {
            '_id': entity.key.id_or_name,
            **entity
        }

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
        entity = self.client.get(self.key(pk))
        return self._unpack(entity)

    def put(self, payload):
        entity = self._pack(payload)
        self.client.put(entity)
        return entity.key.id_or_name

    def delete(self, pk):
        self.client.delete(self.key(pk))

    def query(self, filters, *args, **kwargs):
        q = self.client.query(kind=self.cname)
        for k, v in filters.items():
            q.add_filter(k, '=', v)

        for ret in q.fetch(*args, **kwargs):
            yield self._unpack(ret)