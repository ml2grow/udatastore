from udatastore.helpers import CollectionAbstraction, DataStoreClientWrapper
import pytest
from google.cloud import datastore


def test_client_wrapper(client):
    w = DataStoreClientWrapper(client)
    col = w['User']
    assert isinstance(col, CollectionAbstraction)
    assert col.cname == 'User'
    assert col.client == client


@pytest.fixture
def collection(client):
    yield CollectionAbstraction(client, 'User')


@pytest.fixture
def data(collection):
    collection.put({'identifier': 5, 'property': 2.0, 'category': 'A'})
    collection.put({'identifier': 6, 'property': 0.0, 'category': 'B'})
    collection.put({'identifier': 7, 'property': 2.8, 'category': 'B'})
    collection.put({'identifier': 8, 'property': 5.3, 'category': 'C'})
    collection.put({'identifier': 9, 'property': 4.22, 'category': 'A'})
    collection.put({'identifier': 10, 'property': 0.0, 'category': 'A'})
    collection.put({'identifier': 11, 'property': 0.0, 'category': 'A'})


def test_create_key(collection):
    key = collection.key(5)
    assert isinstance(key, datastore.Key)
    assert key.kind == 'User'
    assert key.id_or_name == 5


def test_get_put_no_key(collection):
    assert collection.get(5) is None
    pk = collection.put({'a': 5, 'property': 2.0})
    retrieved = collection.get(pk.id)
    retrieved == {'a': 5, 'property': 2.0, '_id': pk}


def test_get_put_key(collection):
    assert collection.get(5) is None
    collection.put({'a': 5, 'property': 2.0, '_id': 5})
    retrieved = collection.get(5)
    retrieved == {'a': 5, 'property': 2.0, '_id': 5}


def test_put_delete_get(collection):
    assert collection.get(5) is None
    pk = collection.put({'a': 5, 'property': 2.0})
    collection.delete(pk)
    assert collection.get(5) is None


@pytest.mark.usefixtures("data")
def test_query(collection):
    retrieved = list(collection.query({}))
    assert len(retrieved) == 7
    assert all(set(o.keys()) == set(['identifier', 'property', 'category', '_id']) for o in retrieved)


@pytest.mark.parametrize("filter,expected", [
    ({'category': 'A'}, 4),
    ({'category': {'$eq': 'A'}}, 4),
    ({'category': {'$in': ['B', 'C']}}, 3),
    ({'identifier': {'$lt': 8}}, 3),
    ({'identifier': {'$lte': 8}}, 4),
    ({'property': {'$gt': 4.22}}, 1),
    ({'property': {'$gte': 4.22}}, 2),
    ({'category': 'A', 'property': {'$gte': 2.0}}, 2),
])
@pytest.mark.usefixtures("data")
def test_query(collection, filter, expected):
    retrieved = list(collection.query(filter))
    assert len(retrieved) == expected


def test_put_multi(collection):
    data = [{'a': 5, 'property': 2.0}, {'a': 6, 'property': 3.0}]
    pks = collection.put_multi(data)
    assert len(list(collection.query({}))) == 2
    retrieved = collection.get_multi([k.id for k in pks] + [99])
    assert len(retrieved) == 3
    assert retrieved[-1] is None
    for d, k, r in zip(data, pks, retrieved):
        d['_id'] = k
        assert d == r
